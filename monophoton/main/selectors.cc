#include "selectors.h"

#include "TFile.h"
#include "TTree.h"
#include "TSystem.h"

#include <cstring>

//--------------------------------------------------------------------
// EventSelectorBase
//--------------------------------------------------------------------

std::mutex EventSelectorBase::mutex;

EventSelectorBase::~EventSelectorBase()
{
  if (ownOperators_) {
    for (auto* op : operators_)
      delete op;
  }
}

void
EventSelectorBase::addOperator(Operator* _op, unsigned _idx/* = -1*/)
{
  if (!dynamic_cast<MonophotonOperator*>(_op) && !dynamic_cast<BaseOperator*>(_op))
    throw std::runtime_error(TString::Format("Cannot add operator %s to EventSelector", _op->name()).Data());

  if (_idx >= operators_.size())
    operators_.push_back(_op);
  else
    operators_.insert(operators_.begin() + _idx, _op);
}

Operator*
EventSelectorBase::findOperator(char const* _name) const
{
  for (auto* op : operators_) {
    if (std::strcmp(op->name(), _name) == 0)
      return op;
  }

  return 0;
}

unsigned
EventSelectorBase::index(char const* _name) const
{
  unsigned idx(0);
  for (; idx != operators_.size(); ++idx) {
    if (std::strcmp(operators_[idx]->name(), _name) == 0)
      break;
  }

  return idx;
}

void
EventSelectorBase::removeOperator(char const* _name)
{
  for (auto itr(operators_.begin()); itr != operators_.end(); ++itr) {
    if (std::strcmp((*itr)->name(), _name) == 0) {
      operators_.erase(itr);
      break;
    }
  }
}

void
EventSelectorBase::initialize(char const* _outputPath, panda::EventMonophoton& _inEvent, panda::utils::BranchList& _blist, bool _isMC)
{
  if (printLevel_ > 0)
    *stream_ << "Initializing " << className() << "::" << name() << std::endl;

  auto* outputFile(new TFile(_outputPath, "recreate"));

  skimOut_ = new TTree("events", "Events");
  cutsOut_ = new TTree("cutflow", "cutflow");

  skimOut_->Branch("weight_Input", &inWeight_, "weight_Input/D");

  cutsOut_->Branch("runNumber", &_inEvent.runNumber, "runNumber/i");
  cutsOut_->Branch("lumiNumber", &_inEvent.lumiNumber, "lumiNumber/i");
  cutsOut_->Branch("eventNumber", &_inEvent.eventNumber, "eventNumber/i");

  setupSkim_(_inEvent, _isMC);

  if (printLevel_ > 0 && printLevel_ <= INFO) {
    *stream_ << "Operators for selector " << name() << std::endl;
    for (auto* op : operators_) {
      *stream_ << " " << op->expr() << std::endl;
      op->setPrintLevel(printLevel_);
      op->setOutputStream(*stream_);
    }
    *stream_ << std::endl;
  }

  for (auto* op : operators_) {
    op->addInputBranch(_blist);
    op->addBranches(*skimOut_);
    op->initialize(_inEvent);
    if (dynamic_cast<Cut*>(op))
      static_cast<Cut*>(op)->registerCut(*cutsOut_);
  }

  if (printLevel_ > 0)
    *stream_ << std::endl;

  if (useTimers_)
    timers_.resize(operators_.size());
}

void
EventSelectorBase::finalize()
{
  if (!skimOut_)
    return;

  auto* outputFile(skimOut_->GetCurrentFile());
  outputFile->cd();
  skimOut_->Write();
  cutsOut_->Write();

  // save additional output if there are any
  addOutput_(outputFile);

  delete outputFile;
  skimOut_ = 0;
  cutsOut_ = 0;

  if (useTimers_) {
    *stream_ << "Operator runtimes for " << name() << " (CPU seconds):" << std::endl;
    for (unsigned iO(0); iO != operators_.size(); ++iO) {
      stream_->flags(std::ios_base::fixed);
      stream_->width(5);
      *stream_ << " " << (std::chrono::duration_cast<std::chrono::nanoseconds>(timers_[iO]).count() * 1.e-9) << " " << operators_[iO]->name() << std::endl;
    }
  }
}

//--------------------------------------------------------------------
// EventSelector
//--------------------------------------------------------------------

void
EventSelector::setupSkim_(panda::EventMonophoton& _inEvent, bool _isMC)
{
  // Branches to be directly copied from the input tree
  // Add a prepareFill line below any time a collection branch is added
  panda::utils::BranchList blist{{"runNumber", "lumiNumber", "eventNumber", "npv", "rho", "vertices"}};
  if (_isMC)
    blist += {"npvTrue", "partons", "genParticles", "genVertex"}; // , "genMet"};
  else
    blist += {"metFilters"};

  _inEvent.book(*skimOut_, blist);

  blist = {"weight", "jets", "photons", "electrons", "muons", "taus", "superClusters", "t1Met"};
  if (_isMC)
    blist += {"genJets"}; // filled only if AddGenJets operator is run

  outEvent_.book(*skimOut_, blist);
}

