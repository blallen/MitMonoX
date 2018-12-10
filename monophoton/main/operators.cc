#include "operators.h"

#include "PandaTree/Objects/interface/EventTPEG.h"
#include "PandaTree/Objects/interface/EventTPEEG.h"
#include "PandaTree/Objects/interface/EventTPMG.h"
#include "PandaTree/Objects/interface/EventTPMMG.h"
#include "PandaTree/Objects/interface/EventTP2E.h"
#include "PandaTree/Objects/interface/EventTP2M.h"

#include "TH1.h"
#include "TF1.h"
#include "TGraph.h"

#include <iostream>
#include <functional>
#include <fstream>

#include "fastjet/internal/base.hh"
#include "fastjet/PseudoJet.hh"
#include "fastjet/ClusterSequence.hh"
#include "fastjet/Selector.hh"
#include "fastjet/GhostedAreaSpec.hh"

//--------------------------------------------------------------------
// Base
//--------------------------------------------------------------------

TString
CutMixin::cutExpr(TString const& name) const
{
  if (ignoreDecision_)
    return TString::Format("(%s)", name.Data());
  else
    return TString::Format("[%s]", name.Data());
}

bool
MonophotonCut::monophexec(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  result_ = pass(_event, _outEvent);
  return ignoreDecision_ || result_;
}

bool
MonophotonModifier::monophexec(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  apply(_event, _outEvent);
  return true;
}

panda::ParticleCollection*
TPOperator::getLooseTags(panda::EventTP& _outEvent) const
{
  switch (eventType_) {
  case kTPEEG:
    return &static_cast<panda::EventTPEEG&>(_outEvent).looseTags;
  case kTPMMG:
    return &static_cast<panda::EventTPMMG&>(_outEvent).looseTags;
  default:
    throw std::runtime_error("Incompatible event type in getLooseTag");
  }
}

panda::ParticleCollection*
TPOperator::getTags(panda::EventTP& _outEvent) const
{
  switch (eventType_) {
  case kTPEEG:
  case kTPEG:
    return &static_cast<panda::EventTPEG&>(_outEvent).tags;
  case kTPMMG:
  case kTPMG:
    return &static_cast<panda::EventTPMG&>(_outEvent).tags;
  case kTP2E:
    return &static_cast<panda::EventTP2E&>(_outEvent).tags;
  case kTP2M:
    return &static_cast<panda::EventTP2M&>(_outEvent).tags;
  default:
    throw std::runtime_error("Incompatible event type in getTag");
  }
}

panda::ParticleCollection*
TPOperator::getProbes(panda::EventTP& _outEvent) const
{
  switch (eventType_) {
  case kTPEEG:
  case kTPEG:
    return &static_cast<panda::EventTPEG&>(_outEvent).probes;
  case kTPMMG:
  case kTPMG:
    return &static_cast<panda::EventTPMG&>(_outEvent).probes;
  case kTP2E:
    return &static_cast<panda::EventTP2E&>(_outEvent).probes;
  case kTP2M:
    return &static_cast<panda::EventTP2M&>(_outEvent).probes;
  default:
    throw std::runtime_error("Incompatible event type in getProbe");
  }
}

bool
TPCut::tpexec(panda::EventMonophoton const& _event, panda::EventTP& _outEvent)
{
  result_ = pass(_event, _outEvent);
  return ignoreDecision_ || result_;
}

bool
TPModifier::tpexec(panda::EventMonophoton const& _event, panda::EventTP& _outEvent)
{
  apply(_event, _outEvent);
  return true;
}

//--------------------------------------------------------------------
// HLTFilter
//--------------------------------------------------------------------


HLTFilter::HLTFilter(char const* name) :
  Cut(name)
{
  pathNames_ = name;
}

HLTFilter::~HLTFilter()
{
  tokens_.clear();
}

void
HLTFilter::initialize(panda::EventMonophoton& _event)
{
  Ssiz_t pos(0);
  TString path;
  UInt_t token(0);

  if (printLevel_ > 0)
    *stream_ << "Triggers to add: " << pathNames_ << std::endl;

  while (pathNames_.Tokenize(path, pos, "_OR_")) {
    token = _event.registerTrigger(path.Data());
    tokens_.push_back(token);
    if (printLevel_ > 0)
      *stream_ << "Added trigger path " << path << " with token " << token << " to tokens vector." << std::endl;
  }
}

void
HLTFilter::addBranches(TTree& _skimTree)
{
  _skimTree.Branch(pathNames_, &pass_, pathNames_ + "/O");
}

bool
HLTFilter::pass(panda::EventMonophoton const& _event, panda::EventBase&)
{
  // make sure a trigger menu exists; will return a human readable error if not
  _event.run.triggerMenu();

  pass_ = false;

  for (unsigned iT(0); iT != tokens_.size(); ++iT) {
    auto& token(tokens_[iT]);

    if (_event.triggerFired(token))
      pass_ = true;
  }
  
  return pass_;
}

//--------------------------------------------------------------------
// EventVeto
//--------------------------------------------------------------------

void
EventVeto::addSource(char const* _path)
{
  std::ifstream input(_path);
  std::string line;

  while (true) {
    std::getline(input, line);
    if (!input.good())
      break;

    unsigned run(std::atoi(line.substr(0, line.find(":")).c_str()));
    unsigned lumi(std::atoi(line.substr(line.find(":") + 1, line.rfind(":")).c_str()));
    unsigned event(std::atoi(line.substr(line.rfind(":") + 1).c_str()));

    list_[run][lumi].insert(event);
  }
}

void
EventVeto::addEvent(unsigned run, unsigned lumi, unsigned event)
{
  list_[run][lumi].insert(event);
}

bool
EventVeto::pass(panda::EventMonophoton const& _event, panda::EventBase&)
{
  auto rItr(list_.find(_event.runNumber));
  if (rItr == list_.end())
    return true;

  auto lItr(rItr->second.find(_event.lumiNumber));
  if (lItr == rItr->second.end())
    return true;

  auto eItr(lItr->second.find(_event.eventNumber));
  return eItr == lItr->second.end();
}

//--------------------------------------------------------------------
// MetFilters
//--------------------------------------------------------------------

bool
MetFilters::pass(panda::EventMonophoton const& _event, panda::EventBase&)
{
  if (!_event.metFilters.hbhe && !_event.metFilters.hbheIso && !_event.metFilters.ecalDeadCell && !_event.metFilters.goodVertices && !_event.metFilters.badsc && !_event.metFilters.badMuons && !_event.metFilters.duplicateMuons && !_event.metFilters.badPFMuons && !_event.metFilters.badChargedHadrons) {
    if (halo_) 
      return true;
    else {
      if (!_event.metFilters.globalHalo16)
	return true;
      else
	return false;
    }
  }
  else 
    return false;
}

//--------------------------------------------------------------------
// GenPhotonVeto
//--------------------------------------------------------------------

bool
GenPhotonVeto::pass(panda::EventMonophoton const& _event, panda::EventBase&)
{
  for (unsigned iG(0); iG != _event.genParticles.size(); ++iG) {
    auto& part(_event.genParticles[iG]);

    if (!part.finalState)
      continue;

    if (part.pdgid != 22)
      continue;

    if (part.pt() < minPt_)
      continue;

    unsigned iP(0);
    for (; iP != _event.partons.size(); ++iP) {
      auto& parton(_event.partons[iP]);
      if (parton.dR2(part) < minPartonDR2_)
        break;
    }
    if (iP != _event.partons.size())
      continue;

    return false;
  }

  return true;
}


//--------------------------------------------------------------------
// TriggerMatch
//--------------------------------------------------------------------

void
TriggerMatch::initialize(panda::EventMonophoton& _event)
{
  _event.run.setLoadTrigger(true);
  for (auto& name : filterNames_)
    _event.registerTriggerObjects(name);
}

void
TriggerMatch::addInputBranch(panda::utils::BranchList& _blist)
{
  _blist += {"triggerObjects"};
}

void
TriggerMatch::addBranches(TTree& _skimTree)
{
  switch (collection_) {
  case cPhotons:
    _skimTree.Branch("photons.hltmatch" + name_, matchResults_, "hltmatch" + name_ + "[photons.size]/O");
    break;
  case cElectrons:
    _skimTree.Branch("electrons.hltmatch" + name_, matchResults_, "hltmatch" + name_ + "[electrons.size]/O");
    break;
  case cMuons:
    _skimTree.Branch("muons.hltmatch" + name_, matchResults_, "hltmatch" + name_ + "[muons.size]/O");
    break;
  default:
    return;
  }
}

void
TriggerMatch::apply(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  typedef std::vector<panda::HLTObject const*> HLTObjectVector;

  std::fill_n(matchResults_, NMAX_PARTICLES, false);

  bool any(false);
  std::vector<std::pair<HLTObjectVector const*, double>> filterObjects;
  for (auto& name : filterNames_) {
    double dR(name.Index("hltL1s") == 0 ? 0.3 : 0.15);
    auto& objects(_event.triggerObjects.filterObjects(name));
    filterObjects.emplace_back(&objects, dR);
    if (filterObjects.back().first->size() != 0)
      any = true;
  }

  std::cout << "but we don't care" << std::endl;

  if (!any)
    return;

  panda::ParticleCollection* collection(0);

  switch (collection_) {
  case cPhotons:
    collection = &_outEvent.photons;
    break;
  case cElectrons:
    collection = &_outEvent.electrons;
    break;
  case cMuons:
    collection = &_outEvent.muons;
    break;
  default:
    return;
  }

  for (unsigned iP(0); iP != collection->size(); ++iP) {
    auto& cand(collection->at(iP));
    for (auto& pair : filterObjects) {
      auto* objects(pair.first);
      double dR(pair.second);

      unsigned iO(0);
      for (; iO != objects->size(); ++iO) {
        if (cand.dR(*(*objects)[iO]) < dR) {
          matchResults_[iP] = true;
          break;
        }
      }
      if (iO != objects->size())
        break;
    }
  }
}

//--------------------------------------------------------------------
// PartonKinematics
//--------------------------------------------------------------------

void
PartonKinematics::addBranches(TTree& _skimTree)
{
  _skimTree.Branch("genPhoton.pt", &phoPt_, "genPhoton.pt/F");
  _skimTree.Branch("genPhoton.eta", &phoEta_, "genPhoton.eta/F");
  _skimTree.Branch("genPhoton.phi", &phoPhi_, "genPhoton.phi/F");

  _skimTree.Branch("genMet.pt", &metPt_, "genMet.pt/F");
  _skimTree.Branch("genMet.phi", &metPhi_, "genMet.phi/F");
}

void
PartonKinematics::apply(panda::EventMonophoton const& _event, panda::EventBase&)
{
  phoPt_ = -1;
  phoEta_ = -1;
  phoPhi_ = -1;

  metPt_ = -1;
  metPhi_ = -1;

  long absid(0.);
  double mpx(0.);
  double mpy(0.);

  for (auto& parton : _event.partons) {
    absid = std::abs(parton.pdgid);
    if (absid == 22 && parton.pt() > phoPt_) {
      phoPt_ = parton.pt();
      phoEta_ = parton.eta();
      phoPhi_ = parton.phi();
    }
    
    else if (absid == 12 || absid == 14 || absid == 16 || absid == 51 || absid == 52 || absid == 53 || absid == 1000012 || absid == 2000012 || absid == 3000012) {
      mpx += parton.pt() * std::cos(parton.phi());
      mpy += parton.pt() * std::sin(parton.phi());
    }
  }

  metPt_ = std::sqrt(mpx * mpx + mpy * mpy);
  metPhi_ = std::atan2(mpy, mpx);
}


//--------------------------------------------------------------------
// PartonFlavor
//--------------------------------------------------------------------

bool
PartonFlavor::pass(panda::EventMonophoton const& _event, panda::EventBase&)
{
  if (_event.partons.size() == 0)
    return false;

  for (auto& parton : _event.partons) {
    unsigned absId(std::abs(parton.pdgid));
    if (absId == rejectedId_)
      return false;
    if (absId == requiredId_)
      return true;
  }

  // if requiredId is set, reaching here means the event does not have the target parton -> false
  // if requiredId is not set, we return true.
  return requiredId_ == 0;
}

//--------------------------------------------------------------------
// PhotonSelection
//--------------------------------------------------------------------

TString const
PhotonSelection::selectionName[PhotonSelection::nSelections] = {
  "Pt",
  "IsBarrel",
  "HOverE",
  "Sieie",
  "NHIso",
  "PhIso",
  "CHIso",
  "CHIsoMax",
  "EVeto",
  "CSafeVeto",
  "ChargedPFVeto",
  "MIP49",
  "Time",
  "SieieNonzero",
  "SipipNonzero",
  "NoisyRegion",
  "E2E995",
  "Sieie08",
  "Sieie12",
  "Sieie15",
  "Sieie20",
  "Sipip08",
  "CHIso11",
  "CHIsoMax11",
  "NHIsoLoose",
  "PhIsoLoose",
  "NHIsoTight",
  "PhIsoTight",
  "Sieie05",
  "Sipip05"
};

TString
PhotonSelection::selToString(PhotonSelection::SelectionMask _mask)
{
  TString invert;
  if (!_mask.first)
    invert = "!";

  TString value;
  for (unsigned iS(0); iS != nSelections; ++iS) {
    if (_mask.second[iS]) {
      if (value.Length() == 0)
        value = invert + selectionName[iS];
      else
        value += " OR " + invert + selectionName[iS];
    }
  }

  return value;
}

void
PhotonSelection::initialize(panda::EventMonophoton&)
{
  if (printLevel_ > 0 && printLevel_ <= INFO) {
    if (selections_.size() != 0) {
      *stream_ << "Photon selections for " << name_ << std::endl;
      for (unsigned iT(0); iT != selections_.size(); ++iT) {
        *stream_ << "[" << selToString(selections_[iT]) << "]";
        if (iT != selections_.size() - 1)
          *stream_ << " AND ";
      }
      *stream_ << std::endl;
    }
    if (vetoes_.size() != 0) {
      *stream_ << "Extra photon veto for " << name_ << std::endl;
      for (unsigned iT(0); iT != vetoes_.size(); ++iT) {
        *stream_ << "[" << selToString(vetoes_[iT]) << "]";
        if (iT != vetoes_.size() - 1)
          *stream_ << " AND ";
      }
      *stream_ << std::endl;
    }
  }
}

void
PhotonSelection::registerCut(TTree& cutsTree)
{
  cutsTree.Branch(name_, &nominalResult_, name_ + "/O");
  auto sname(name_ + "_size");
  cutsTree.Branch(sname, &size_, sname + "/i");

  for (unsigned iS(0); iS != nSelections; ++iS) {
    auto bname(name_ + "_" + selectionName[iS]);
    cutsTree.Branch(bname, cutRes_[iS], bname + "[" + sname + "]/O");
  }
}

void
PhotonSelection::addBranches(TTree& _skimTree)
{
  // add pt variation branches for simple selections.
  // vetoes are used for control regions, which would not require pt variation systematics studies.
  if (vetoes_.size() == 0) {
    _skimTree.Branch("photons.ptVarUp", ptVarUp_, "ptVarUp[photons.size]/F");
    _skimTree.Branch("photons.ptVarDown", ptVarDown_, "ptVarDown[photons.size]/F");
  }
  _skimTree.Branch("photons.chargedPFVeto", chargedPFVeto_, "chargedPFVeto[photons.size]/O");
}

void
PhotonSelection::addInputBranch(panda::utils::BranchList& _blist)
{
  bool hasPF(false);
  for (auto& sel : selections_) {
    if (sel.second[ChargedPFVeto]) {
      hasPF = true;
    }
  }
  for (auto& sel : vetoes_) {
    if (sel.second[ChargedPFVeto]) {
      hasPF = true;
      break;
    }
  }

  if (hasPF)
    _blist += {"pfCandidates"};
}

void
PhotonSelection::addSelection(bool _pass, unsigned _s1, unsigned _s2/* = nSelections*/, unsigned _s3/* = nSelections*/)
{
  BitMask sel;
  sel.set(_s1);
  if (_s2 != nSelections)
    sel.set(_s2);
  if (_s3 != nSelections)
    sel.set(_s3);

  selections_.emplace_back(_pass, sel);
}

void
PhotonSelection::removeSelection(unsigned _s1, unsigned _s2/* = nSelections*/, unsigned _s3/* = nSelections*/)
{
  BitMask sel;
  sel.set(_s1);
  if (_s2 != nSelections)
    sel.set(_s2);
  if (_s3 != nSelections)
    sel.set(_s3);

  for (auto&& itr(selections_.begin()); itr != selections_.end(); ++itr) {
    if (itr->second == sel) {
      selections_.erase(itr);
      *stream_ << "Removed photon selection " << selToString(*itr) << std::endl;
    }
  }
}

void
PhotonSelection::addVeto(bool _pass, unsigned _s1, unsigned _s2/* = nSelections*/, unsigned _s3/* = nSelections*/)
{
  BitMask sel;
  sel.set(_s1);
  if (_s2 != nSelections)
    sel.set(_s2);
  if (_s3 != nSelections)
    sel.set(_s3);

  vetoes_.emplace_back(_pass, sel);
}

void
PhotonSelection::removeVeto(unsigned _s1, unsigned _s2/* = nSelections*/, unsigned _s3/* = nSelections*/)
{
  BitMask sel;
  sel.set(_s1);
  if (_s2 != nSelections)
    sel.set(_s2);
  if (_s3 != nSelections)
    sel.set(_s3);

  for (auto&& itr(vetoes_.begin()); itr != vetoes_.end(); ++itr) {
    if (itr->second == sel) {
      vetoes_.erase(itr);
      *stream_ << "Removed photon selection " << selToString(*itr) << std::endl;
    }
  }
}

