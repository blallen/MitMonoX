#ifndef photon_extra_h
#define photon_extra_h

#include "PandaTree/Objects/interface/XPhoton.h"
#include "PandaTree/Objects/interface/UnpackedGenParticle.h"

namespace panda {

  void
  photon_extra(panda::XPhoton& _dest, panda::Photon const& _src, double _rho, panda::UnpackedGenParticleCollection const* _genParticles = 0)
  {
    auto& superCluster(*_src.superCluster);

    _dest.scRawPt = superCluster.rawPt;
    _dest.scEta = superCluster.eta;
    _dest.e4 = _src.eleft + _src.eright + _src.etop + _src.ebottom;
    _dest.isEB = std::abs(_dest.scEta) < 1.4442;

    // Recomputing isolation with scRawPt
    // S15 isolation valid only for panda >= 003
    // In 002 we had Spring15 leakage correction but Spring16 effective areas (production error).

    double absEta(std::abs(_dest.scEta));

    panda::XPhoton::IDTune const nID(panda::XPhoton::nIDTunes);
    panda::XPhoton::IDTune const s15(panda::XPhoton::kSpring15);
    panda::XPhoton::IDTune const s16(panda::XPhoton::kSpring16);
    panda::XPhoton::IDTune const f17(panda::XPhoton::kFall17);
    panda::XPhoton::IDTune const gj(panda::XPhoton::kGJetsCWIso);
    panda::XPhoton::IDTune const zg(panda::XPhoton::kZGCWIso);

    double chIsoEA[nID]{};
    double nhIsoEA[nID]{};
    double phIsoEA[nID]{};
    double chIsoMaxEA[nID]{};
    if (absEta < 1.) {
      nhIsoEA[s15] = 0.0599;
      phIsoEA[s15] = 0.1271;

      chIsoEA[s16] = 0.0360;
      nhIsoEA[s16] = 0.0597;
      phIsoEA[s16] = 0.1210;

      chIsoEA[f17] = 0.0112;
      nhIsoEA[f17] = 0.0668;
      phIsoEA[f17] = 0.1113;

      chIsoMaxEA[gj] = 0.1064;

      chIsoMaxEA[zg] = chIsoMaxEA[gj];
    }
    else if (absEta < 1.479) {
      nhIsoEA[s15] = 0.0819;
      phIsoEA[s15] = 0.1101;

      chIsoEA[s16] = 0.0377;
      nhIsoEA[s16] = 0.0807;
      phIsoEA[s16] = 0.1107;

      chIsoEA[f17] = 0.0108;
      nhIsoEA[f17] = 0.1054;
      phIsoEA[f17] = 0.0953;

      chIsoMaxEA[gj] = 0.1026;

      chIsoMaxEA[zg] = chIsoMaxEA[gj];
    }
    else if (absEta < 2.) {
      nhIsoEA[s15] = 0.0696;
      phIsoEA[s15] = 0.0756;

      chIsoEA[s16] = 0.0306;
      nhIsoEA[s16] = 0.0629;
      phIsoEA[s16] = 0.0699;

      chIsoEA[f17] = 0.0106;
      nhIsoEA[f17] = 0.0786;
      phIsoEA[f17] = 0.0619;
    }
    else if (absEta < 2.2) {
      nhIsoEA[s15] = 0.0360;
      phIsoEA[s15] = 0.1175;

      chIsoEA[s16] = 0.0283;
      nhIsoEA[s16] = 0.0197;
      phIsoEA[s16] = 0.1056;

      chIsoEA[f17] = 0.01002;
      nhIsoEA[f17] = 0.0233;
      phIsoEA[f17] = 0.0837;
    }
    else if (absEta < 2.3) {
      nhIsoEA[s15] = 0.0360;
      phIsoEA[s15] = 0.1498;

      chIsoEA[s16] = 0.0254;
      nhIsoEA[s16] = 0.0184;
      phIsoEA[s16] = 0.1457;

      chIsoEA[f17] = 0.0098;
      nhIsoEA[f17] = 0.0078;
      phIsoEA[f17] = 0.1070;
    }
    else if (absEta < 2.4) {
      nhIsoEA[s15] = 0.0462;
      phIsoEA[s15] = 0.1857;

      chIsoEA[s16] = 0.0217;
      nhIsoEA[s16] = 0.0284;
      phIsoEA[s16] = 0.1719;

      chIsoEA[f17] = 0.0089;
      nhIsoEA[f17] = 0.0028;
      phIsoEA[f17] = 0.1212;
    }
    else {
      nhIsoEA[s15] = 0.0656;
      phIsoEA[s15] = 0.2183;

      chIsoEA[s16] = 0.0167;
      nhIsoEA[s16] = 0.0591;
      phIsoEA[s16] = 0.1998;

      chIsoEA[f17] = 0.0087;
      nhIsoEA[f17] = 0.0137;
      phIsoEA[f17] = 0.1466;
    }

    chIsoEA[gj] = chIsoEA[s16];
    nhIsoEA[gj] = nhIsoEA[s16];
    phIsoEA[gj] = phIsoEA[s16];

    chIsoEA[zg] = chIsoEA[s16];
    nhIsoEA[zg] = nhIsoEA[s16];
    phIsoEA[zg] = phIsoEA[s16];

    double nhIsoE1[nID]{};
    double nhIsoE2[nID]{};
    double phIsoE1[nID]{};

    if (_dest.isEB) {
      nhIsoE1[s15] = 0.014;
      nhIsoE2[s15] = 0.000019;
      phIsoE1[s15] = 0.0053;

      nhIsoE1[s16] = 0.0148;
      nhIsoE2[s16] = 0.000017;
      phIsoE1[s16] = 0.0047;

      nhIsoE1[f17] = 0.01512;
      nhIsoE2[f17] = 2.259e-5;
      phIsoE1[f17] = 0.004017;

      nhIsoE1[gj] = 0.0112;
      nhIsoE2[gj] = 0.000028;
      phIsoE1[gj] = 0.0043;

      nhIsoE1[zg] = nhIsoE1[gj];
      nhIsoE2[zg] = nhIsoE2[gj];
      phIsoE1[zg] = phIsoE1[gj];
    }
    else {
      nhIsoE1[s15] = 0.0139;
      nhIsoE2[s15] = 0.000025;
      phIsoE1[s15] = 0.0034;

      nhIsoE1[s16] = 0.0163;
      nhIsoE2[s16] = 0.000014;
      phIsoE1[s16] = 0.0034;

      nhIsoE1[f17] = 0.0117;
      nhIsoE2[f17] = 2.3e-5;
      phIsoE1[f17] = 0.0037;
    }

    double pt(_src.pt());
    double pt2(pt * pt);
    double scpt(_dest.scRawPt);
    double scpt2(scpt * scpt);

    double chIsoCore(_src.chIso + chIsoEA[f17] * _rho);
    double nhIsoCore(_src.nhIso + nhIsoEA[f17] * _rho + nhIsoE1[f17] * pt + nhIsoE2[f17] * pt2);
    double phIsoCore(_src.phIso + phIsoEA[f17] * _rho + phIsoE1[f17] * pt);

    for (unsigned iD(0); iD != nID; ++iD) {
      _dest.chIsoX[iD] = chIsoCore - chIsoEA[iD] * _rho;
      _dest.nhIsoX[iD] = nhIsoCore - nhIsoEA[iD] * _rho - nhIsoE1[iD] * scpt - nhIsoE2[iD] * scpt2;
      _dest.phIsoX[iD] = phIsoCore - phIsoEA[iD] * _rho - phIsoE1[iD] * scpt;
      _dest.chIsoMaxX[iD] = _src.chIsoMax - chIsoMaxEA[iD] * _rho;

      _dest.looseX[iD] = _dest.passHOverE(0, iD) && _dest.passSieie(0, iD) &&
        _dest.passCHIso(0, iD) && _dest.passNHIso(0, iD) && _dest.passCHIso(0, iD);
      _dest.mediumX[iD] = _dest.passHOverE(1, iD) && _dest.passSieie(1, iD) &&
        _dest.passCHIso(1, iD) && _dest.passNHIso(1, iD) && _dest.passCHIso(1, iD);
      _dest.tightX[iD] = _dest.passHOverE(2, iD) && _dest.passSieie(2, iD) &&
        _dest.passCHIso(2, iD) && _dest.passNHIso(2, iD) && _dest.passCHIso(2, iD);
    }

    if (_genParticles) {
      _dest.matchedGenId = 0;
      if (_src.matchedGen.isValid()) {
        _dest.matchedGenId = _src.matchedGen->pdgid;
        if (_dest.matchedGenId == 22) {
          auto& gen(*_src.matchedGen);
          if (gen.testFlag(panda::GenParticle::kIsPrompt) ||
              (gen.parent.isValid() && gen.parent->pdgid == 22 && gen.parent->testFlag(panda::GenParticle::kIsPrompt)))
            _dest.matchedGenId = -22;
        }
      }

      if (_dest.matchedGenId == 0) {
        // passed genParticles is the post-copy collection where only prompt photons / leptons are saved
        double dR2Min(-1.);
        for (auto& gen : *_genParticles) {
          double dR2(gen.dR2(_dest));
          if (dR2Min < 0. || dR2 < dR2Min) {
            _dest.matchedGenId = gen.pdgid;
            unsigned absId(_dest.matchedGenId);
            if (dR2 < 0.01 && (absId == 11 || absId == 13))
              break;

            dR2Min = dR2;
          }
        }
      }
    }
  }

}

#endif