void
EventSelector::prepareFill_(panda::EventMonophoton& _inEvent)
{
  _inEvent.vertices.prepareFill(*skimOut_);
  // _inEvent.pfCandidates.prepareFill(*skimOut_);
  _inEvent.partons.prepareFill(*skimOut_);
  _inEvent.genParticles.prepareFill(*skimOut_);
}

void
EventSelector::selectEvent(panda::EventMonophoton& _event)
{
  if (blindPrescale_ > 1 && _event.runNumber >= blindMinRun_ && _event.eventNumber % blindPrescale_ != 0)
    return;

  outEvent_.init();
  inWeight_ = _event.weight;
  outEvent_.weight = _event.weight;

  Clock::time_point start;

  bool pass(true);
  for (unsigned iO(0); iO != operators_.size(); ++iO) {
    auto& op(*operators_[iO]);
    
    if (useTimers_)
      start = Clock::now();

    if (!op.exec(_event, outEvent_))
      pass = false;

    if (useTimers_)
      timers_[iO] += Clock::now() - start;
  }

  cutsOut_->Fill();

  if (pass) {
    // IMPORTATNT
    // We link these skimOut branches to the input event. Need to refresh the addresses in case
    // collections are resized.

    // It would be clearer / more elegant to factor this operation out to a serial part, have
    // selectEvent take an EventMonophoton const& as an argument, and return pass, but cases
    // like ZeeEventSelector doesn't allow an easy factorization.

    std::lock_guard<std::mutex> lock(EventSelectorBase::mutex);

    prepareFill_(_event);

    outEvent_.fill(*skimOut_);
  }
}

//--------------------------------------------------------------------
// ZeeEventSelector
//--------------------------------------------------------------------

void
ZeeEventSelector::setupSkim_(panda::EventMonophoton& _inEvent, bool _isMC)
{
  EventSelector::setupSkim_(_inEvent, _isMC);

  for (leptonSelection_ = operators_.begin(); leptonSelection_ != operators_.end(); ++leptonSelection_) {
    if (dynamic_cast<LeptonSelection*>(*leptonSelection_))
      break;
  }
}

void
ZeeEventSelector::selectEvent(panda::EventMonophoton& _event)
{
  outEvent_.init();
  inWeight_ = _event.weight;
  outEvent_.weight = _event.weight;

  Clock::time_point start;

  bool passUpToLS(true);
  unsigned iO(0);
  for (auto itr(operators_.begin()); itr != leptonSelection_; ++itr) {
    auto& op(**itr);
    
    if (useTimers_)
      start = Clock::now();

    if (!op.exec(_event, outEvent_))
      passUpToLS = false;

    if (useTimers_)
      timers_[iO] += Clock::now() - start;

    ++iO;
  }

  if (passUpToLS && outEvent_.photons.size() > 1) {
    // Assumption: Photon selector is run
    panda::XPhotonCollection photonsTmp(outEvent_.photons);

    for (auto& photon : photonsTmp) {
      outEvent_.electrons.clear();
      outEvent_.photons.clear();
      outEvent_.photons.push_back(photon);

      bool pass(true);

      unsigned iOPair(iO);
      for (auto itr(leptonSelection_); itr != operators_.end(); ++itr) {
        auto& op(**itr);

        if (useTimers_)
          start = Clock::now();

        if (!op.exec(_event, outEvent_))
          pass = false;

        if (useTimers_)
          timers_[iOPair] += Clock::now() - start;

        ++iOPair;
      }

      cutsOut_->Fill();

      if (pass) {
        std::lock_guard<std::mutex> lock(EventSelectorBase::mutex);

        prepareFill_(_event);
          
        outEvent_.fill(*skimOut_);
      }
    }
  }
  else {
    // just run the remaining operators

    bool pass(passUpToLS);

    for (auto itr(leptonSelection_); itr != operators_.end(); ++itr) {
      auto& op(**itr);

      if (useTimers_)
        start = Clock::now();

      if (!op.exec(_event, outEvent_))
        pass = false;

      if (useTimers_)
        timers_[iO] += Clock::now() - start;

      ++iO;
    }

    cutsOut_->Fill();

    if (pass) {
      std::lock_guard<std::mutex> lock(EventSelectorBase::mutex);

      prepareFill_(_event);
          
      outEvent_.fill(*skimOut_);
    }
  }
}

//--------------------------------------------------------------------
// PartonSelector
//--------------------------------------------------------------------

PartonSelector::PartonSelector(char const* _name) :
  EventSelector(_name),
  flavor_(new PartonFlavor())
{
  operators_.push_back(flavor_);
}

PartonSelector::~PartonSelector()
{
  if (!ownOperators_) {
    // we need to take care of the first operator which we created
    delete flavor_;
    operators_.erase(operators_.begin());
  }
}

void
PartonSelector::selectEvent(panda::EventMonophoton& _event)
{
  if (!flavor_->exec(_event, outEvent_))
    return;

  EventSelector::selectEvent(_event);
}

//--------------------------------------------------------------------
// NormalizingSelector
//--------------------------------------------------------------------