double
PhotonSelection::ptVariation(panda::XPhoton const& _photon, double _shift)
{
  double scRawPt(_photon.scRawPt);
  /*
  if (useOriginalPt_) {
    double deltaPt = ((_photon.originalPt - _photon.pt()) / _photon.pt());

    if (TMath::Abs(deltaPt) < 0.2) 
      scRawPt = 0.0; // don't keep events that weren't affected by the gain switch issue
    else {
      scRawPt *= _photon.originalPt / _photon.pt();
    }
  }
  */

  return scRawPt * (1. + 0.015 * _shift);
}

bool
PhotonSelection::pass(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  for (unsigned iC(0); iC != nSelections; ++iC)
    std::fill_n(cutRes_[iC], NMAX_PARTICLES, false);

  chargedCands_.clear();

  for (auto& cand : _event.pfCandidates) {
    if (cand.q() != 0)
      chargedCands_.push_back(&cand);
  }

  size_ = 0;

  bool vetoed(false);

  for (unsigned iP(0); iP != _event.photons.size(); ++iP) {
    auto& photon(_event.photons[iP]);

    if (!photon.isEB)
      continue;

    bool passPt(false);
    if (vetoes_.size() == 0) {
      // veto is not set -> this is a simple photon selection. Pass if upward variation is above the threshold.
      passPt = (ptVariation(photon, 1.) > minPt_);
    }
    else {
      passPt = (ptVariation(photon, 0.) > minPt_);
    }

    // We continue in both cases below because photons are not necessarily sorted by scRawPt

    if (!includeLowPt_ && !passPt)
      continue;

    if (size_ == 0 && !passPt) // leading photon has to pass the pt threshold
      continue;

    int selection(selectPhoton(photon, size_));

    ++size_;

    if (printLevel_ > 0 && printLevel_ <= DEBUG)
      *stream_ << "Photon " << iP << " returned selection " << selection << std::endl;

    if (vetoed)
      continue;

    if (selection < 0 && passPt) {
      _outEvent.photons.clear();
      vetoed = true;
    }
    else if (selection > 0) {
      // if includeLowPt = true, here we push back soft photons passing the ID
      if (vetoes_.size() == 0) {
        ptVarUp_[_outEvent.photons.size()] = ptVariation(photon, 1.);
        ptVarDown_[_outEvent.photons.size()] = ptVariation(photon, -1.);
      }
      chargedPFVeto_[_outEvent.photons.size()] = cutRes_[ChargedPFVeto][_outEvent.photons.size()];
      _outEvent.photons.push_back(photon);
      /*
      if (useOriginalPt_) {
        auto& outPhoton(_outEvent.photons.back());
        double scale(photon.originalPt / photon.pt());
        outPhoton.setPtEtaPhiM(photon.pt() * scale, photon.eta(), photon.phi(), 0.);
        outPhoton.scRawPt *= scale;
      }
      */
    }
  }

  unsigned nPassNominal(0);
  for (auto& ph : _outEvent.photons) {
    if (ph.scRawPt > minPt_)
      ++nPassNominal;
  }

  nominalResult_ = (nPassNominal >= nPhotons_);
  
  return _outEvent.photons.size() >= nPhotons_;
}

int
PhotonSelection::selectPhoton(panda::XPhoton const& _photon, unsigned _idx)
{
  BitMask cutres;
  // Ashim's retuned ID GJets_CWIso (https://indico.cern.ch/event/629088/contributions/2603837/attachments/1464422/2279061/80X_PhotonID_EfficiencyStudy_23-05-2017.pdf)
  cutres[Pt] = ptVariation(_photon, 0.) > minPt_;
  cutres[IsBarrel] = _photon.isEB;
  cutres[HOverE] = _photon.passHOverE(wp_, idTune_);
  cutres[Sieie] = _photon.passSieie(wp_, idTune_);
  cutres[CHIso] = _photon.passCHIso(wp_, idTune_);
  cutres[NHIso] = _photon.passNHIso(wp_, idTune_);
  cutres[PhIso] = _photon.passPhIso(wp_, idTune_);
  cutres[CHIsoMax] = _photon.passCHIsoMax(wp_, idTune_);
  cutres[EVeto] = _photon.pixelVeto;
  cutres[CSafeVeto] = _photon.csafeVeto;
  cutres[MIP49] = (_photon.mipEnergy < 4.9);
  cutres[Time] = (std::abs(_photon.time) < 3.);
  cutres[SieieNonzero] = (_photon.sieie > 0.001);
  cutres[SipipNonzero] = (_photon.sipip > 0.001);
  // If running over panda <= 011, need to compute eta ranges as floating point
  // Bound by   etamin      etamax      phimin       phimax
  // D=pi/180, {D*(ieta-1), D*(ieta+1), D*(iphi-11), D*(iphi-10)}
  unsigned subdet(_photon.isEB ? 0 : (_photon.eta() < 0. ? 1 : 2));
  cutres[NoisyRegion] = (noiseMap_.count(std::make_tuple(subdet, _photon.ix, _photon.iy)) == 0);
  cutres[E2E995] = (_photon.emax + _photon.e2nd) / (_photon.r9 * ptVariation(_photon, 0.)) < 0.95;
  cutres[Sieie08] = (_photon.sieie < 0.008);
  cutres[Sieie12] = (_photon.sieie < 0.012);
  cutres[Sieie15] = (_photon.sieie < 0.015);
  cutres[Sieie20] = (_photon.sieie < 0.020);
  cutres[Sipip08] = (_photon.sieie < 0.008);
  cutres[CHIso11] = (_photon.chIsoX[idTune_] < 11.);
  cutres[CHIsoMax11] = (_photon.chIsoMax < 11.);
  cutres[NHIsoLoose] = _photon.passNHIso(0, idTune_);
  cutres[PhIsoLoose] = _photon.passPhIso(0, idTune_);
  cutres[NHIsoTight] = _photon.passNHIso(2, idTune_);
  cutres[PhIsoTight] = _photon.passPhIso(2, idTune_);
  cutres[Sieie05] = (_photon.sieie < 0.005);
  cutres[Sipip05] = (_photon.sipip < 0.005);
  cutres[R9Unity] = (_photon.r9 < 1.0);

  cutres[ChargedPFVeto] = true;
  for (auto* cand : chargedCands_) {
    double dr(cand->dR(_photon));
    if (dr > 0.1)
      continue;

    double relPt(cand->pt() / ptVariation(_photon, 0.));
    if (relPt > 0.6) {
      cutres[ChargedPFVeto] = false;
      break;
    }
  }

  for (unsigned iC(0); iC != nSelections; ++iC)
    cutRes_[iC][_idx] = cutres[iC];

  if (vetoes_.size() != 0) {
    unsigned iV(0);
    for (; iV != vetoes_.size(); ++iV) {
      BitMask& mask(vetoes_[iV].second);

      if (vetoes_[iV].first) { // passing at least one of OR'ed cuts required
        if ((mask & cutres).none()) // but it failed all
          break;
      }
      else { // failing at least one of OR'ed cuts required
        if ((mask & cutres) == mask) // but it passed all
          break;
      }
    }
    if (iV == vetoes_.size()) // all veto requirements matched
      return -1;
  }

  if (selections_.size() != 0) {
    unsigned iS(0);
    for (; iS != selections_.size(); ++iS) {
      BitMask& mask(selections_[iS].second);

      if (selections_[iS].first) { // passing at least one of OR'ed cuts required
        if ((mask & cutres).none()) // but it failed all
          break;
      }
      else { // failing at least one of OR'ed cuts required
        if ((mask & cutres) == mask) // but it passed all
          break;
      }
    }
    if (iS == selections_.size()) // all selection requirements matched
      return 1;
  }
    
  return 0;
}

//--------------------------------------------------------------------
// TauVeto
//--------------------------------------------------------------------

bool
TauVeto::pass(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  panda::ParticleCollection* cols[] = {
    &_outEvent.photons,
    &_outEvent.muons,
    &_outEvent.electrons
  };

  bool hasNonOverlapping(false);
  for (unsigned iTau(0); iTau != _event.taus.size(); ++iTau) {
    auto& tau(_event.taus[iTau]);

    if (!tau.decayMode || tau.isoDeltaBetaCorr > 5.)
      continue;

    bool overlap(false);
    for (auto* col : cols) {
      unsigned iP(0);
      for (; iP != col->size(); ++iP) {
        if ((*col)[iP].dR2(tau) < 0.25)
          break;
      }
      if (iP != col->size()) {
        // there was a matching candidate
        overlap = true;
        break;
      }
    }
    
    if (!overlap) {
      _outEvent.taus.push_back(tau);
      hasNonOverlapping = true;
    }
  }

  return !hasNonOverlapping;
}

//--------------------------------------------------------------------
// LeptonMt
//--------------------------------------------------------------------

void
LeptonMt::addBranches(TTree& _skimTree)
{
  TString prefix;
  switch (flavor_) {
  case lElectron:
    prefix = "electrons";
    break;
  case lMuon:
    prefix = "muons";
    break;
  default:
    return;
  }

  _skimTree.Branch(prefix + ".mt", mt_, "mt[" + prefix + ".size]/F");
}

bool
LeptonMt::pass(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  panda::LeptonCollection const* leptons(0);
  if (flavor_ == lElectron && _outEvent.electrons.size() != 0)
    leptons = &_outEvent.electrons;
  else if (flavor_ == lMuon && _outEvent.muons.size() != 0)
    leptons = &_outEvent.muons;
  else
    return false;

  bool result(false);
  unsigned iL(0);
  for (auto& lepton : *leptons) {
    mt_[iL] = std::sqrt(2. * _event.t1Met.pt * lepton.pt() * (1. - std::cos(lepton.phi() - _event.t1Met.phi)));
    if ((iL == 0 || !onlyLeading_) && mt_[iL] > min_ && mt_[iL] < max_)
      result = true;

    ++iL;
  }

  return result;
}

//--------------------------------------------------------------------
// Mass
//--------------------------------------------------------------------

void
Mass::addBranches(TTree& _skimTree)
{
  _skimTree.Branch(prefix_ + ".mass", &mass_, "mass");
  _skimTree.Branch(prefix_ + ".pt", &pt_, "pt");
  _skimTree.Branch(prefix_ + ".eta", &eta_, "eta");
  _skimTree.Branch(prefix_ + ".phi", &phi_, "phi");
}

bool
Mass::pass(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  mass_ = -1.;
  pt_ = -1.;
  eta_ = -99.;
  phi_ = -99.;

  panda::ParticleCollection const* col[2]{};

  for (unsigned ic : {0, 1}) {
    switch (col_[ic]) {
    case cPhotons:
      col[ic] = &_outEvent.photons;
      break;
    case cElectrons:
      col[ic] = &_outEvent.electrons;
      break;
    case cMuons:
      col[ic] = &_outEvent.muons;
      break;
    case cTaus:
      col[ic] = &_outEvent.taus;
      break;
    default:
      break;
    }
  }

  if (!col[0] || !col[1] || col[0]->size() == 0 || col[1]->size() == 0)
    return false;

  TLorentzVector pair(0., 0., 0., 0.);

  if (col[0] == col[1]) {
    if (col[0]->size() == 1)
      return false;
    
    for (unsigned i1 = 0; i1 != col[0]->size(); ++i1) {
      for (unsigned i2 = i1; i2 != col[0]->size(); ++i2) {
	pair = (col[0]->at(i1).p4() + col[0]->at(i2).p4());
	mass_ = pair.M();
	
	if (mass_ > min_ && mass_ < max_) {
	  pt_ = pair.Pt();
	  eta_ = pair.Eta();
	  phi_ = pair.Phi();

	  return true; 
	}
      }
    }
  }
  else { 
    for (unsigned i1 = 0; i1 != col[0]->size(); ++i1) {
      for (unsigned i2 = 0; i2 != col[1]->size(); ++i2) {
	pair = (col[0]->at(i1).p4() + col[1]->at(i2).p4());
	mass_ = pair.M();
	
	if (mass_ > min_ && mass_ < max_) {
	  pt_ = pair.Pt();
	  eta_ = pair.Eta();
	  phi_ = pair.Phi();
	  
	  return true; 
	}
      }
    }
  }
  
  mass_ = pair.M();
  pt_ = pair.Pt();
  eta_ = pair.Eta();
  phi_ = pair.Phi();

  return false;
}

//--------------------------------------------------------------------
// OppositeSign
//--------------------------------------------------------------------

void
OppositeSign::addBranches(TTree& _skimTree)
{
  _skimTree.Branch(prefix_ + ".oppSign", &oppSign_, "oppSign/O");
}

bool
OppositeSign::pass(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  oppSign_ = 0;

  panda::LeptonCollection const* col[2]{};

  for (unsigned ic : {0, 1}) {
    switch (col_[ic]) {
    case cElectrons:
      col[ic] = &_outEvent.electrons;
      break;
    case cMuons:
      col[ic] = &_outEvent.muons;
      break;
    default:
      break;
    }
  }

  if (!col[0] || !col[1] || col[0]->size() == 0 || col[1]->size() == 0)
    return false;

  if (col[0] == col[1]) {
    if (col[0]->size() == 1)
      return false;

    for (unsigned i1 = 0; i1 != col[0]->size(); ++i1) {
      for (unsigned i2 = i1; i2 != col[0]->size(); ++i2) {
	oppSign_ = ((col[0]->at(i1).charge == col[0]->at(i2).charge) ? 0 : 1);

	if (oppSign_)
	  return true;
      }
    }
  }
  else {
    for (unsigned i1 = 0; i1 != col[0]->size(); ++i1) {
      for (unsigned i2 = 0; i2 != col[1]->size(); ++i2) {
	oppSign_ = ((col[0]->at(0).charge == col[1]->at(0).charge) ? 0 : 1);

	if (oppSign_)
	  return true; 
      }
    }
  }

  return false;
}

//--------------------------------------------------------------------
// BjetVeto
//--------------------------------------------------------------------

void
BjetVeto::addBranches(TTree& _skimTree)
{
  bjets_.book(_skimTree);
}

bool
BjetVeto::pass(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  // veto condition: loose, pt > 10 GeV, no matching candidate photon / lepton

  panda::ParticleCollection* cols[] = {
    &_outEvent.photons,
    &_outEvent.muons,
    &_outEvent.electrons,
    &_outEvent.taus
  };

  bjets_.clear();
  bool hasNonOverlapping(false);
  for (unsigned iB(0); iB != _outEvent.jets.size(); ++iB) {
    auto& jet(_outEvent.jets[iB]);
    if (jet.csv < 0.800 || jet.pt() < 20.)
      continue;

    bool overlap(false);
    for (auto* col : cols) {
      unsigned iP(0);
      for (; iP != col->size(); ++iP) {
        if ((*col)[iP].dR2(jet) < 0.25)
          break;
      }
      if (iP != col->size()) {
        // there was a matching candidate
        overlap = true;
        break;
      }
    }
    
    if (!overlap) { 
      bjets_.push_back(jet);
      hasNonOverlapping = true;
    }
  }

  return !hasNonOverlapping;
}

//--------------------------------------------------------------------
// PhotonMetDPhi
//--------------------------------------------------------------------

void
PhotonMetDPhi::addBranches(TTree& _skimTree)
{
  if (metSource_ == kInMet) {
    _skimTree.Branch("t1Met.realPhotonDPhi", &dPhi_, "realPhotonDPhi/F");
    _skimTree.Branch("t1Met.realPhotonDPhiJECUp", &dPhiJECUp_, "realPhotonDPhiJECUp/F");
    _skimTree.Branch("t1Met.realPhotonDPhiJECDown", &dPhiJECDown_, "realPhotonDPhiJECDown/F");
    _skimTree.Branch("t1Met.realPhotonDPhiGECUp", &dPhiGECUp_, "realPhotonDPhiGECUp/F");
    _skimTree.Branch("t1Met.realPhotonDPhiGECDown", &dPhiGECDown_, "realPhotonDPhiGECDown/F");
    _skimTree.Branch("t1Met.realPhotonDPhiUnclUp", &dPhiUnclUp_, "realPhotonDPhiUnclUp/F");
    _skimTree.Branch("t1Met.realPhotonDPhiUnclDown", &dPhiUnclDown_, "realPhotonDPhiUnclDown/F");
  }
  else {
    _skimTree.Branch("t1Met.photonDPhi", &dPhi_, "photonDPhi/F");
    _skimTree.Branch("t1Met.photonDPhiJECUp", &dPhiJECUp_, "photonDPhiJECUp/F");
    _skimTree.Branch("t1Met.photonDPhiJECDown", &dPhiJECDown_, "photonDPhiJECDown/F");
    _skimTree.Branch("t1Met.photonDPhiGECUp", &dPhiGECUp_, "photonDPhiGECUp/F");
    _skimTree.Branch("t1Met.photonDPhiGECDown", &dPhiGECDown_, "photonDPhiGECDown/F");
    _skimTree.Branch("t1Met.photonDPhiUnclUp", &dPhiUnclUp_, "photonDPhiUnclUp/F");
    _skimTree.Branch("t1Met.photonDPhiUnclDown", &dPhiUnclDown_, "photonDPhiUnclDown/F");
  }
  // _skimTree.Branch("t1Met.photonDPhiJER", &dPhiJER_, "photonDPhiJER/F");
  // _skimTree.Branch("t1Met.photonDPhiJERUp", &dPhiJERUp_, "photonDPhiJERUp/F");
  // _skimTree.Branch("t1Met.photonDPhiJERDown", &dPhiJERDown_, "photonDPhiJERDown/F");
}

