#include "TreeEntries_simpletree.h"
#include "SimpleTreeUtils.h"

#include "TTree.h"
#include "TFile.h"
#include "TString.h"

#include <iostream>

enum EventType {
  kDiphoton,
  kElectronPhoton,
  kMuonPhoton,
  kJetHT,
  kDimuon,
  kDielectron,
  nEventTypes
};

void
skim(TTree* _input, EventType _eventType, char const* _outputName, long _nEntries = -1)
{
  auto* outputFile(TFile::Open(_outputName, "recreate"));
  auto* output(new TTree("triggerTree", "trigger matching"));

  unsigned runNum;
  unsigned lumiNum;
  unsigned eventNum;
  float rho;
  unsigned short npv;

  simpletree::MuonCollection outMuons("probe");
  simpletree::ElectronCollection outElectrons("probe");
  simpletree::PhotonCollection outPhotons("probe"); // will only have one element

  output->Branch("run", &runNum, "run/i");
  output->Branch("lumi", &lumiNum, "lumi/i");
  output->Branch("event", &eventNum, "event/i");
  output->Branch("rho", &rho, "rho/F");
  output->Branch("npv", &npv, "npv/s");
  
  switch (_eventType) {
  case kDimuon:
    outMuons.book(*output);
    outMuons.resize(1);
    break;
  case kDielectron:
    outElectrons.book(*output);
    outElectrons.resize(1);
    break;
  default:
    outPhotons.book(*output);
    outPhotons.resize(1);
    break;
  }

  simpletree::Event event;
  event.setStatus(*_input, false, {"*"});
  event.setAddress(*_input, {"run", "lumi", "event", "rho", "npv", "hltBits", "photons", "electrons", "muons"});

  std::vector<simpletree::TriggerHelper*> triggers;
  switch (_eventType) {
  case kDiphoton:
    triggers.push_back(new simpletree::TriggerHelper("HLT_Photon36_R9Id90_HE10_Iso40_EBOnly_PFMET40"));
    break;
  case kElectronPhoton:
    triggers.push_back(new simpletree::TriggerHelper("HLT_Ele23_WPLoose_Gsf"));
    break;
  case kMuonPhoton:
    triggers.push_back(new simpletree::TriggerHelper("HLT_IsoMu20"));
    break;
  case kJetHT:
    triggers.push_back(new simpletree::TriggerHelper("HLT_DiPFJetAve80"));
    triggers.push_back(new simpletree::TriggerHelper("HLT_PFHT400_SixJet30"));
    triggers.push_back(new simpletree::TriggerHelper("HLT_HT650"));
    break;
  case kDimuon:
    triggers.push_back(new simpletree::TriggerHelper("HLT_IsoMu20"));
    break;
  case kDielectron:
    triggers.push_back(new simpletree::TriggerHelper("HLT_Ele23_WPLoose_Gsf"));
    break;
  default:
    break;
  }

  auto passTrigger([&triggers, &event]()->bool {
      if (triggers.size() == 0)
        return true;

      for (auto* h : triggers) {
        if (h->pass(event))
          return true;
      }
      return false;
    });

  long iEntry(0);
  while (iEntry != _nEntries && _input->GetEntry(iEntry++) > 0) {
    if (iEntry % 100000 == 1)
      std::cout << iEntry << std::endl;

    try {
      if (!passTrigger())
        continue;
    }
    catch (std::exception& ex) {
      std::cerr << ex.what() << std::endl;
      return;
    }

    runNum = event.run;
    lumiNum = event.lumi;
    eventNum = event.event;
    rho = event.rho;
    npv = event.npv;

    switch (_eventType) {
    case kDimuon:
      for (auto& muon : event.muons) {
	if (!muon.tight)
	  continue;
	
	unsigned iTag(0);
	for (; iTag != event.muons.size(); ++iTag) {
	  auto& tag(event.muons[iTag]);
	  if (&tag == &muon)
	    continue;
	  
	  if ( !(tag.pt > 25. && tag.tight && tag.matchHLT[simpletree::fMu20]))
	    continue;

	  float mass = (muon.p4() + tag.p4()).M();
	  if (mass > 61. && mass < 121.)
	    break;
	}
	if (iTag == event.muons.size())
	  continue;
	
	outMuons[0] = muon;
	output->Fill();
      }
      break;
      
    case kDielectron:
      for (auto& electron : event.electrons) {
	if (!electron.tight)
	  continue;
	
	unsigned iTag(0);
	for (; iTag != event.electrons.size(); ++iTag) {
	  auto& tag(event.electrons[iTag]);
	  if (&tag == &electron)
	    continue;
	  
	  if ( !(tag.pt > 25. && tag.tight && tag.matchHLT[simpletree::fEl23Loose]))
	    continue;

	  float mass = (electron.p4() + tag.p4()).M();
	  if (mass > 61. && mass < 121.)
	    break;
	}
	if (iTag == event.electrons.size())
	  continue;
	
	outElectrons[0] = electron;
	output->Fill();
      }
      break;
      
    default:
      for (auto& photon : event.photons) {
	if (!photon.medium)
	  continue;
	
	switch (_eventType) {
	case kDiphoton:
	  if (!photon.pixelVeto)
	    continue;
	  break;
	case kDielectron:
	  if (photon.pixelVeto)
	    continue;
	  break;
	default:
	  break;
	}

	if (_eventType == kDiphoton) {
	  unsigned iTag(0);
	  for (; iTag != event.photons.size(); ++iTag) {
	    auto& tag(event.photons[iTag]);
	    if (&tag == &photon)
	      continue;

	    if (tag.matchHLT[simpletree::fPh36EBR9Iso])
	      break;
	  }
	  if (iTag == event.photons.size())
	    continue;
	}
	else if (_eventType == kElectronPhoton) {
	  unsigned iTag(0);
	  for (; iTag != event.electrons.size(); ++iTag) {
	    auto& tag(event.electrons[iTag]);
	    if (tag.dR2(photon) < 0.09)
	      continue;

	    if (tag.matchHLT[simpletree::fEl23Loose])
	      break;
	  }
	  if (iTag == event.electrons.size())
	    continue;
	}
	else if (_eventType == kMuonPhoton) {
	  unsigned iTag(0);
	  for (; iTag != event.muons.size(); ++iTag) {
	    auto& tag(event.muons[iTag]);
	    if (tag.dR2(photon) < 0.09)
	      continue;

	    if (tag.matchHLT[simpletree::fMu20])
	      break;
	  }
	  if (iTag == event.muons.size())
	    continue;
	}
	
	outPhotons[0] = photon;
	output->Fill();
      } // probe photons
      break;
    } // skim switch
  } // nEntries

  outputFile->cd();
  output->Write();
  delete outputFile;
}