void
NormalizingSelector::addOutput_(TFile*& _outputFile)
{
  auto* hSumW(new TH1D("sumW", "", 1, 0., 1.));
  skimOut_->Draw("0.5>>sumW", "weight * (" + normCut_ + ")", "goff");
  double sumW(hSumW->GetBinContent(1));
  delete hSumW;

  TString outName(_outputFile->GetName());
  TString tmpName(outName);
  tmpName.ReplaceAll(".root", "_normalizing.root");

  auto* trueOutput(TFile::Open(tmpName, "recreate"));
  auto* trueSkim(skimOut_->CloneTree(0));
  double weight(0.);
  trueSkim->SetBranchAddress("weight", &weight);

  printf("check time. \n norm_ = %.2f \n sumW  = %.2f \n", norm_, sumW);

  long iEntry(0);
  while (skimOut_->GetEntry(iEntry++)) {
    weight = norm_ / sumW * outEvent_.weight;
    trueSkim->Fill();
  }

  trueOutput->cd();
  trueSkim->Write();
  auto* trueCuts(cutsOut_->CloneTree(-1, "fast"));
  trueCuts->Write();

  delete trueOutput;

  delete _outputFile;
  // set the pointer to NULL so that finalize() does not delete it again
  _outputFile = 0;

  gSystem->Rename(tmpName, outName);
}

//--------------------------------------------------------------------
// SmearingSelector
//--------------------------------------------------------------------

void
SmearingSelector::selectEvent(panda::EventMonophoton& _event)
{
  if (!func_)
    return;

  // smearing the MET only - total pT will be inconsistent
  double originalMet(_event.t1Met.pt);

  _event.weight /= nSamples_;

  for (unsigned iS(0); iS != nSamples_; ++iS) {
    _event.t1Met.pt = originalMet + func_->GetRandom();
  
    EventSelector::selectEvent(_event);
  }
}

//--------------------------------------------------------------------
// TagAndProbeSelector
//--------------------------------------------------------------------

#include "PandaTree/Objects/interface/EventTPEG.h"
#include "PandaTree/Objects/interface/EventTPEEG.h"
#include "PandaTree/Objects/interface/EventTPMG.h"
#include "PandaTree/Objects/interface/EventTPMMG.h"
#include "PandaTree/Objects/interface/EventTP2E.h"
#include "PandaTree/Objects/interface/EventTP2M.h"

void
TagAndProbeSelector::addOperator(Operator* _op, unsigned _idx/* = -1*/)
{
  if (!dynamic_cast<TPOperator*>(_op) && !dynamic_cast<BaseOperator*>(_op))
    throw std::runtime_error(TString::Format("Cannot add operator %s to TagAndProbeSelector", _op->name()).Data());

  if (_idx >= operators_.size())
    operators_.push_back(_op);
  else
    operators_.insert(operators_.begin() + _idx, _op);
}

void
TagAndProbeSelector::setupSkim_(panda::EventMonophoton& _inEvent, bool _isMC)
{
  switch (outType_) {
  case kTPEG:
    outEvent_ = new panda::EventTPEG;
    break;
  case kTPEEG:
    outEvent_ = new panda::EventTPEEG;
    break;
  case kTPMG:
    outEvent_ = new panda::EventTPMG;
    break;
  case kTPMMG:
    outEvent_ = new panda::EventTPMMG;
    break;
  case kTP2E:
    outEvent_ = new panda::EventTP2E;
    break;
  case kTP2M:
    outEvent_ = new panda::EventTP2M;
    break;
  default:
    throw std::runtime_error("Out event type not set");
  }

  // Branches to be directly copied from the input tree
  // Add a prepareFill function when a collection branch is added
  panda::utils::BranchList blist{{"runNumber", "lumiNumber", "eventNumber", "isData", "npv", "rho", "t1Met"}};
  if (_isMC)
    blist += {"npvTrue"};

  _inEvent.book(*skimOut_, blist);

  // looseTags will be added by the TPMuonPhoton operator
  blist = {"weight", "sample", "tp", "tags", "probes", "jets"};
  if (outType_ == kTPEEG || outType_ == kTPMMG)
    blist += {"looseTags"};

  outEvent_->book(*skimOut_, blist);
}

void
TagAndProbeSelector::selectEvent(panda::EventMonophoton& _event)
{
  outEvent_->init();

  // copy EventBase members
  static_cast<panda::EventBase&>(*outEvent_) = _event;

  outEvent_->npv = _event.npv;
  outEvent_->npvTrue = _event.npvTrue;
  outEvent_->rho = _event.rho;
  outEvent_->t1Met = _event.t1Met;

  inWeight_ = _event.weight;

  outEvent_->sample = sampleId_;

  Clock::time_point start;

  bool pass(true);
  for (unsigned iO(0); iO != operators_.size(); ++iO) {
    auto& op(*operators_[iO]);

    if (useTimers_)
      start = Clock::now();

    if (!op.exec(_event, *outEvent_))
      pass = false;

    if (useTimers_)
      timers_[iO] += Clock::now() - start;
  }

  cutsOut_->Fill();

  if (pass) {
    std::lock_guard<std::mutex> lock(EventSelectorBase::mutex);
    outEvent_->fill(*skimOut_);
  }
}