bool
PhotonMetDPhi::pass(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  dPhi_ = 0.;
  if (_outEvent.photons.size() != 0) {
    panda::RecoMet const* met(0);
    if (metSource_ == kInMet)
      met = &_event.t1Met;
    else
      met = &_outEvent.t1Met;

    double metPhiGECUp(0.);
    double metPhiGECDown(0.);
    if (metVar_) {
      metPhiGECUp = metVar_->gecUp().Phi();
      metPhiGECDown = metVar_->gecDown().Phi();
    }

    dPhi_ = std::abs(TVector2::Phi_mpi_pi(met->phi - _outEvent.photons[0].phi()));

    dPhiJECUp_ = std::abs(TVector2::Phi_mpi_pi(met->phiCorrUp - _outEvent.photons[0].phi()));
    dPhiJECDown_ = std::abs(TVector2::Phi_mpi_pi(met->phiCorrDown - _outEvent.photons[0].phi()));
    dPhiUnclUp_ = std::abs(TVector2::Phi_mpi_pi(met->phiUnclUp - _outEvent.photons[0].phi()));
    dPhiUnclDown_ = std::abs(TVector2::Phi_mpi_pi(met->phiUnclDown - _outEvent.photons[0].phi()));

    if (metVar_) {
      dPhiGECUp_ = std::abs(TVector2::Phi_mpi_pi(metPhiGECUp - _outEvent.photons[0].phi()));
      dPhiGECDown_ = std::abs(TVector2::Phi_mpi_pi(metPhiGECDown - _outEvent.photons[0].phi()));
      // dPhiJER_ = std::abs(TVector2::Phi_mpi_pi(metVar_->jer().Phi() - _outEvent.photons[0].phi()));
      // dPhiJERUp_ = std::abs(TVector2::Phi_mpi_pi(metVar_->jerUp().Phi() - _outEvent.photons[0].phi()));
      // dPhiJERDown_ = std::abs(TVector2::Phi_mpi_pi(metVar_->jerDown().Phi() - _outEvent.photons[0].phi()));      
    }
  }

  if (invert_)
    nominalResult_ = dPhi_ < cutValue_;
  else
    nominalResult_ = dPhi_ > cutValue_;

  // for (double dPhi : {dPhi_, dPhiJECUp_, dPhiJECDown_, dPhiGECUp_, dPhiGECDown_, dPhiUnclUp_, dPhiUnclDown_, dPhiJER_, dPhiJERUp_, dPhiJERDown_}) {
  for (double dPhi : {dPhi_, dPhiJECUp_, dPhiJECDown_, dPhiGECUp_, dPhiGECDown_, dPhiUnclUp_, dPhiUnclDown_}) {
    if (invert_) {
      if (dPhi > cutValue_)
        return true;
    }
    else {
      if (dPhi < cutValue_)
        return true;
    }
  }
  return false;
}

//--------------------------------------------------------------------
// JetMetDPhi
//--------------------------------------------------------------------

void
JetMetDPhi::addBranches(TTree& _skimTree)
{
  if (metSource_ == kInMet) {
    _skimTree.Branch("t1Met.realMinJetDPhi", &dPhi_, "realMinJetDPhi/F");
    _skimTree.Branch("t1Met.realMinJetDPhiJECUp", &dPhiJECUp_, "realMinJetDPhiJECUp/F");
    _skimTree.Branch("t1Met.realMinJetDPhiJECDown", &dPhiJECDown_, "realMinJetDPhiJECDown/F");
    _skimTree.Branch("t1Met.realMinJetDPhiGECUp", &dPhiGECUp_, "realMinJetDPhiGECUp/F");
    _skimTree.Branch("t1Met.realMinJetDPhiGECDown", &dPhiGECDown_, "realMinJetDPhiGECDown/F");
    _skimTree.Branch("t1Met.realMinJetDPhiUnclUp", &dPhiUnclUp_, "realMinJetDPhiUnclUp/F");
    _skimTree.Branch("t1Met.realMinJetDPhiUnclDown", &dPhiUnclDown_, "realMinJetDPhiUnclDown/F");
  }
  else {
    _skimTree.Branch("t1Met.minJetDPhi", &dPhi_, "minJetDPhi/F");
    _skimTree.Branch("t1Met.minJetDPhiJECUp", &dPhiJECUp_, "minJetDPhiJECUp/F");
    _skimTree.Branch("t1Met.minJetDPhiJECDown", &dPhiJECDown_, "minJetDPhiJECDown/F");
    _skimTree.Branch("t1Met.minJetDPhiGECUp", &dPhiGECUp_, "minJetDPhiGECUp/F");
    _skimTree.Branch("t1Met.minJetDPhiGECDown", &dPhiGECDown_, "minJetDPhiGECDown/F");
    _skimTree.Branch("t1Met.minJetDPhiUnclUp", &dPhiUnclUp_, "minJetDPhiUnclUp/F");
    _skimTree.Branch("t1Met.minJetDPhiUnclDown", &dPhiUnclDown_, "minJetDPhiUnclDown/F");
  }
  // _skimTree.Branch("t1Met.minJetDPhiJER", &dPhiJER_, "minJetDPhiJER/F");
  // _skimTree.Branch("t1Met.minJetDPhiJERUp", &dPhiJERUp_, "minJetDPhiJERUp/F");
  // _skimTree.Branch("t1Met.minJetDPhiJERDown", &dPhiJERDown_, "minJetDPhiJERDown/F");
}

bool
JetMetDPhi::pass(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  unsigned nJ(0);
  unsigned nJCorrUp(0);
  unsigned nJCorrDown(0);
  // unsigned nJJER(0);
  // unsigned nJJERUp(0);
  // unsigned nJJERDown(0);

  dPhi_ = 4.;
  dPhiJECUp_ = 4.;
  dPhiJECDown_ = 4.;
  dPhiGECUp_ = 4.;
  dPhiGECDown_ = 4.;
  dPhiUnclUp_ = 4.;
  dPhiUnclDown_ = 4.;
  // dPhiJER_ = 4.;
  // dPhiJERUp_ = 4.;
  // dPhiJERDown_ = 4.;

  panda::RecoMet const* met(0);
  if (metSource_ == kInMet)
    met = &_event.t1Met;
  else
    met = &_outEvent.t1Met;

  double metPhiGECUp(0.);
  double metPhiGECDown(0.);
  if (metVar_) {
    metPhiGECUp = metVar_->gecUp().Phi();
    metPhiGECDown = metVar_->gecDown().Phi();
  }

  for (unsigned iJ(0); iJ != _outEvent.jets.size(); ++iJ) {
    auto& jet(_outEvent.jets[iJ]);

    if (jet.pt() > 30. && nJ < 4) {
      ++nJ;
      double dPhi(std::abs(TVector2::Phi_mpi_pi(jet.phi() - met->phi)));
      if (dPhi < dPhi_)
        dPhi_ = dPhi;

      if (metVar_) {
        dPhi = std::abs(TVector2::Phi_mpi_pi(jet.phi() - metPhiGECUp));
        if (dPhi < dPhiGECUp_)
          dPhiGECUp_ = dPhi;

        dPhi = std::abs(TVector2::Phi_mpi_pi(jet.phi() - metPhiGECDown));
        if (dPhi < dPhiGECDown_)
          dPhiGECDown_ = dPhi;
      }

      dPhi = std::abs(TVector2::Phi_mpi_pi(jet.phi() - met->phiUnclUp));
      if (dPhi < dPhiUnclUp_)
        dPhiUnclUp_ = dPhi;

      dPhi = std::abs(TVector2::Phi_mpi_pi(jet.phi() - met->phiUnclDown));
      if (dPhi < dPhiUnclDown_)
        dPhiUnclDown_ = dPhi;
    }

    if (jet.ptCorrUp > 30. && nJCorrUp < 4) {
      ++nJCorrUp;
      double dPhi(std::abs(TVector2::Phi_mpi_pi(jet.phi() - met->phiCorrUp)));
      if (dPhi < dPhiJECUp_)
        dPhiJECUp_ = dPhi;
    }

    if (jet.ptCorrDown > 30. && nJCorrDown < 4) {
      ++nJCorrDown;
      double dPhi(std::abs(TVector2::Phi_mpi_pi(jet.phi() - met->phiCorrDown)));
      if (dPhi < dPhiJECDown_)
        dPhiJECDown_ = dPhi;
    }

    // if (metVar_) {
    //   if (jetCleaning_) {
    //     if (jetCleaning_->ptScaled(iJ) > 30. && nJJER < 4) {
    //       ++nJJER;
    //       double dPhi(std::abs(TVector2::Phi_mpi_pi(jet.phi() - metVar_->jer().Phi())));
    //       if (dPhi < dPhiJER_)
    //         dPhiJER_ = dPhi;
    //     }
        
    //     if (jetCleaning_->ptScaledUp(iJ) > 30. && nJJERUp < 4) {
    //       ++nJJERUp;
    //       double dPhi(std::abs(TVector2::Phi_mpi_pi(jet.phi() - metVar_->jerUp().Phi())));
    //       if (dPhi < dPhiJERUp_)
    //         dPhiJERUp_ = dPhi;
    //     }
        
    //     if (jetCleaning_->ptScaledDown(iJ) > 30. && nJJERDown < 4) {
    //       ++nJJERDown;
    //       double dPhi(std::abs(TVector2::Phi_mpi_pi(jet.phi() - metVar_->jerDown().Phi())));
    //       if (dPhi < dPhiJERDown_)
    //         dPhiJERDown_ = dPhi;
    //     }
    //   }
    // }
  }

  if (passIfIsolated_) {
    nominalResult_ = dPhi_ > 0.5;

    //    for (double dPhi : {dPhi_, dPhiJECUp_, dPhiJECDown_, dPhiGECUp_, dPhiGECDown_, dPhiUnclUp_, dPhiUnclDown_, dPhiJER_, dPhiJERUp_, dPhiJERDown_}) {
    for (double dPhi : {dPhi_, dPhiJECUp_, dPhiJECDown_, dPhiGECUp_, dPhiGECDown_, dPhiUnclUp_, dPhiUnclDown_}) {
      if (dPhi > 0.5)
        return true;
    }
    return false;
  }
  else {
    nominalResult_ = dPhi_ < 0.5;

    //    for (double dPhi : {dPhi_, dPhiJECUp_, dPhiJECDown_, dPhiGECUp_, dPhiGECDown_, dPhiUnclUp_, dPhiUnclDown_, dPhiJER_, dPhiJERUp_, dPhiJERDown_}) {
    for (double dPhi : {dPhi_, dPhiJECUp_, dPhiJECDown_, dPhiGECUp_, dPhiGECDown_, dPhiUnclUp_, dPhiUnclDown_}) {
      if (dPhi < 0.5)
        return true;
    }
    return false;
  }
}

//--------------------------------------------------------------------
// LeptonSelection
//--------------------------------------------------------------------

LeptonSelection::LeptonSelection(char const* name) :
  MonophotonCut(name)
{
  failingMuons_ = new panda::MuonCollection("failingsMuons");
  failingElectrons_ = new panda::ElectronCollection("failingElectrons");
}

LeptonSelection::~LeptonSelection()
{
  delete failingMuons_;
  delete failingElectrons_;
}

void
LeptonSelection::addBranches(TTree& _skimTree)
{
  failingMuons_->book(_skimTree);
  failingElectrons_->book(_skimTree);
}

bool
LeptonSelection::pass(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  bool foundMedium(false);
  bool foundTight(false);
  unsigned nLooseIsoMuons(0);

  failingMuons_->clear();
  failingElectrons_->clear();

  std::vector<panda::ParticleCollection*> cols;
  cols.push_back(&_outEvent.photons);

  for (unsigned iM(0); iM != _event.muons.size(); ++iM) {
    auto& muon(_event.muons[iM]);

    if (std::abs(muon.eta()) > 2.5 || muon.pt() < 10.)
      continue;
   
    bool overlap(false);
    for (auto* col : cols) {
      unsigned iP(0);
      for (; iP != col->size(); ++iP) {
        if ((*col)[iP].dR2(muon) < 0.25)
	  break;
      }
      if (iP != col->size()) {
	// there was a matching candidate
	overlap = true;
	break;
      }
    }
    
    if (overlap)
      continue;

    if (nMu_ != 0 && muon.pt() > 30.) {
      if (muon.tight && muon.combIso() / muon.pt() < 0.15)
        foundTight = true;
      // if ((mediumBtoF_ && muon.mediumBtoF) || (!mediumBtoF_ && muon.medium))
      if (muon.medium)
        foundMedium = true;
    }
    
    if (muon.loose) {
      _outEvent.muons.push_back(muon);
      if ((muon.combIso() / muon.pt()) < 0.25)
        ++nLooseIsoMuons;
    }
    else if (muon.matchedGen.idx() != -1)
      failingMuons_->push_back(muon);
  }

  cols.push_back(&_outEvent.muons);

  for (unsigned iE(0); iE != _event.electrons.size(); ++iE) {
    auto& electron(_event.electrons[iE]);

    if (std::abs(electron.eta()) > 2.5 || electron.pt() < 10.)
      continue;

    bool overlap(false);
    for (auto* col : cols) {
      unsigned iP(0);
      for (; iP != col->size(); ++iP) {
	if ((*col)[iP].dR2(electron) < 0.25)
	  break;
      }
      if (iP != col->size()) {
	// there was a matching candidate
	overlap = true;
	break;
      }
    }
    
    if (overlap)
      continue;

    if (nEl_ != 0 && electron.pt() > 30.) {
      if (electron.tight)
        foundTight = true;
      if (electron.medium)
        foundMedium = true;
    }

    if (electron.loose)
      _outEvent.electrons.push_back(electron);
    else if (electron.matchedGen.idx() != -1)
      failingElectrons_->push_back(electron);
  }

  if (requireTight_ && !foundTight)
    return false;

  if (requireMedium_ && !foundMedium)
    return false;

  if (strictMu_ && strictEl_)
    return _outEvent.electrons.size() == nEl_ && _outEvent.muons.size() == nMu_ && nLooseIsoMuons == nMu_;
  else if (strictMu_ && !strictEl_)
    return _outEvent.electrons.size() >= nEl_ && _outEvent.muons.size() == nMu_ && nLooseIsoMuons == nMu_;
  else if (!strictMu_ && strictEl_)
    return _outEvent.electrons.size() == nEl_ && _outEvent.muons.size() >= nMu_ && nLooseIsoMuons >= nMu_;
  else
    return _outEvent.electrons.size() >= nEl_ && _outEvent.muons.size() >= nMu_ && nLooseIsoMuons >= nMu_;
}

//--------------------------------------------------------------------
// FakeElectron
//--------------------------------------------------------------------

bool
FakeElectron::pass(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  auto& photons(_outEvent.photons);

  for (unsigned iE(0); iE != _event.electrons.size(); ++iE) {
    auto& electron(_event.electrons[iE]);

    if (!electron.veto || electron.loose || electron.pt() < 30.)
      continue;

    unsigned iP(0);
    for (; iP != photons.size(); ++iP) {
      if (photons[iP].dR2(electron) < 0.25)
        break;
    }
    if (iP != photons.size()) // overlap with photon
      continue;
    
    _outEvent.electrons.push_back(electron);
  }

  return _outEvent.electrons.size() != 0;
}

//--------------------------------------------------------------------
// Met
//--------------------------------------------------------------------

bool
Met::pass(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  if (metSource_ == kInMet)
    return _event.t1Met.pt > min_ && _event.t1Met.pt < max_;
  else
    return _outEvent.t1Met.pt > min_ && _outEvent.t1Met.pt < max_;
}

//--------------------------------------------------------------------
// PhotonPtOverMet
//--------------------------------------------------------------------

bool
PhotonPtOverMet::pass(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  if (metSource_ == kInMet)
    return (_outEvent.photons[0].scRawPt / _event.t1Met.pt) < max_;
  else
    return (_outEvent.photons[0].scRawPt / _outEvent.t1Met.pt) < max_;
}

//--------------------------------------------------------------------
// MtRange
//--------------------------------------------------------------------

bool
MtRange::pass(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  if (!calc_ || _outEvent.photons.size() == 0)
    return false;

  double mt(calc_->getMt(0));

  return mt > min_ && mt < max_;
}

//--------------------------------------------------------------------
// HighPtJetSelection
//--------------------------------------------------------------------

bool
HighPtJetSelection::pass(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  unsigned nJets(0);

  for (unsigned iJ(0); iJ != _outEvent.jets.size(); ++iJ) {
    auto& jet(_outEvent.jets[iJ]);

    if (jet.pt() > min_ && std::abs(jet.eta()) < 5.)
      ++nJets;
  }

  return nJets >= nMin_ && nJets <= nMax_;
}

//--------------------------------------------------------------------
// DijetSelection
//--------------------------------------------------------------------

void
DijetSelection::setDEtajjReweight(TFile* _plotsFile)
{
  delete reweightSource_;

  auto* gjets(static_cast<TH1D*>(_plotsFile->Get("detajjAll/gjets")));
  auto* obs(static_cast<TH1D*>(_plotsFile->Get("detajjAll/data_obs")));
  auto* qcd(static_cast<TH1D*>(_plotsFile->Get("detajjAll/hfake")));

  reweightSource_ = static_cast<TH1D*>(obs->Clone("detajjweight"));
  reweightSource_->SetDirectory(0);
  reweightSource_->Add(qcd, -1.);
  reweightSource_->Divide(gjets);
}

void
DijetSelection::addBranches(TTree& _skimTree)
{
  TString colName("dijet");
  if (jetType_ == jGen)
    colName = "digenjet";

  _skimTree.Branch(colName + ".size", &nDijet_, "size/i");
  _skimTree.Branch(colName + ".dEtajj", dEtajj_, "dEtajj[" + colName + ".size]/F");
  _skimTree.Branch(colName + ".mjj", mjj_, "mjj[" + colName + ".size]/F");
  _skimTree.Branch(colName + ".ij1", ij1_, "ij1[" + colName + ".size]/i");
  _skimTree.Branch(colName + ".ij2", ij2_, "ij2[" + colName + ".size]/i");
  if (savePassing_) {
    _skimTree.Branch("p" + colName + ".size", &nDijetPassing_, "size/i");
    _skimTree.Branch("p" + colName + ".dEtajj", dEtajjPassing_, "dEtajj[p" + colName + ".size]/F");
    _skimTree.Branch("p" + colName + ".mjj", mjjPassing_, "mjj[p" + colName + ".size]/F");
    _skimTree.Branch("p" + colName + ".ij1", ij1Passing_, "ij1[p" + colName + ".size]/i");
    _skimTree.Branch("p" + colName + ".ij2", ij2Passing_, "ij2[p" + colName + ".size]/i");
  }

  if (reweightSource_)
    _skimTree.Branch("reweight_detajj", &detajjReweight_, "reweight_detajj/D");
}

void
DijetSelection::addInputBranch(panda::utils::BranchList& _blist)
{
  if (jetType_ == jGen)
    _blist += {"ak4GenJets"};
}

bool
DijetSelection::pass(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  nDijet_ = 0;
  nDijetPassing_ = 0;

  panda::ParticleCollection const* jets(0);
  switch (jetType_) {
  case jReco:
    jets = &_outEvent.jets;
    break;
  case jGen:
    jets = &_event.genJets;
    break;
  default:
    return false;
  }

  for (unsigned iJ1(0); iJ1 != jets->size(); ++iJ1) {
    if (leadingOnly_ && iJ1 != 0)
      break;

    auto& jet1((*jets)[iJ1]);

    if (jet1.pt() < minPt1_)
      break;

    if (jetType_ == jReco) {
      auto& recoJet(static_cast<panda::Jet const&>(jet1));
      if (!recoJet.tight || !JetCleaning::passPUID(2, recoJet))
        continue;
    }

    for (unsigned iJ2(iJ1 + 1); iJ2 != jets->size(); ++iJ2) {
      if (leadingOnly_ && iJ2 != 1)
        break;

      auto& jet2((*jets)[iJ2]);

      if (jet2.pt() < minPt2_)
        break;

      if (jet1.eta() * jet2.eta() > 0.)
        continue;

      if (jetType_ == jReco) {
        auto& recoJet(static_cast<panda::Jet const&>(jet2));
        if (!recoJet.tight || !JetCleaning::passPUID(2, recoJet))
          continue;
      }

      if (nDijet_ == NMAX_PARTICLES)
        throw std::runtime_error(TString::Format("Too many dijet pairs in an event %i, %i, %llu", _event.runNumber, _event.lumiNumber, _event.eventNumber).Data());

      dEtajj_[nDijet_] = jet1.eta() - jet2.eta();
      mjj_[nDijet_] = (jet1.p4() + jet2.p4()).M();
      ij1_[nDijet_] = iJ1;
      ij2_[nDijet_] = iJ2;

      if (std::abs(dEtajj_[nDijet_]) > minDEta_ && mjj_[nDijet_] > minMjj_) {
        dEtajjPassing_[nDijetPassing_] = dEtajj_[nDijet_];
        mjjPassing_[nDijetPassing_] = mjj_[nDijet_];
        ij1Passing_[nDijetPassing_] = iJ1;
        ij2Passing_[nDijetPassing_] = iJ2;

        if (reweightSource_ && nDijetPassing_ == 0) {
          int ibin(reweightSource_->FindFixBin(dEtajj_[nDijet_]));
          _outEvent.weight *= reweightSource_->GetBinContent(ibin);
          detajjReweight_ = reweightSource_->GetBinContent(ibin);
        }

        ++nDijetPassing_;
      }

      ++nDijet_;
    }
  }

  return nDijetPassing_ != 0;
}

//--------------------------------------------------------------------
// PhotonPtTruncator
//--------------------------------------------------------------------

bool
PhotonPtTruncator::pass(panda::EventMonophoton const& _event, panda::EventBase&)
{
  for (unsigned iP(0); iP != _event.partons.size(); ++iP) {
    auto& parton(_event.partons[iP]);

    if (parton.pdgid == 22 && (parton.pt() < min_ || parton.pt() > max_))
      return false;
  }

  return true;
}

//--------------------------------------------------------------------
// HtTruncator
//--------------------------------------------------------------------

void
HtTruncator::addBranches(TTree& _skimTree)
{
  _skimTree.Branch("genHt", &ht_, "genHt/F");
}

bool
HtTruncator::pass(panda::EventMonophoton const& _event, panda::EventBase&)
{
  ht_ = 0.; // ht is an additive quantity; need to start with 0.
  for (unsigned iP(0); iP != _event.partons.size(); ++iP) {
    auto& parton(_event.partons[iP]);

    if ( !(parton.pdgid == 21 || std::abs(parton.pdgid) < 6))
      continue;

    ht_ += parton.pt();
  }

  if (ht_ < min_ || ht_ > max_)
      return false;

  return true;
}

//--------------------------------------------------------------------
// GenBosonPtTruncator
//--------------------------------------------------------------------

void
GenBosonPtTruncator::addBranches(TTree& _skimTree)
{
  _skimTree.Branch("genBosonPt", &pt_, "genBosonPt/F");
}

bool
GenBosonPtTruncator::pass(panda::EventMonophoton const& _event, panda::EventBase&)
{
  pt_ = -1.;
  unsigned nLep = 0;
  TLorentzVector genBoson(0., 0., 0., 0.);
  for (unsigned iP(0); iP != _event.partons.size(); ++iP) {
    auto& parton(_event.partons[iP]);

    // don't run on diboson samples for now
    if (nLep > 2)
      break;

    if ( (std::abs(parton.pdgid) < 11) || (std::abs(parton.pdgid) > 16) )
      continue;

    genBoson += parton.p4();
    nLep++;
  }

  if (nLep == 2)
    pt_ = genBoson.Pt();

  if (pt_ < min_ || pt_ > max_)
      return false;

  return true;
}

//--------------------------------------------------------------------
// GenParticleSelection
//--------------------------------------------------------------------

bool
GenParticleSelection::pass(panda::EventMonophoton const& _event, panda::EventBase&)
{
  for (unsigned iP(0); iP != _event.genParticles.size(); ++iP) {
    auto& part(_event.genParticles[iP]);

    if (std::abs(part.pdgid) != pdgId_)
      continue;

    if (std::abs(part.eta()) > maxEta_ || std::abs(part.eta()) < minEta_ )
      continue;

    if (part.pt() < minPt_ || part.pt() > maxPt_)
      continue;

    return true;
  }

  return false;
}


//--------------------------------------------------------------------
// EcalCrackVeto
//--------------------------------------------------------------------

void
EcalCrackVeto::addBranches(TTree& _skimTree)
{
  _skimTree.Branch("ecalCrackVeto", &ecalCrackVeto_, "ecalCrackVeto/O");
}

bool
EcalCrackVeto::pass(panda::EventMonophoton const& _event, panda::EventBase&)
{
  for (unsigned iP(0); iP != _event.photons.size(); ++iP) {
    auto& photon(_event.photons[iP]);

    if (photon.scRawPt < minPt_)
      continue;

    if (std::abs(photon.eta()) > 1.4 && std::abs(photon.eta()) < 1.6) {
      ecalCrackVeto_ = false;
      return false;
    }
  }
  
  for (unsigned iJ(0); iJ != _event.jets.size(); ++iJ) {
    auto& jet(_event.jets[iJ]);

    if (jet.pt() < minPt_)
      continue;

    if (std::abs(jet.eta()) > 1.4 && std::abs(jet.eta()) < 1.6) {
      ecalCrackVeto_ = false;
      return false;
    }
  }

  ecalCrackVeto_ = true;
  return true;
}

//--------------------------------------------------------------------
// TagAndProbePairZ
//--------------------------------------------------------------------

TagAndProbePairZ::TagAndProbePairZ(char const* name) :
  Cut(name),
  tp_("tp")
{
}

TagAndProbePairZ::~TagAndProbePairZ()
{
  delete tags_;
  delete probes_;
}

void
TagAndProbePairZ::addBranches(TTree& _skimTree)
{
  switch (tagSpecies_) {
  case cMuons:
    tags_ = new panda::MuonCollection("tag");
    break;
  case cElectrons:
    tags_ = new panda::ElectronCollection("tag");
    break;
  case cPhotons:
    tags_ = new panda::XPhotonCollection("tag");
    break;
  default:
    throw runtime_error("Invalid tag species");
  }

  switch (probeSpecies_) {
  case cMuons:
    probes_ = new panda::MuonCollection("probe");
    break;
  case cElectrons:
    probes_ = new panda::ElectronCollection("probe");
    break;
  case cPhotons:
    probes_ = new panda::XPhotonCollection("probe");
    break;
  default:
    throw runtime_error("Invalid tag species");
  }

  tp_.book(_skimTree);
  _skimTree.Branch("tp.oppSign", &zOppSign_, "tp.oppSign/O");

  tags_->book(_skimTree);
  probes_->book(_skimTree);
}

bool
TagAndProbePairZ::pass(panda::EventMonophoton const& _event, panda::EventBase&)
{
  panda::LeptonCollection const* inTags(0);
  panda::LeptonCollection const* inProbes(0);
  TLorentzVector tnpPair(0., 0., 0., 0.);

  // OK, object-orientation and virtual methods cannot quite solve the problem at hand (push back the objects with full info).
  // We will cheat.
  std::function<void(panda::Particle const&)> push_back_tag;
  std::function<void(panda::Particle const&)> push_back_probe;

  switch (tagSpecies_) {
  case cMuons:
    inTags = &_event.muons;
    push_back_tag = [this](panda::Particle const& tag) {
      static_cast<panda::MuonCollection*>(this->tags_)->push_back(static_cast<panda::Muon const&>(tag));
    };
    break;
  case cElectrons:
    inTags = &_event.electrons;
    push_back_tag = [this](panda::Particle const& tag) {
      static_cast<panda::ElectronCollection*>(this->tags_)->push_back(static_cast<panda::Electron const&>(tag));
    };
    break;
  case cPhotons:
    // inTags = &_event.photons;
    push_back_tag = [this](panda::Particle const& tag) {
      static_cast<panda::XPhotonCollection*>(this->tags_)->push_back(static_cast<panda::XPhoton const&>(tag));
    };
    break;
  default:
    throw runtime_error("Invalid tag species");
  }
  
  switch (probeSpecies_) {
  case cMuons:
    inProbes = &_event.muons;
    push_back_probe = [this](panda::Particle const& probe) {
      static_cast<panda::MuonCollection*>(this->probes_)->push_back(static_cast<panda::Muon const&>(probe));
    };
    break;
  case cElectrons:
    inProbes = &_event.electrons;
    push_back_probe = [this](panda::Particle const& probe) {
      static_cast<panda::ElectronCollection*>(this->probes_)->push_back(static_cast<panda::Electron const&>(probe));
    };
    break;
  case cPhotons:
    // inProbes = &_event.photons; 
    push_back_probe = [this](panda::Particle const& probe) {
      static_cast<panda::XPhotonCollection*>(this->probes_)->push_back(static_cast<panda::XPhoton const&>(probe));
    };
    break;
  default:
    throw runtime_error("Invalid tag species");
  }

  tp_.clear();
  tags_->clear();
  probes_->clear();
  nUniqueZ_ = 0;

  for (unsigned iT(0); iT != inTags->size(); ++iT) {
    auto& tag = inTags->at(iT);
    
    if ( !(tag.tight && tag.pt() > 30.))
      continue;
    
    for (unsigned iP(0); iP != inProbes->size(); ++iP) {
      auto& probe = inProbes->at(iP);
      
      if ( !(probe.loose && probe.pt() > 20.))
	continue;

      // don't want the same object in case the tag and probe collections are the same
      // currently going with dR < 0.3, maybe change?
      if (tag.dR2(probe) < 0.09 ) 
	continue;

      tnpPair = (tag.p4() + probe.p4());
      double mass(tnpPair.M());
      // tighter mass range was just so I could use cutresult to debug, switched backed
      if ( !(mass > 60. && mass < 120.))
	continue;

      push_back_tag(tag);
      push_back_probe(probe);

      // cannot push back here; resize and use the last element
      tp_.resize(tp_.size() + 1);
      auto& z(tp_.back());
      z.setPtEtaPhiM(tnpPair.Pt(), tnpPair.Eta(), tnpPair.Phi(), tnpPair.M());
      zOppSign_ = ( (tag.charge == probe.charge) ? 0 : 1);

      // check if other tag-probe pairs match this pair
      unsigned iZ(0);
      for (; iZ != tp_.size() - 1; ++iZ) {
        if ((tag.dR2(tags_->at(iZ)) < 0.09 && probe.dR2(probes_->at(iZ)) < 0.09) ||
            (tag.dR2(probes_->at(iZ)) < 0.09 && probe.dR2(tags_->at(iZ)) < 0.09))
          break;
      }
      // if not, increment unique Z counter
      if (iZ == tp_.size() -1)
        ++nUniqueZ_;
    }
  }

  return tp_.size() != 0;
}

//--------------------------------------------------------------------
// ZJetBackToBack
//--------------------------------------------------------------------

bool
ZJetBackToBack::pass(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  if (tnp_->getNUniqueZ() != 1)
    return false;

  for (unsigned iJ(0); iJ != _outEvent.jets.size(); ++iJ) {
    auto& jet( _outEvent.jets[iJ]);

    if ( jet.pt() < minJetPt_)
      continue;

    if ( std::abs(TVector2::Phi_mpi_pi(jet.phi() - tnp_->getPhiZ(0))) > dPhiMin_ )
      return true;
  }
  return false;
}

//--------------------------------------------------------------------
// PFMatch
//--------------------------------------------------------------------

void
PFMatch::addInputBranch(panda::utils::BranchList& _blist)
{
  _blist += {"pfCandidates"};
}

void
PFMatch::addBranches(TTree& _skimTree)
{
  _skimTree.Branch("photons.pfDR", matchedDR_, "pfDR[photons.size]/F");
  _skimTree.Branch("photons.pfRelPt", matchedRelPt_, "pfRelPt[photons.size]/F");
  _skimTree.Branch("photons.pfPtype", matchedPtype_, "pfPtype[photons.size]/s");
}

void
PFMatch::apply(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  std::vector<panda::PFCand const*> chargedCands;

  for (auto& cand : _event.pfCandidates) {
    if (cand.q() != 0)
      chargedCands.push_back(&cand);
  }

  for (unsigned iPh(0); iPh != _outEvent.photons.size(); ++iPh) {
    auto& photon(_outEvent.photons[iPh]);

    matchedPtype_[iPh] = -1;
    matchedDR_[iPh] = -1.;
    matchedRelPt_[iPh] = -1.;

    for (auto* cand : chargedCands) {
      double dr(cand->dR(photon));
      double relPt(cand->pt() / photon.scRawPt);
      if (dr < dr_ && relPt > matchedRelPt_[iPh]) {
        matchedPtype_[iPh] = cand->ptype;
        matchedRelPt_[iPh] = relPt;
        matchedDR_[iPh] = dr;
      }
    }
  }
}

//--------------------------------------------------------------------
// TriggerEfficiency
//--------------------------------------------------------------------

void
TriggerEfficiency::setFormula(char const* formula)
{
  delete formula_;
  formula_ = new TF1("TriggerEfficiency", formula, 0., 6500.);
}

void
TriggerEfficiency::setUpFormula(char const* formula)
{
  delete upFormula_;
  upFormula_ = new TF1("TriggerEfficiencyUp", formula, 0., 6500.);
}

void
TriggerEfficiency::setDownFormula(char const* formula)
{
  delete downFormula_;
  downFormula_ = new TF1("TriggerEfficiencyDown", formula, 0., 6500.);
}

void
TriggerEfficiency::addBranches(TTree& _skimTree)
{
  _skimTree.Branch("weight_" + name_, &weight_, "weight_" + name_ + "/D");
  if (upFormula_)
    _skimTree.Branch("reweight_trigUp", &reweightUp_, "reweight_trigUp/D");
  if (downFormula_)
    _skimTree.Branch("reweight_trigDown", &reweightDown_, "reweight_trigDown/D");
}

void
TriggerEfficiency::apply(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  if (!formula_ || _outEvent.photons.size() == 0)
    return;

  double pt(_outEvent.photons[0].scRawPt);
  if (pt < minPt_)
    return;

  _outEvent.weight *= formula_->Eval(pt);
  if (upFormula_)
    reweightUp_ = upFormula_->Eval(pt);
  if (downFormula_)
    reweightDown_ = downFormula_->Eval(pt);
}

//--------------------------------------------------------------------
// ExtraPhotons
//--------------------------------------------------------------------

void
ExtraPhotons::apply(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  panda::ParticleCollection* cols[] = {
    &_outEvent.photons,
    &_outEvent.electrons,
    &_outEvent.muons,
    &_outEvent.taus
    // &_outEvent.jets
  };

  for (unsigned iP(0); iP != _event.photons.size(); ++iP) {
    auto& photon(_event.photons[iP]);

    if (photon.isEB)
      continue;
    
    if (photon.scRawPt < minPt_)
      continue;

    bool overlap(false);
    for (auto* col : cols) {
      unsigned iP(0);
      for (; iP != col->size(); ++iP) {
        if ((*col)[iP].dR2(photon) < 0.25)
          break;
      }
      if (iP != col->size()) {
        // there was a matching candidate
        overlap = true;
        break;
      }
    }
    if (overlap)
      continue;

    _outEvent.photons.push_back(photon);
  }
}

//--------------------------------------------------------------------
// JetCleaning
//--------------------------------------------------------------------

// Values from a talk linked from https://twiki.cern.ch/twiki/bin/view/CMS/PileupJetID
// under Information for 13TeV data analysis in 80X
// and Hgg AN 2017-036

/*static*/
double const JetCleaning::puidCuts[4][4][4] = {
  {
    {-0.97, -0.68, -0.53, -0.47},
    {-0.97, -0.68, -0.53, -0.47},
    {-0.89, -0.52, -0.38, -0.3},
    {-0.56, -0.17, -0.04, -0.01}
  },
  {
    {0.18, -0.55, -0.42, -0.36},
    {0.18, -0.55, -0.42, -0.36},
    {0.61, -0.35, -0.23, -0.17},
    {0.87, 0.03, 0.13, 0.12}
  },
  {
    {0.69, -0.35, -0.26, -0.21},
    {0.69, -0.35, -0.26, -0.21},
    {0.86, -0.1, -0.05, -0.01},
    {0.95, 0.28, 0.31, 0.28}
  },
  {
    {-0.8, -0.95, -0.97, -0.99},
    {-0.8, -0.95, -0.97, -0.99},
    {-0.8, -0.95, -0.97, -0.99},
    {-0.8, -0.95, -0.97, -0.99}
  }
};

/*static*/
bool
JetCleaning::passPUID(int _wp, panda::Jet const& _jet)
{
  int ptBin(0);
  if (_jet.pt() < 20.)
    ptBin = 0;
  else if (_jet.pt() < 30.)
    ptBin = 1;
  else if (_jet.pt() < 50.)
    ptBin = 2;
  else
    ptBin = 3;

  double absEta(std::abs(_jet.eta()));

  int etaBin(0);
  if (absEta < 2.5)
    etaBin = 0;
  else if (absEta < 2.75)
    etaBin = 1;
  else if (absEta < 3.)
    etaBin = 2;
  else
    etaBin = 3;

  return _jet.puid > puidCuts[_wp][ptBin][etaBin];
}

JetCleaning::JetCleaning(char const* _name/* = "JetCleaning"*/) :
  MonophotonModifier(_name)
{
  cleanAgainst_.set();
}

void
JetCleaning::initialize(panda::EventMonophoton&)
{
  if (printLevel_ > 0 && printLevel_ <= INFO) {
    *stream_ << "Jet cleaning " << name_ << " removes overlaps with ";
    if (cleanAgainst_[cPhotons])
      *stream_ << "photons ";
    if (cleanAgainst_[cElectrons])
      *stream_ << "electrons ";
    if (cleanAgainst_[cMuons])
      *stream_ << "muons ";
    if (cleanAgainst_[cTaus])
      *stream_ << "taus ";
    if (cleanAgainst_.none())
      *stream_ << "NONE";
    *stream_ << std::endl;
  }
}

void
JetCleaning::addBranches(TTree& _skimTree)
{
  // _skimTree.Branch("jets.ptResScaled", ptScaled_, "ptResScaled[jets.size]/F");
  // _skimTree.Branch("jets.ptResScaledUp", ptScaledUp_, "ptResScaledUp[jets.size]/F");
  // _skimTree.Branch("jets.ptResScaledDown", ptScaledDown_, "ptResScaledDown[jets.size]/F");
}

// void
// JetCleaning::setJetResolution(char const* _jerSource)
// {
//   jer_ = new JER(_jerSource);
//   rndm_ = new TRandom3(1234);
// }

void
JetCleaning::apply(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  panda::ParticleCollection* cols[] = {
    &_outEvent.photons,
    &_outEvent.electrons,
    &_outEvent.muons,
    &_outEvent.taus
  };

  //  auto& genJets(_event.genJets);

  for (unsigned iJ(0); iJ != _event.jets.size(); ++iJ) {
    auto& jet(_event.jets[iJ]);

    if (printLevel_ > 0 && printLevel_ <= DEBUG)
      *stream_ << "jet " << iJ << std::endl;

    if (!jet.loose)
      continue;

    if (useTightWP_ && !jet.tight)
      continue;

    double absEta(std::abs(jet.eta()));

    if (jet.pt() < minPt_ || absEta > 5.)
      continue;

    if (printLevel_ > 0 && printLevel_ <= DEBUG)
      *stream_ << " pass pt and eta cut" << std::endl;

    if (!passPUID(puidWP_, jet))
      continue;

    // No JEC info stored in nero right now (at least samples I am using)
    // double maxPt(jet.ptCorrUp);
    double maxPt(jet.pt());

    // if (jer_) {
    //   double res(jer_->resolution(jet.pt, jet.eta(), _event.rho));
    //   double sf, dsf;
    //   jer_->scalefactor(jet.eta(), sf, dsf);

    //   unsigned iG(0);
    //   for (; iG != genJets.size(); ++iG) {
    //     // matching definition from JetResolution twiki
    //     if (genJets[iG].dR2(jet) < 0.04 && std::abs(genJets[iG].pt - jet.pt) < 3. * res)
    //       break;
    //   }

    //   unsigned iOJ(_outEvent.jets.size());

    //   if (iG != genJets.size()) {
    //     auto& genJet(genJets[iG]);
    //     double dpt(jet.pt - genJet.pt);

    //     ptScaled_[iOJ] = std::max(0., genJet.pt + dpt * sf);
    //     ptScaledUp_[iOJ] = std::max(0., genJet.pt + dpt * (sf + dsf));
    //     ptScaledDown_[iOJ] = std::max(0., genJet.pt + dpt * (sf - dsf));
    //   }
    //   else {
    //     ptScaled_[iOJ] = std::max(0., rndm_->Gaus(jet.pt, std::sqrt(sf * sf - 1.) * res));
    //     ptScaledUp_[iOJ] = std::max(0., rndm_->Gaus(jet.pt, std::sqrt((sf + dsf) * (sf + dsf) - 1.) * res));
    //     ptScaledDown_[iOJ] = std::max(0., rndm_->Gaus(jet.pt, std::sqrt((sf - dsf) * (sf - dsf) - 1.) * res));
    //   }

    //   if (ptScaled_[iOJ] > maxPt)
    //     maxPt = ptScaled_[iOJ];
    //   if (ptScaledUp_[iOJ] > maxPt)
    //     maxPt = ptScaledUp_[iOJ];
    //   if (ptScaledDown_[iOJ] > maxPt)
    //     maxPt = ptScaledDown_[iOJ];
    // }

    if (maxPt < minPt_)
      continue;

    if (printLevel_ > 0 && printLevel_ <= DEBUG)
      *stream_ << " pass pt selection" << std::endl;
   
    unsigned iC(0);
    for (; iC != nCollections; ++iC) {
      if (!cleanAgainst_[iC])
        continue;

      auto& col(*cols[iC]);

      unsigned nP(col.size());
      if (iC == cPhotons && nP > 1)
        nP = 1;

      unsigned iP(0);
      for (; iP != nP; ++iP) {
        if (jet.dR2(col[iP]) < 0.16)
          break;
      }
      if (iP != nP)
        break;
    }
    if (iC != nCollections)
      continue;

    if (printLevel_ > 0 && printLevel_ <= DEBUG)
      *stream_ << " pass cleaning" << std::endl;

    _outEvent.jets.push_back(jet);

    if (printLevel_ > 0 && printLevel_ <= DEBUG)
      *stream_ << " added" << std::endl;
  }
}

//--------------------------------------------------------------------
// PhotonJetDPhi
//--------------------------------------------------------------------

void
PhotonJetDPhi::addBranches(TTree& _skimTree)
{
  _skimTree.Branch("photons.minJetDPhi", minDPhi_, "minJetDPhi[photons.size]/F");
  _skimTree.Branch("photons.minJetDPhiJECUp", minDPhiJECUp_, "minJetDPhiJECUp[photons.size]/F");
  _skimTree.Branch("photons.minJetDPhiJECDown", minDPhiJECDown_, "minJetDPhiJECDown[photons.size]/F");
  _skimTree.Branch("jets.photonDPhi", dPhi_, "photonDPhi[jets.size]/F");
}

void
PhotonJetDPhi::apply(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  unsigned nJ(0);
  unsigned nJCorrUp(0);
  unsigned nJCorrDown(0);

  for (unsigned iP(0); iP != _outEvent.photons.size(); ++iP) {
    auto& photon(_outEvent.photons[iP]);
    
    if ( !(photon.isEB) )
      continue;

    minDPhi_[iP] = 4.;
    minDPhiJECUp_[iP] = 4.;
    minDPhiJECDown_[iP] = 4.;
    
    for (unsigned iJ(0); iJ != _outEvent.jets.size(); ++iJ) {
      auto& jet(_outEvent.jets[iJ]);

      double dPhi(std::abs(TVector2::Phi_mpi_pi(jet.phi() - photon.phi())));

      if (iP == 0)
	dPhi_[iJ] = dPhi;
      
      if (jet.pt() > 30. && nJ < 4) {
	++nJ;
	
	if (dPhi < minDPhi_[iP])
	  minDPhi_[iP] = dPhi;
      }

      if (metVar_) {
	if (jet.ptCorrUp > 30. && nJCorrUp < 4) {
	  ++nJCorrUp;
	  if (dPhi < minDPhiJECUp_[iP])
	    minDPhiJECUp_[iP] = dPhi;
	}

	if (jet.ptCorrDown > 30. && nJCorrDown < 4) {
	  ++nJCorrDown;
	  if (dPhi < minDPhiJECDown_[iP])
	    minDPhiJECDown_[iP] = dPhi;
	}
      }
    }
  }
}

//--------------------------------------------------------------------
// CopyMet
//--------------------------------------------------------------------

void
CopyMet::apply(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  // if (useGSFix_) {
  _outEvent.t1Met = _event.t1Met;
  /*
    }
  else {
    _outEvent.t1Met = _event.metMuOnlyFix;
  }
  */
}
//--------------------------------------------------------------------
// CopySuperClusters
//--------------------------------------------------------------------

void
CopySuperClusters::apply(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  // collect the ids of the input superclusters from output collections
  std::map<unsigned, unsigned> referenced;

  for (auto& photon : _outEvent.photons) {
    if (photon.superCluster.idx() != -1)
      referenced.emplace(unsigned(photon.superCluster.idx()), unsigned(-1));
  }

  for (auto& electron : _outEvent.electrons) {
    if (electron.superCluster.idx() != -1)
      referenced.emplace(unsigned(electron.superCluster.idx()), unsigned(-1));
  }

  for (auto& p : referenced) {
    p.second = _outEvent.superClusters.size();
    _outEvent.superClusters.push_back(_event.superClusters[p.first]);
  }

  for (auto& photon : _outEvent.photons) {
    if (photon.superCluster.idx() != -1)
      photon.superCluster.idx() = referenced[photon.superCluster.idx()];
  }

  for (auto& electron : _outEvent.electrons) {
    if (electron.superCluster.idx() != -1)
      electron.superCluster.idx() = referenced[electron.superCluster.idx()];
  }
}

//--------------------------------------------------------------------
// AddTrailingPhotons
//--------------------------------------------------------------------

void
AddTrailingPhotons::apply(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  // truncate the output to 1
  _outEvent.photons.resize(1);

  for (auto& ph : _event.photons) {
    if (ph.dR2(_outEvent.photons[0]) < 0.01)
      continue;

    if (ph.loose && ph.csafeVeto)
      _outEvent.photons.push_back(ph);
  }
}

//--------------------------------------------------------------------
// AddGenJets
//--------------------------------------------------------------------

void
AddGenJets::addInputBranch(panda::utils::BranchList& _blist)
{
  _blist += {"ak4GenJets"};
}

void
AddGenJets::apply(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  _outEvent.genJets.clear();
  
  for (auto& jet : _event.genJets) {
    if (jet.pt() > minPt_ && std::abs(jet.eta()) < maxEta_)
      _outEvent.genJets.push_back(jet);
  }
}

//--------------------------------------------------------------------
// PhotonMt
//--------------------------------------------------------------------

void
PhotonMt::addBranches(TTree& _skimTree)
{
  _skimTree.Branch("photons.mt", mt_, "mt[photons.size]/F");
}

void
PhotonMt::apply(panda::EventMonophoton const&, panda::EventMonophoton& _outEvent)
{
  auto& met(_outEvent.t1Met);
  for (unsigned iP(0); iP != _outEvent.photons.size(); ++iP) {
    auto& photon(_outEvent.photons[iP]);
    mt_[iP] = std::sqrt(2. * met.pt * photon.scRawPt * (1. - std::cos(met.phi - photon.phi())));
  }
}

//--------------------------------------------------------------------
// LeptonRecoil
//--------------------------------------------------------------------

void
LeptonRecoil::addBranches(TTree& _skimTree)
{
  _skimTree.Branch("t1Met.realMet", &realMet_, "realMet/F");
  _skimTree.Branch("t1Met.realPhi", &realPhi_, "realPhi/F");
}

void
LeptonRecoil::apply(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  panda::LeptonCollection* col(0);

  switch (flavor_) {
  case lElectron:
    col = &_outEvent.electrons;
    break;
  case lMuon:
    col = &_outEvent.muons;
    break;
  default:
    return;
  }

  float inMets[] = {
    _outEvent.t1Met.pt,
    _outEvent.t1Met.ptCorrUp,
    _outEvent.t1Met.ptCorrDown,
    _outEvent.t1Met.ptUnclUp,
    _outEvent.t1Met.ptUnclDown
  };
  float inPhis[] = {
    _outEvent.t1Met.phi,
    _outEvent.t1Met.phiCorrUp,
    _outEvent.t1Met.phiCorrDown,
    _outEvent.t1Met.phiUnclUp,
    _outEvent.t1Met.phiUnclDown
  };

  float* outRecoils[] = {
    &_outEvent.t1Met.pt,
    &_outEvent.t1Met.ptCorrUp,
    &_outEvent.t1Met.ptCorrDown,
    &_outEvent.t1Met.ptUnclUp,
    &_outEvent.t1Met.ptUnclDown
  };
  float* outRecoilPhis[] = {
    &_outEvent.t1Met.phi,
    &_outEvent.t1Met.phiCorrUp,
    &_outEvent.t1Met.phiCorrDown,
    &_outEvent.t1Met.phiUnclUp,
    &_outEvent.t1Met.phiUnclDown
  };

  float* realMets[] = {
    &realMet_,
    &realMetCorrUp_,
    &realMetCorrDown_,
    &realMetUnclUp_,
    &realMetUnclDown_
  };
  float* realPhis[] = {
    &realPhi_,
    &realPhiCorrUp_,
    &realPhiCorrDown_,
    &realPhiUnclUp_,
    &realPhiUnclDown_
  };

  for (unsigned iM(0); iM != sizeof(realMets) / sizeof(float*); ++iM) {
    *realMets[iM] = inMets[iM];
    *realPhis[iM] = inPhis[iM];
  }

  double lpx(0.);
  double lpy(0.);
    
  for (unsigned iL(0); iL != col->size(); ++iL) {
    auto& lep = col->at(iL);

    lpx += lep.pt() * std::cos(lep.phi());
    lpy += lep.pt() * std::sin(lep.phi());
  }

  for (unsigned iM(0); iM != sizeof(outRecoils) / sizeof(float*); ++iM) {
    double mex(lpx + inMets[iM] * std::cos(inPhis[iM]));
    double mey(lpy + inMets[iM] * std::sin(inPhis[iM]));
    *outRecoils[iM] = std::sqrt(mex * mex + mey * mey);
    *outRecoilPhis[iM] = std::atan2(mey, mex);
  }
  
}

TVector2
LeptonRecoil::realMetCorr(int corr) const
{
  if (corr == 0)
    return realMet();

  TVector2 vec;
  switch (corr) {
  case 1:
    vec.SetMagPhi(realMetCorrUp_, realPhiCorrUp_);
    break;
  case -1:
    vec.SetMagPhi(realMetCorrDown_, realPhiCorrDown_);
    break;
  };

  return vec;
}

TVector2
LeptonRecoil::realMetUncl(int corr) const
{
  if (corr == 0)
    return realMet();

  TVector2 vec;
  switch (corr) {
  case 1:
    vec.SetMagPhi(realMetUnclUp_, realPhiUnclUp_);
    break;
  case -1:
    vec.SetMagPhi(realMetUnclDown_, realPhiUnclDown_);
    break;
  };

  return vec;
}

//--------------------------------------------------------------------
// PhotonFakeMet
//--------------------------------------------------------------------

void
PhotonFakeMet::addBranches(TTree& _skimTree)
{
  _skimTree.Branch("photons.realScRawPt", &realPhoPt_, "realScRawPt[photons.size]/F");
  _skimTree.Branch("t1Met.realMet", &realMet_, "realMet/F");
  _skimTree.Branch("t1Met.realPhi", &realPhi_, "realPhi/F");
}

void
PhotonFakeMet::apply(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  float inMets[] = {
    _outEvent.t1Met.pt,
    _outEvent.t1Met.ptCorrUp,
    _outEvent.t1Met.ptCorrDown,
    _outEvent.t1Met.ptUnclUp,
    _outEvent.t1Met.ptUnclDown
  };
  float inPhis[] = {
    _outEvent.t1Met.phi,
    _outEvent.t1Met.phiCorrUp,
    _outEvent.t1Met.phiCorrDown,
    _outEvent.t1Met.phiUnclUp,
    _outEvent.t1Met.phiUnclDown
  };

  float* outRecoils[] = {
    &_outEvent.t1Met.pt,
    &_outEvent.t1Met.ptCorrUp,
    &_outEvent.t1Met.ptCorrDown,
    &_outEvent.t1Met.ptUnclUp,
    &_outEvent.t1Met.ptUnclDown
  };
  float* outRecoilPhis[] = {
    &_outEvent.t1Met.phi,
    &_outEvent.t1Met.phiCorrUp,
    &_outEvent.t1Met.phiCorrDown,
    &_outEvent.t1Met.phiUnclUp,
    &_outEvent.t1Met.phiUnclDown
  };

  float* realMets[] = {
    &realMet_,
    &realMetCorrUp_,
    &realMetCorrDown_,
    &realMetUnclUp_,
    &realMetUnclDown_
  };
  float* realPhis[] = {
    &realPhi_,
    &realPhiCorrUp_,
    &realPhiCorrDown_,
    &realPhiUnclUp_,
    &realPhiUnclDown_
  };

  for (unsigned iM(0); iM != sizeof(realMets) / sizeof(float*); ++iM) {
    *realMets[iM] = inMets[iM];
    *realPhis[iM] = inPhis[iM];
  }

  double px(0.);
  double py(0.);

  double fraction(0.);

  if (fraction_ < 0.)
    fraction = rand_.Uniform(0.25, 0.75);
  else
    fraction = fraction_;

  for (unsigned iP(0); iP != _outEvent.photons.size(); ++iP) {
    auto& pho = _outEvent.photons[iP];

    px += fraction * pho.scRawPt * std::cos(pho.phi());
    py += fraction * pho.scRawPt * std::sin(pho.phi());

    realPhoPt_[iP] = pho.scRawPt;
    _outEvent.photons[iP].scRawPt = (1. - fraction) * pho.scRawPt;
  }

  for (unsigned iM(0); iM != sizeof(outRecoils) / sizeof(float*); ++iM) {
    double mex(px + inMets[iM] * std::cos(inPhis[iM]));
    double mey(py + inMets[iM] * std::sin(inPhis[iM]));
    *outRecoils[iM] = std::sqrt(mex * mex + mey * mey);
    *outRecoilPhis[iM] = std::atan2(mey, mex);
  }
  
}

TVector2
PhotonFakeMet::realMetCorr(int corr) const
{
  if (corr == 0)
    return realMet();

  TVector2 vec;
  switch (corr) {
  case 1:
    vec.SetMagPhi(realMetCorrUp_, realPhiCorrUp_);
    break;
  case -1:
    vec.SetMagPhi(realMetCorrDown_, realPhiCorrDown_);
    break;
  };

  return vec;
}

TVector2
PhotonFakeMet::realMetUncl(int corr) const
{
  if (corr == 0)
    return realMet();

  TVector2 vec;
  switch (corr) {
  case 1:
    vec.SetMagPhi(realMetUnclUp_, realPhiUnclUp_);
    break;
  case -1:
    vec.SetMagPhi(realMetUnclDown_, realPhiUnclDown_);
    break;
  };

  return vec;
}

//--------------------------------------------------------------------
// MetVariations
//--------------------------------------------------------------------

void
MetVariations::addBranches(TTree& _skimTree)
{
  if (photonSel_) {
    if (metSource_ == kInMet) {
      _skimTree.Branch("t1Met.realMetGECUp", &metGECUp_, "realMetGECUp/F");
      _skimTree.Branch("t1Met.realPhiGECUp", &phiGECUp_, "realPhiGECUp/F");
      _skimTree.Branch("t1Met.realMetGECDown", &metGECDown_, "realMetGECDown/F");
      _skimTree.Branch("t1Met.realPhiGECDown", &phiGECDown_, "realPhiGECDown/F");
    }
    else {
      _skimTree.Branch("t1Met.ptGECUp", &metGECUp_, "metGECUp/F");
      _skimTree.Branch("t1Met.phiGECUp", &phiGECUp_, "phiGECUp/F");
      _skimTree.Branch("t1Met.ptGECDown", &metGECDown_, "metGECDown/F");
      _skimTree.Branch("t1Met.phiGECDown", &phiGECDown_, "phiGECDown/F");
    }
  }
  // if (jetCleaning_) {
  //   _skimTree.Branch("t1Met.ptJER", &metJER_, "metJER/F");
  //   _skimTree.Branch("t1Met.phiJER", &phiJER_, "phiJER/F");
  //   _skimTree.Branch("t1Met.ptJERUp", &metJERUp_, "metJERUp/F");
  //   _skimTree.Branch("t1Met.phiJERUp", &phiJERUp_, "phiJERUp/F");
  //   _skimTree.Branch("t1Met.ptJERDown", &metJERDown_, "metJERDown/F");
  //   _skimTree.Branch("t1Met.phiJERDown", &phiJERDown_, "phiJERDown/F");
  // }
}

void
MetVariations::apply(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  metGECUp_ = 0.;
  phiGECUp_ = 0.;
  metGECDown_ = 0.;
  phiGECDown_ = 0.;
  // metJER_ = 0.;
  // phiJER_ = 0.;
  // metJERUp_ = 0.;
  // phiJERUp_ = 0.;
  // metJERDown_ = 0.;
  // phiJERDown_ = 0.;

  if (_outEvent.photons.size() == 0)
    return;

  TVector2 metV;
  if (metSource_ == kInMet)
    metV = _event.t1Met.v();
  else
    metV = _outEvent.t1Met.v();

  if (photonSel_) {
    auto& photon(_outEvent.photons[0]);

    TVector2 nominal;
    nominal.SetMagPhi(photon.scRawPt, photon.phi());

    TVector2 photonUp;
    photonUp.SetMagPhi(photonSel_->ptVariation(photon, 1.), photon.phi());

    TVector2 photonDown;
    photonDown.SetMagPhi(photonSel_->ptVariation(photon, -1.), photon.phi());

    TVector2 shiftUp(metV + nominal - photonUp);
    TVector2 shiftDown(metV + nominal - photonDown);

    metGECUp_ = shiftUp.Mod();
    phiGECUp_ = TVector2::Phi_mpi_pi(shiftUp.Phi());
    metGECDown_ = shiftDown.Mod();
    phiGECDown_ = TVector2::Phi_mpi_pi(shiftDown.Phi());
  }

  // if (jetCleaning_) {
  //   TVector2 shiftCentral(metV);
  //   TVector2 shiftUp(metV);
  //   TVector2 shiftDown(metV);

  //   for (unsigned iJ(0); iJ != _outEvent.jets.size(); ++iJ) {
  //     auto& jet(_outEvent.jets[iJ]);

  //     TVector2 nominal;
  //     nominal.SetMagPhi(jet.pt, jet.phi());

  //     if (jetCleaning_->ptScaled(iJ) > 15.) {
  //       TVector2 resShift;
  //       resShift.SetMagPhi(jetCleaning_->ptScaled(iJ), jet.phi());
  //       shiftCentral += nominal - resShift;
  //     }

  //     if (jetCleaning_->ptScaledUp(iJ) > 15.) {
  //       TVector2 resShift;
  //       resShift.SetMagPhi(jetCleaning_->ptScaledUp(iJ), jet.phi());
  //       shiftUp += nominal - resShift;
  //     }

  //     if (jetCleaning_->ptScaledDown(iJ) > 15.) {
  //       TVector2 resShift;
  //       resShift.SetMagPhi(jetCleaning_->ptScaledDown(iJ), jet.phi());
  //       shiftDown += nominal - resShift;
  //     }
  //   }

  //   metJER_ = shiftCentral.Mod();
  //   phiJER_ = TVector2::Phi_mpi_pi(shiftCentral.Phi());
  //   metJERUp_ = shiftUp.Mod();
  //   phiJERUp_ = TVector2::Phi_mpi_pi(shiftUp.Phi());
  //   metJERDown_ = shiftDown.Mod();
  //   phiJERDown_ = TVector2::Phi_mpi_pi(shiftDown.Phi());
  // }
}

//--------------------------------------------------------------------
// ConstantWeight
//--------------------------------------------------------------------

void
ConstantWeight::addBranches(TTree& _skimTree)
{
  _skimTree.Branch("weight_" + name_, &weight_, "weight_" + name_ + "/D");
  if (weightUp_ >= 0.)
    _skimTree.Branch("reweight_" + name_ + "Up", &weightUp_, "reweight_" + name_ + "Up/D");
  if (weightDown_ >= 0.)
    _skimTree.Branch("reweight_" + name_ + "Down", &weightDown_, "reweight_" + name_ + "Down/D");
}

//--------------------------------------------------------------------
// PtWeight
//--------------------------------------------------------------------

PhotonPtWeight::PhotonPtWeight(TObject* _factors, char const* _name/* = "PhotonPtWeight"*/) :
  MonophotonModifier(_name),
  nominal_(0)
{
  nominal_ = _factors->Clone(name_ + "_" + _factors->GetName());
  if (nominal_->InheritsFrom(TH1::Class()))
    static_cast<TH1*>(nominal_)->SetDirectory(0);
}

PhotonPtWeight::~PhotonPtWeight()
{
  for (auto& var : variations_)
    delete var.second;

  for (auto& var : varWeights_)
    delete var.second;
}

void
PhotonPtWeight::addBranches(TTree& _skimTree)
{
  _skimTree.Branch("weight_" + name_, &weight_, "weight_" + name_ + "/D");
  for (auto& var : varWeights_)
    _skimTree.Branch("reweight_" + var.first, var.second, "reweight_" + var.first + "/D");
}

void
PhotonPtWeight::addVariation(char const* _tag, TObject* _corr)
{
  if (variations_.count(_tag) != 0) {
    delete variations_[_tag];
    delete varWeights_[_tag];
  }

  auto* clone(_corr->Clone(name_ + "_" + _corr->GetName()));
  if (clone->InheritsFrom(TH1::Class()))
    static_cast<TH1*>(clone)->SetDirectory(0);
  variations_[_tag] = clone;
  varWeights_[_tag] = new double;
}

void
PhotonPtWeight::useErrors(bool _b)
{
  usingErrors_ = true;

  TString tag(name_ + "Up");
  if (varWeights_.count(tag) != 0) {
    delete varWeights_[tag];
    varWeights_.erase(tag);
  }
  tag = name_ + "Down";
  if (varWeights_.count(tag) != 0) {
    delete varWeights_[tag];
    varWeights_.erase(tag);
  }

  if (_b) {
    varWeights_[name_ + "Up"] = new double;
    varWeights_[name_ + "Down"] = new double;
  }
}

void
PhotonPtWeight::computeWeight(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  weight_ = 1.;
  for (auto& var : varWeights_)
    *var.second = 1.;

  double maxPt(0.);
  switch (photonType_) {
  case kReco:
    for (unsigned iP(0); iP != _outEvent.photons.size(); ++iP) {
      auto& photon( _outEvent.photons[iP]);

      if (photon.scRawPt > maxPt)
        maxPt = photon.scRawPt;
    }
    break;
  case kParton:
    for (unsigned iP(0); iP != _event.partons.size(); ++iP) {
      auto& part( _event.partons[iP]);
      
      if (part.pdgid == 22 && part.pt() > maxPt)
        maxPt = part.pt();
    }
    break;
  case kPostShower:
    for (unsigned iP(0); iP != _event.genParticles.size(); ++iP) {
      auto& fs( _event.genParticles[iP]);
      // probably need to add a check if it's prompt final state
      /*
	if (part.statusFlags != "someCondition")
	continue;
      */
      
      if (fs.pdgid == 22 && fs.pt() > maxPt)
        maxPt = fs.pt();
    }
    break;
  default:
    return;
  }

  double weight(calcWeight_(nominal_, maxPt));
  weight_ = weight;

  for (auto& var : varWeights_) {
    if (usingErrors_) {
      if (var.first == name_ + "Up")
        *var.second = calcWeight_(nominal_, maxPt, 1) / weight;
      else if (var.first == name_ + "Down")
        *var.second = calcWeight_(nominal_, maxPt, -1) / weight;
    }
    else // other variations
      *var.second = calcWeight_(variations_[var.first], maxPt) / weight;
  }
}

void
PhotonPtWeight::apply(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  computeWeight(_event, _outEvent);
  _outEvent.weight *= weight_;
}

double
PhotonPtWeight::calcWeight_(TObject* source, double pt, int var/* = 0*/)
{
  if (source->InheritsFrom(TH1::Class())) {
    TH1* hist(static_cast<TH1*>(source));

    int iX(hist->FindFixBin(pt));
    if (iX == 0)
      iX = 1;
    if (iX > hist->GetNbinsX())
      iX = hist->GetNbinsX();

    if (var == 0)
      return hist->GetBinContent(iX);
    else if (var == 1)
      return hist->GetBinContent(iX) + hist->GetBinError(iX);
    else
      return hist->GetBinContent(iX) - hist->GetBinError(iX);
  }
  else if (source->InheritsFrom(TF1::Class())) {
    TF1* func(static_cast<TF1*>(source));

    if (pt < func->GetXmin())
      pt = func->GetXmin();
    if (pt > func->GetXmax())
      pt = func->GetXmax();

    return func->Eval(pt);
  }
  else if (source->InheritsFrom(TGraph::Class())) {
    TGraph* graph(static_cast<TGraph*>(source));

    if (pt < graph->GetX()[0])
      pt = graph->GetX()[0];
    if (pt > graph->GetX()[graph->GetN() - 1])
      pt = graph->GetX()[graph->GetN() - 1];

    return graph->Eval(pt);
  }
  else
    return 0.;
}

//--------------------------------------------------------------------
// PhotonPtWeightSigned
//--------------------------------------------------------------------

PhotonPtWeightSigned::PhotonPtWeightSigned(TObject* _pfactors, TObject* _nfactors, char const* name/* = "PhotonPtWeightSigned"*/) :
  MonophotonModifier(name)
{
  operators_[kPositive] = new PhotonPtWeight(_pfactors, name_ + "_positive");
  operators_[kNegative] = new PhotonPtWeight(_nfactors, name_ + "_negative");
}

PhotonPtWeightSigned::~PhotonPtWeightSigned()
{
  for (auto& v : varWeights_)
    delete v.second;

  delete operators_[kPositive];
  delete operators_[kNegative];
}

void
PhotonPtWeightSigned::addBranches(TTree& _skimTree)
{
  _skimTree.Branch("weight_" + name_, &weight_, "weight_" + name_ + "/D");
  for (auto& var : varWeights_)
    _skimTree.Branch("reweight_" + var.first, var.second, "reweight_" + var.first + "/D");
}

void
PhotonPtWeightSigned::addVariation(char const* _tag, TObject* _pcorr, TObject* _ncorr)
{
  if (varWeights_.count(_tag) != 0)
    delete varWeights_[_tag];

  operators_[kPositive]->addVariation(_tag, _pcorr);
  operators_[kNegative]->addVariation(_tag, _ncorr);
  if (varWeights_.count(_tag) == 0)
    varWeights_[_tag] = new double;
}

void
PhotonPtWeightSigned::setPhotonType(unsigned _t)
{
  for (auto* op : operators_)
    op->setPhotonType(_t);
}

void
PhotonPtWeightSigned::useErrors(bool _b)
{
  TString tag(name_ + "Up");
  if (varWeights_.count(tag) != 0) {
    delete varWeights_[tag];
    varWeights_.erase(tag);
  }
  tag = name_ + "Down";
  if (varWeights_.count(tag) != 0) {
    delete varWeights_[tag];
    varWeights_.erase(tag);
  }

  if (_b) {
    varWeights_[name_ + "Up"] = new double;
    varWeights_[name_ + "Down"] = new double;
  }

  for (auto* op : operators_)
    op->useErrors(_b);
}

void
PhotonPtWeightSigned::apply(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  weight_ = 1.;
  for (auto& var : varWeights_)
    *var.second = 1.;

  PhotonPtWeight* op(0);
  for (auto& part : _event.partons) {
    if (part.pdgid == 11 || part.pdgid == 13 || part.pdgid == 15)
      op = operators_[kNegative];
    else if (part.pdgid == -11 || part.pdgid == -13 || part.pdgid == -15)
      op = operators_[kPositive];
  }
  if (!op)
    return;

  op->computeWeight(_event, _outEvent);

  weight_ = op->getWeight();
  _outEvent.weight *= weight_;

  for (auto& var : varWeights_)
    *var.second = op->getVariation(var.first);
}

//--------------------------------------------------------------------
// DEtajjWeight
//--------------------------------------------------------------------

DEtajjWeight::DEtajjWeight(TF1* _formula, char const* name/* = "DEtajjWeight"*/) :
  Modifier(name),
  formula_(_formula)
{}

void
DEtajjWeight::addBranches(TTree& _skimTree)
{
  _skimTree.Branch("weight_" + name_, &weight_, "weight_" + name_ + "/D");
}

void
DEtajjWeight::apply(panda::EventMonophoton const& _event, panda::EventBase&)
{
  if (dijet_->getNDijetPassing() == 0) {
    weight_ = 1.;
    return;
  }

  weight_ = formula_->Eval(dijet_->getDEtajjPassing(0));
}

//--------------------------------------------------------------------
// IDSFWeight
//--------------------------------------------------------------------

void
IDSFWeight::addBranches(TTree& _skimTree)
{
  _skimTree.Branch("weight_" + name_, &weight_, "weight_" + name_ + "/D");
  _skimTree.Branch("reweight_" + name_ + "Up", &weightUp_, "reweight_" + name_ + "Up/D");
  _skimTree.Branch("reweight_" + name_ + "Down", &weightDown_, "reweight_" + name_ + "Down/D");
}

void
IDSFWeight::setVariable(Variable vx, Variable vy)
{
  variables_[0] = vx;
  variables_[1] = vy;
}

void
IDSFWeight::applyParticle(unsigned iP, panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  // simply consider the leading object. Ignores inefficiency scales etc.
  panda::Particle const* part(0);

  switch (object_) {
  case cPhotons:
    if (_outEvent.photons.size() > iP)
      part = &_outEvent.photons.at(iP);
    break;
  case cElectrons:
    if (_outEvent.electrons.size() > iP)
      part = &_outEvent.electrons.at(iP);
    break;
  case cMuons:
    if (_outEvent.muons.size() > iP)
      part = &_outEvent.muons.at(iP);
    break;
  case nCollections:
    if (customCollection_ && customCollection_->size() > iP) {
      part = &customCollection_->at(iP);
    }
    else
      return;
    break;
  default:
    return;
  };

  if (!part)
    return;

  int iCell(0);

  TAxis* axis(0);
  int rowSize(1);
  for (unsigned iV(0); iV != 2; ++iV) {
    if (variables_[iV] == nVariables)
      break;

    switch (iV) {
    case 0:
      axis = factors_[iP]->GetXaxis();
      break;
    case 1:
      axis = factors_[iP]->GetYaxis();
      break;
    };

    int iBin(0);
    switch (variables_[iV]) {
    case kPt:
      switch (object_) {
      case cPhotons:
	{
	  panda::XPhoton const* photon = &_outEvent.photons.at(iP);
	  iBin = axis->FindFixBin(photon->scRawPt);
	  break;
	}
      default:
	iBin = axis->FindFixBin(part->pt());
      }
      break;
    case kEta:
      iBin = axis->FindFixBin(part->eta());
      break;
    case kAbsEta:
      iBin = axis->FindFixBin(std::abs(part->eta()));
      break;
    case kNpv:
      iBin = axis->FindFixBin(_event.npvTrue);
      if (iBin == 0)
	iBin = 1;
      if (iBin > axis->GetNbins())
	iBin = axis->GetNbins();
    default:
      break;
    }

    if (iBin == 0)
      iBin = 1;
    if (iBin > axis->GetNbins())
      iBin = axis->GetNbins();

    iCell += iBin * rowSize;

    rowSize *= axis->GetNbins() + 2;
  }

  double weight(factors_[iP]->GetBinContent(iCell));
  double error(factors_[iP]->GetBinError(iCell));

  weight_ *= weight;
  _outEvent.weight *= weight;

  double relerror = error / weight;

  if (printLevel_ > 0 && printLevel_ <= DEBUG && relerror > 0.5)  {
    *stream_ << "relerror " << relerror << ", weight " << weight << ", error " << error << std::endl;
    *stream_ << "hist: " << factors_[iP]->GetDirectory()->GetName() << ", bin " << iCell << std::endl;
  }

  weightUp_ += relerror;
  weightDown_ -= relerror;
}

void
IDSFWeight::apply(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  // not exactly sure why I need to reset these, but it's definitely necessary to get reasonable results
  weight_ = 1.;
  weightUp_ = 1.;
  weightDown_ = 1.;
    
  for (unsigned iP(0); iP != nParticles_; iP++) {
    applyParticle(iP, _event, _outEvent);
  }
}

//--------------------------------------------------------------------
// NPVWeight
//--------------------------------------------------------------------

void
NPVWeight::apply(panda::EventMonophoton const& _event, panda::EventBase& _outEvent)
{
  int iX(factors_->FindFixBin(_event.npv));
  if (iX == 0)
    iX = 1;
  if (iX > factors_->GetNbinsX())
    iX = factors_->GetNbinsX();

  _outEvent.weight *= factors_->GetBinContent(iX);
}

//--------------------------------------------------------------------
// VtxAdjustedJetProxyWeight
//--------------------------------------------------------------------

VtxAdjustedJetProxyWeight::VtxAdjustedJetProxyWeight(TH1* isoTFactor, TH2* isoVScore, TH1* noIsoTFactor, TH2* noIsoVScore, char const* name/* = "VtxAdjustedJetProxyWeight"*/) :
  PhotonPtWeight(isoTFactor, name),
  isoVScore_(isoVScore),
  noIsoTFactor_(noIsoTFactor),
  noIsoVScore_(noIsoVScore)
{
}

void
VtxAdjustedJetProxyWeight::setRCProb(TH2* distribution, double chIsoCut)
{
  delete rcProb_;

  rcProb_ = new TH1D("rcprob", "", distribution->GetNbinsX(), distribution->GetXaxis()->GetXmin(), distribution->GetXaxis()->GetXmax());

  int iYMax(distribution->GetYaxis()->FindBin(chIsoCut));

  for (int iX(1); iX <= distribution->GetNbinsX(); ++iX) {
    double p(0.);
    for (int iY(1); iY <= iYMax; ++iY)
      p += distribution->GetBinContent(iX, iY);

    rcProb_->SetBinContent(iX, p);
  }
}

void
VtxAdjustedJetProxyWeight::addBranches(TTree& _skimTree)
{
  _skimTree.Branch("isoTFactor", &weight_, "isoTFactor/F");
  _skimTree.Branch("isoPVProb", &isoPVProb_, "isoPVProb/F");
  _skimTree.Branch("noIsoTFactor", &noIsoT_, "noIsoTFactor/F");
  _skimTree.Branch("noIsoPVProb", &noIsoPVProb_, "noIsoPVProb/F");
  _skimTree.Branch("randomcone", &rc_, "randomcone/F");
  
  for (auto& var : varWeights_)
    _skimTree.Branch("reweight_" + var.first, var.second, "reweight_" + var.first + "/D");
}

void
VtxAdjustedJetProxyWeight::apply(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  if (_outEvent.photons.empty())
    return;

  double pt(_outEvent.photons[0].scRawPt);
  double eta(_outEvent.photons[0].eta());

  weight_ = calcWeight_(nominal_, pt);
  noIsoT_ = calcWeight_(noIsoTFactor_, pt);

  if (_event.vertices.size() <= 1) {
    isoPVProb_ = 1.;
    noIsoPVProb_ = 1.;
  }
  else {
    int iYMin(isoVScore_->GetYaxis()->FindBin(std::log(_event.vertices[1].score)));
      
    int iX(isoVScore_->GetXaxis()->FindBin(pt));
    if (iX == 0)
      iX = 1;
    else if (iX == isoVScore_->GetNbinsX() + 1)
      iX = isoVScore_->GetNbinsX();
    
    isoPVProb_ = 0.;
    for (int iY(iYMin); iY <= isoVScore_->GetNbinsY(); ++iY)
      isoPVProb_ += isoVScore_->GetBinContent(iX, iY);

    iX = noIsoVScore_->GetXaxis()->FindBin(pt);
    if (iX == 0)
      iX = 1;
    else if (iX == noIsoVScore_->GetNbinsX() + 1)
      iX = noIsoVScore_->GetNbinsX();
    
    noIsoPVProb_ = 0.;
    for (int iY(iYMin); iY <= noIsoVScore_->GetNbinsY(); ++iY)
      noIsoPVProb_ += noIsoVScore_->GetBinContent(iX, iY);
  }

  rc_ = 0.;
  if (rcProb_)
    rc_ = calcWeight_(rcProb_, eta);

  double t(isoPVProb_ * weight_ + (1. - noIsoPVProb_) * noIsoT_ * rc_);

  _outEvent.weight *= t;

  for (auto& var : varWeights_) {
    double isoT(0.);
    if (var.first == name_ + "Up")
      isoT = calcWeight_(nominal_, pt, 1);
    else if (var.first == name_ + "Down")
      isoT = calcWeight_(nominal_, pt, -1);
    else
      isoT = calcWeight_(variations_[var.first], pt);

    *var.second = (isoPVProb_ * isoT + (1. - noIsoPVProb_) * noIsoT_ * rc_) / t;
  }
}

//--------------------------------------------------------------------
// NNPDFVariation
//--------------------------------------------------------------------

void
NNPDFVariation::addBranches(TTree& _skimTree)
{
  _skimTree.Branch("reweight_pdfUp", &weightUp_, "reweight_pdfUp/D");
  _skimTree.Branch("reweight_pdfDown", &weightDown_, "reweight_pdfDown/D");
}

void
NNPDFVariation::apply(panda::EventMonophoton const& _event, panda::EventBase&)
{
  // need to implement new version of pdf weights
  weightUp_ = 1.; // + _event.genReweight.pdfDW * rescale_;
  weightDown_ = 1.; // - _event.genReweight.pdfDW * rescale_;
}

//--------------------------------------------------------------------
// GJetsDR
//--------------------------------------------------------------------

void
GJetsDR::addBranches(TTree& _skimTree)
{
  _skimTree.Branch("genPhotonDR", &minDR_, "genPhotonDR/F");
}

void
GJetsDR::apply(panda::EventMonophoton const& _event, panda::EventBase&)
{
  minDR_ = -1.;

  for (auto& photon : _event.partons) {
    if (std::abs(photon.pdgid) != 22)
      continue;

    for (auto& parton : _event.partons) {
      if (&parton == &photon)
        continue;

      unsigned absId(std::abs(parton.pdgid));
      if (!(absId == 21 || absId < 7))
        continue;

      double dR(photon.dR(parton));
      if (minDR_ < 0. || dR < minDR_)
        minDR_ = dR;
    }
  }
}

//--------------------------------------------------------------------
// JetClustering
//--------------------------------------------------------------------

void
JetClustering::addInputBranch(panda::utils::BranchList& _blist)
{
  _blist += {"pfCandidates"};
}

void
JetClustering::addBranches(TTree& _skimTree)
{
  if (!overwrite_)
    jets_.book(_skimTree, {"pt_", "eta_", "phi_", "mass_", "chf", "nhf", "constituents_"});
}

void
JetClustering::apply(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  auto& outJets(overwrite_ ? _outEvent.jets : jets_);

  outJets.data.constituentsContainer_ = &_event.pfCandidates;

  auto& inputs(_event.pfCandidates);

  std::vector<fastjet::PseudoJet> fjInputs;
  fjInputs.reserve(inputs.size());

  unsigned iI(-1);
  for (auto& input : inputs) {
    ++iI;
    if (input.pt() < 100. * std::numeric_limits<double>::epsilon())
      continue;

    auto p4(input.p4());
    fjInputs.emplace_back(p4.X(), p4.Y(), p4.Z(), p4.E());
    fjInputs.back().set_user_index(iI);
  }

  fastjet::ClusterSequence clusterSeq(fjInputs, jetDef_);

  auto&& fjJets(fastjet::sorted_by_pt(clusterSeq.inclusive_jets(minPt_)));

  outJets.init();
  for (auto& fjJet : fjJets) {
    auto& outJet(outJets.create_back());
    outJet.setXYZE(fjJet.px(), fjJet.py(), fjJet.pz(), fjJet.E());
    outJet.rawPt = outJet.pt();

    auto&& fjConsts(fastjet::sorted_by_pt(fjJet.constituents()));

    outJet.chf = 0.;
    outJet.nhf = 0.;

    for (auto& fjConst : fjConsts) {
      auto index(fjConst.user_index());
      if (index < 0 || unsigned(index) >= inputs.size())
        continue;

      auto& pf(inputs[index]);

      switch (pf.ptype) {
      case panda::PFCand::hm:
      case panda::PFCand::hp:
        outJet.chf += pf.e();
        break;
      case panda::PFCand::h0:
      case panda::PFCand::h_HF:
        outJet.nhf += pf.e();
        break;
      default:
        break;
      }

      outJet.constituents.addRef(&pf);
    }

    outJet.chf /= outJet.e();
    outJet.nhf /= outJet.e();
  }

  outJets.data.constituentsContainer_ = 0;
}

//--------------------------------------------------------------------
// JetScore
//--------------------------------------------------------------------

void
JetScore::addBranches(TTree& _skimTree)
{
  _skimTree.Branch("jets.score", score_, "score[jets.size]/F");
}

void
JetScore::apply(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  if (_outEvent.jets.size() == 0)
    return;

  for (unsigned iJ(0); iJ != _outEvent.jets.size(); ++iJ) {
    auto& jet(_outEvent.jets[iJ]);
    double che(jet.rawPt * jet.chf);
    score_[iJ] = che * che * 0.8 * 0.8;
  }
}

//--------------------------------------------------------------------
// LeptonVertex
//--------------------------------------------------------------------

void
LeptonVertex::addInputBranch(panda::utils::BranchList& _blist)
{
  _blist += {"pfCandidates"};
}

void
LeptonVertex::addBranches(TTree& _skimTree)
{
  _skimTree.Branch("lvertex.idx", &ivtx_, "idx/S");
  _skimTree.Branch("lvertex.idxNoL", &ivtxNoL_, "idxNoL/S");
  _skimTree.Branch("lvertex.score", &score_, "score/F");
}

void
LeptonVertex::apply(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  ivtx_ = -1;
  ivtxNoL_ = -1;
  score_ = 0.;

  panda::LeptonCollection* col(0);
  int pdgId(0);

  switch (flavor_) {
  case lElectron:
    col = &_outEvent.electrons;
    pdgId = 11;
    break;
  case lMuon:
    col = &_outEvent.muons;
    pdgId = 13;
    break;
  default:
    return;
  }

  if (col->size() == 0)
    return;

  std::vector<panda::PFCand const*> pfs;
  pfs.reserve(16);
  unsigned iPF(0);
  for (auto& pf : _event.pfCandidates) {
    if (std::abs(pf.pdgId()) == pdgId)
      pfs.push_back(&pf);

    ++iPF;
  }

  panda::PFCand const* cand(0);
  for (auto& lepton : *col) {
    for (auto* pf : pfs) {
      if (pf->dR2(lepton) < 0.01) {
        cand = pf;
        break;
      }
    }
    if (cand)
      break;
  }

  if (!cand)
    return;

  unsigned iPFMin(0);
  if (cand->vertex.idx() != 0)
    iPFMin = _event.vertices[cand->vertex.idx() - 1].pfRangeMax;

  ivtx_ = cand->vertex.idx();
  auto& vertex(*cand->vertex);
  score_ = vertex.score;

  for (unsigned iPF(iPFMin); iPF != vertex.pfRangeMax; ++iPF) {
    auto& pf(_event.pfCandidates[iPF]);

    bool isLepton(&pf == cand);
    if (!isLepton) {
      if (std::abs(pf.pdgId()) != pdgId)
        continue;

      for (auto& lepton : *col) {
        if (pf.dR2(lepton) < 0.01) {
          isLepton = true;
          break;
        }
      }
    }
    
    if (!isLepton)
      continue;

    double pt(pf.pt()); // actually has to be pt - ptError
    score_ -= pt * pt;
  }

  for (ivtxNoL_ = ivtx_; ivtxNoL_ < int(_event.vertices.size()) - 1; ++ivtxNoL_) {
    if (score_ > _event.vertices[ivtxNoL_ + 1].score)
      break;
  }
}

//--------------------------------------------------------------------
// WHadronizer
//--------------------------------------------------------------------

void
WHadronizer::addBranches(TTree& _skimTree)
{
  _skimTree.Branch("reweight_whadronizer", &weight_, "reweight_whadronizer/D");
}

void
WHadronizer::apply(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  weight_ = 67.41 / (10.86 * 3.);
  _outEvent.weight *= weight_;

  for (auto& part : _event.genParticles) {
    if (!part.finalState)
      continue;

    unsigned absId(std::abs(part.pdgid));
    if (absId < 11 || absId > 16)
      continue;

    auto* parent(part.parent.get());
    if (parent && std::abs(parent->pdgid) == part.pdgid)
      parent = parent->parent.get();

    if (parent && std::abs(parent->pdgid) == 24) {
      auto& outJet(_outEvent.jets.create_back());
      outJet.setPtEtaPhiM(part.pt(), part.eta(), part.phi(), part.m());
      outJet.puid = 1.;
      outJet.rawPt = part.pt();
    }
  }
}

//--------------------------------------------------------------------
// PhotonRecoil
//--------------------------------------------------------------------

void
PhotonRecoil::addBranches(TTree& _skimTree)
{
  _skimTree.Branch("t1Met.realMet", &realMet_, "realMet/F");
  _skimTree.Branch("t1Met.realPhi", &realPhi_, "realPhi/F");
}

void
PhotonRecoil::apply(panda::EventMonophoton const& _event, panda::EventMonophoton& _outEvent)
{
  float inMets[] = {
    _outEvent.t1Met.pt,
    _outEvent.t1Met.ptCorrUp,
    _outEvent.t1Met.ptCorrDown,
    _outEvent.t1Met.ptUnclUp,
    _outEvent.t1Met.ptUnclDown
  };
  float inPhis[] = {
    _outEvent.t1Met.phi,
    _outEvent.t1Met.phiCorrUp,
    _outEvent.t1Met.phiCorrDown,
    _outEvent.t1Met.phiUnclUp,
    _outEvent.t1Met.phiUnclDown
  };

  float* outRecoils[] = {
    &_outEvent.t1Met.pt,
    &_outEvent.t1Met.ptCorrUp,
    &_outEvent.t1Met.ptCorrDown,
    &_outEvent.t1Met.ptUnclUp,
    &_outEvent.t1Met.ptUnclDown
  };
  float* outRecoilPhis[] = {
    &_outEvent.t1Met.phi,
    &_outEvent.t1Met.phiCorrUp,
    &_outEvent.t1Met.phiCorrDown,
    &_outEvent.t1Met.phiUnclUp,
    &_outEvent.t1Met.phiUnclDown
  };

  float* realMets[] = {
    &realMet_,
    &realMetCorrUp_,
    &realMetCorrDown_,
    &realMetUnclUp_,
    &realMetUnclDown_
  };
  float* realPhis[] = {
    &realPhi_,
    &realPhiCorrUp_,
    &realPhiCorrDown_,
    &realPhiUnclUp_,
    &realPhiUnclDown_
  };

  for (unsigned iM(0); iM != sizeof(realMets) / sizeof(float*); ++iM) {
    *realMets[iM] = inMets[iM];
    *realPhis[iM] = inPhis[iM];
  }

  double phox(0.);
  double phoy(0.);
    
  for (unsigned iP(0); iP != _outEvent.photons.size(); ++iP) {
    if (iP == 0)
      continue;
    
    auto& pho = _outEvent.photons[iP];

    phox += pho.pt() * std::cos(pho.phi());
    phoy += pho.pt() * std::sin(pho.phi());
  }

  for (unsigned iM(0); iM != sizeof(realMets) / sizeof(float*); ++iM) {
    double mex(phox + inMets[iM] * std::cos(inPhis[iM]));
    double mey(phoy + inMets[iM] * std::sin(inPhis[iM]));
    *outRecoils[iM] = std::sqrt(mex * mex + mey * mey);
    *outRecoilPhis[iM] = std::atan2(mey, mex);
  } 
}

//--------------------------------------------------------------------
// PUWeight
//--------------------------------------------------------------------

void
PUWeight::addBranches(TTree& _skimTree)
{
  _skimTree.Branch("weight_" + name_, &weight_, "weight_" + name_ + "/D");
}

void
PUWeight::apply(panda::EventMonophoton const& _event, panda::EventBase& _outEvent)
{
  int iX(factors_->FindFixBin(_event.npvTrue));
  if (iX == 0)
    iX = 1;
  if (iX > factors_->GetNbinsX())
    iX = factors_->GetNbinsX();

  weight_ = factors_->GetBinContent(iX);

  _outEvent.weight *= weight_;
}

//--------------------------------------------------------------------
// TPLeptonPhoton
//--------------------------------------------------------------------

void
TPLeptonPhoton::addBranches(TTree& _skimTree)
{
  _skimTree.Branch("probes.chargedPFVeto", chargedPFVeto_, "chargedPFVeto[probes.size]/O");
  _skimTree.Branch("probes.hasCollinearL", hasCollinearL_, "hasCollinearL[probes.size]/O");
  _skimTree.Branch("probes.ptdiff", ptdiff_, "ptdiff[probes.size]/F");
}

void
TPLeptonPhoton::addInputBranch(panda::utils::BranchList& _blist)
{
  _blist += {"pfCandidates"};
}

bool
TPLeptonPhoton::pass(panda::EventMonophoton const& _inEvent, panda::EventTP& _outEvent)
{
  panda::LeptonCollection const* leptons(0);
  double tagMaxEta(0.);
  switch (eventType_) {
  case kTPEG:
  case kTPEEG:
    leptons = &_inEvent.electrons;
    tagMaxEta = 2.5;
    break;
  case kTPMG:
  case kTPMMG:
    leptons = &_inEvent.muons;
    tagMaxEta = 2.1;
    break;
  default:
    throw runtime_error("Incompatible event type in TPLeptonPhoton");
  }

  std::vector<panda::PFCand const*> chargedCands;

  for (auto& cand : _inEvent.pfCandidates) {
    if (cand.q() != 0)
      chargedCands.push_back(&cand);
  }

  for (auto& photon : _inEvent.photons) {
    if (!photon.isEB || photon.scRawPt < minProbePt_)
      continue;

    bool chargedPFMatch(false);

    for (auto* cand : chargedCands) {
      double dr(cand->dR(photon));
      if (dr > chargedPFDR_)
        continue;

      double relPt(cand->pt() / photon.scRawPt);
      if (relPt > chargedPFRelPt_) {
        chargedPFMatch = true;
        break;
      }
    }

    auto&& pg(photon.p4());

    for (auto& lepton : *leptons) {
      if (!lepton.tight)
        continue;

      if (lepton.pt() < minTagPt_ || std::abs(lepton.eta()) > tagMaxEta)
        continue;

      // see discussion on lepton veto below for the choice of the cone size
      if (photon.dR2(lepton) < 0.09)
        continue;

      if (eventType_ == kTPMG || eventType_ == kTPMMG) {
        auto& muon(static_cast<panda::Muon const&>(lepton));
        if (muon.combIso() / muon.pt() > 0.15)
          continue;
      }

      bool hasCollinearL(false);

      if (eventType_ == kTPEEG || eventType_ == kTPMMG) {
        for (auto& looseLepton : *leptons) {
          if (&looseLepton == &lepton)
            continue;

          if (!looseLepton.loose || looseLepton.pt() < 2.)
            continue;

          // we do need to allow loose leptons pretty close to the photon
          // since the bulk of FSR events exist in that phase space
          if (photon.dR2(looseLepton) < 0.01) {
            hasCollinearL = true;
            continue;
          }

          TLorentzVector pll(lepton.p4() + looseLepton.p4());
          double mllg((pg + pll).M());

          if (mllg < 20. || mllg > 160.)
            continue;

          auto& tp(_outEvent.tp.create_back());
          tp.mass = mllg;
          tp.mass2 = pll.M();

          if (eventType_ == kTPEEG) {
            auto& outEvent(static_cast<panda::EventTPEEG&>(_outEvent));
            outEvent.looseTags.push_back(static_cast<panda::Electron const&>(looseLepton));
            outEvent.tags.push_back(static_cast<panda::Electron const&>(lepton));
            outEvent.probes.push_back(photon);
          }
          else {
            auto& outEvent(static_cast<panda::EventTPMMG&>(_outEvent));
            outEvent.looseTags.push_back(static_cast<panda::Muon const&>(looseLepton));
            outEvent.tags.push_back(static_cast<panda::Muon const&>(lepton));
            outEvent.probes.push_back(photon);
          }

          chargedPFVeto_[_outEvent.tp.size() - 1] = !chargedPFMatch;
        }
      }
      else {
	auto&& pl(lepton.p4());
        double mlg((pg + pl).M());
	
	// calculate expected pt using z mass 
	TLorentzVector ug;
	ug.SetPtEtaPhiM(1., photon.eta(), photon.phi(), 0.);
	float ptdiff = (91.2 * 91.2) / (2 * ug.Dot(pl)) - photon.scRawPt;
	
        // if (mlg < 20. || mlg > 160.)
        //   continue;

        // veto additional loose leptons
        unsigned iVeto(0);
        for (; iVeto != leptons->size(); ++iVeto) {
          auto& veto((*leptons)[iVeto]);

          if (&veto == &lepton)
            continue;

          if (eventType_ == kTPEG) {
            if (!static_cast<panda::Electron const&>(veto).veto)
              continue;
          }
          else {
            if (!veto.loose)
              continue;
          }

          if (veto.pt() < 10.)
            continue;

          // Our electron veto does not reject photons overlapping with e/mu
          // Cases:
          // 1. One electron radiates hard, gets deflected by a large angle
          //   -> The radiation is a photon, and the deflected electron is an additional
          //   lepton. Veto the event.
          // 2. One electron radiates hard but stays collinear with the radiation
          //   -> This is an electron faking a photon. The event should be included
          //   in the "eg" sample of the tag & probe fit.
          //
          // Large angle is defined by the isolation cone of the electron, which defines
          // what object can be considered an independent electron.
          if (photon.dR2(veto) < 0.09) {
            hasCollinearL = true;
            continue;
          }

          break;
        }
        if (iVeto != leptons->size())
          continue;

        auto& tp(_outEvent.tp.create_back());
        tp.mass = mlg;

        if (eventType_ == kTPEG) {
          auto& outEvent(static_cast<panda::EventTPEG&>(_outEvent));
          outEvent.tags.push_back(static_cast<panda::Electron const&>(lepton));
          outEvent.probes.push_back(photon);
        }
        else {
          auto& outEvent(static_cast<panda::EventTPMG&>(_outEvent));
          outEvent.tags.push_back(static_cast<panda::Muon const&>(lepton));
          outEvent.probes.push_back(photon);
        }

        chargedPFVeto_[_outEvent.tp.size() - 1] = !chargedPFMatch;
        hasCollinearL_[_outEvent.tp.size() - 1] = hasCollinearL;
	ptdiff_[_outEvent.tp.size() - 1] = ptdiff;
      }
    }
  }
  
  return _outEvent.tp.size() != 0;
}

//--------------------------------------------------------------------
// TPDilepton
//--------------------------------------------------------------------

void
TPDilepton::addBranches(TTree& _skimTree)
{
  _skimTree.Branch("probes.matchedGenId", probeGenId_, "matchedGenId[probes.size]/I");
}

bool
TPDilepton::pass(panda::EventMonophoton const& _inEvent, panda::EventTP& _outEvent)
{
  panda::LeptonCollection const* leptons(0);
  double maxEta(0.);
  switch (eventType_) {
  case kTP2E:
    leptons = &_inEvent.electrons;
    maxEta = 2.5;
    break;
  case kTP2M:
    leptons = &_inEvent.muons;
    maxEta = 2.1;
    break;
  default:
    throw runtime_error("Incompatible event type in TPDilepton");
  }

  for (auto& tag : *leptons) {
    if (!tag.tight || tag.pt() < minTagPt_ || std::abs(tag.eta()) > maxEta)
      continue;

    if (eventType_ == kTP2M && tag.combIso() / tag.pt() > 0.15)
      continue;

    for (auto& probe : *leptons) {
      if (&probe == &tag)
        continue;

      double mll((tag.p4() + probe.p4()).M());

      if (mll < 20. || mll > 160.)
        continue;

      auto& tp(_outEvent.tp.create_back());
      tp.mass = mll;

      if (eventType_ == kTP2E) {
        auto& outEvent(static_cast<panda::EventTP2E&>(_outEvent));
        outEvent.tags.push_back(static_cast<panda::Electron const&>(tag));
        outEvent.probes.push_back(static_cast<panda::Electron const&>(probe));
      }
      else {
        auto& outEvent(static_cast<panda::EventTP2M&>(_outEvent));
        outEvent.tags.push_back(static_cast<panda::Muon const&>(tag));
        outEvent.probes.push_back(static_cast<panda::Muon const&>(probe));
      }

      if(probe.matchedGen.isValid())
        probeGenId_[_outEvent.tp.size() - 1] = probe.matchedGen->pdgid;
      else
        probeGenId_[_outEvent.tp.size() - 1] = 0;
    }
  }
  
  return _outEvent.tp.size() != 0;
}

//--------------------------------------------------------------------
// TPLeptonVeto
//--------------------------------------------------------------------

void
TPLeptonVeto::addBranches(TTree& _skimTree)
{
  _skimTree.Branch("electrons.size", &nElectrons_, "size/i");
  _skimTree.Branch("muons.size", &nMuons_, "size/i");
}

bool
TPLeptonVeto::pass(panda::EventMonophoton const& _inEvent, panda::EventTP& _outEvent)
{
  // veto condition: loose, pt > 10 GeV, no matching candidate photon / lepton

  std::vector<panda::ParticleCollection const*> cols;
  if (eventType_ == kTPEEG || eventType_ == kTPMMG)
    cols.emplace_back(getLooseTags(_outEvent));
  cols.emplace_back(getTags(_outEvent));
  cols.emplace_back(getProbes(_outEvent));
    
  nMuons_ = 0;
  
  std::vector<panda::Muon const*> goodMuons;

  for (auto& muon : _inEvent.muons) {
    if (!muon.loose || muon.pt() < 10.)
      continue;

    bool overlap(false);
    for (auto* col : cols) {
      unsigned iP(0);
      for (; iP != col->size(); ++iP) {
        if ((*col)[iP].dR2(muon) < 0.25)
          break;
      }
      if (iP != col->size()) {
        // there was an overlappin particle
        overlap = true;
        break;
      }
    }

    if (!overlap) {
      goodMuons.push_back(&muon);
      ++nMuons_;
    }
  }

  nElectrons_ = 0;

  for (auto& electron : _inEvent.electrons) {
    if (!electron.loose || electron.pt() < 10.)
      continue;

    bool overlap(false);
    for (auto* col : cols) {
      unsigned iP(0);
      for (; iP != col->size(); ++iP) {
        if ((*col)[iP].dR2(electron) < 0.25)
          break;
      }
      if (iP != col->size()) {
        // there was an overlappin particle
        overlap = true;
        break;
      }
    }

    if (overlap)
      continue;

    unsigned iP(0);
    for (; iP != goodMuons.size(); ++iP) {
      if (goodMuons[iP]->dR2(electron) < 0.25)
        break;
    }
    if (iP == goodMuons.size())
      ++nElectrons_;
  }

  bool result(true);
  if (vetoElectrons_ && nElectrons_ != 0)
    result = false;
  if (vetoMuons_ && nMuons_ != 0)
    result = false;

  return result;
}

//--------------------------------------------------------------------
// TPJetCleaning
//--------------------------------------------------------------------

void
TPJetCleaning::apply(panda::EventMonophoton const& _event, panda::EventTP& _outEvent)
{
  std::vector<std::pair<panda::ParticleCollection const*, bool>> cols;
  bool leadingProbeOnly(false);
  if (eventType_ == kTPEEG || eventType_ == kTPMMG) {
    leadingProbeOnly = true;
    cols.emplace_back(getLooseTags(_outEvent), false);
  }
  else if (eventType_ == kTPEG || eventType_ == kTPMG)
    leadingProbeOnly = true;

  cols.emplace_back(getTags(_outEvent), false);
  cols.emplace_back(getProbes(_outEvent), leadingProbeOnly);

  for (auto& jet : _event.jets) {
    if (jet.pt() < minPt_ || std::abs(jet.eta()) > 5.)
      continue;

    bool overlap(false);
    for (auto& col : cols) {
      // For TPXG probes, we only want to clean overlaps wrt the leading candidate
      unsigned nP(col.second ? std::min(unsigned(1), col.first->size()) : col.first->size());

      unsigned iP(0);
      for (; iP != nP; ++iP) {
        if (jet.dR2((*col.first)[iP]) < 0.16)
          break;
      }
      if (iP != nP) {
        overlap = true;
        break;
      }
    }
    if (overlap)
      continue;

    _outEvent.jets.push_back(jet);
  }
}

//--------------------------------------------------------------------
// TPTriggerMatch
//--------------------------------------------------------------------

void
TPTriggerMatch::initialize(panda::EventMonophoton& _event)
{
  _event.run.setLoadTrigger(true);
  for (auto& name : filterNames_)
    _event.registerTriggerObjects(name);
}

void
TPTriggerMatch::addInputBranch(panda::utils::BranchList& _blist)
{
  _blist += {"triggerObjects"};
}

void
TPTriggerMatch::addBranches(TTree& _skimTree)
{
  if (candidate_ == kProbe)
    _skimTree.Branch("probes.hltmatch" + name_, matchResults_, "hltmatch" + name_ + "[probes.size]/O");
  else
    _skimTree.Branch("tags.hltmatch" + name_, matchResults_, "hltmatch" + name_ + "[tags.size]/O");
}

void
TPTriggerMatch::apply(panda::EventMonophoton const& _event, panda::EventTP& _outEvent)
{
  typedef std::vector<panda::HLTObject const*> HLTObjectVector;

  std::fill_n(matchResults_, NMAX_PARTICLES, false);

  bool any(false);
  std::vector<std::pair<HLTObjectVector const*, double>> filterObjects;
  for (auto& name : filterNames_) {
    //    std::cout << "Looking for objects for filter " << name << std::endl;
    auto& objects(_event.triggerObjects.filterObjects(name));
    if (objects.size() != 0)
      any = true;

    //    std::cout << "Found: size " << objects.size() << std::endl;
    double dR(name.Index("hltL1s") == 0 ? 0.3 : 0.15);
    filterObjects.emplace_back(&objects, dR);
  }

  if (!any)
    return;

  auto& candidates(candidate_ == kProbe ? *getProbes(_outEvent) : *getTags(_outEvent));

  //  std::cout << "now match against candidates: size " << candidates.size() << std::endl;

  for (unsigned iP(0); iP != candidates.size(); ++iP) {
    auto& cand(candidates[iP]);

    for (auto& pair : filterObjects) {
      auto& objects(*pair.first);
      double dR(pair.second);

      unsigned iO(0);
      for (; iO != objects.size(); ++iO) {
        if (cand.dR(*objects[iO]) < dR) {
          matchResults_[iP] = true;
          break;
        }
      }
      if (iO != objects.size())
        break;
    }
  }
}
