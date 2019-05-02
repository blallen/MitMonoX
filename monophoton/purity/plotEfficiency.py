import os
import sys
from pprint import pprint
from array import array
from subprocess import Popen, PIPE
import ROOT as r
import math

basedir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if basedir not in sys.path:
    sys.path.append(basedir)
import config
from plotstyle import WEBDIR, SimpleCanvas, RatioCanvas
import selections as s

versDir = WEBDIR + '/purity/' + s.Version
outDir = os.path.join(versDir, 'ScaleFactors')
if not os.path.exists(outDir):
    os.makedirs(outDir)

tune = 'GJetsCWIso' # 'Spring16'

outFile = r.TFile("../data/pvsf_" + tune + ".root", "RECREATE")

bases = s.bases
mods = s.mods
PhotonIds = [base+mod for base in bases for mod in mods]
PhotonPtSels = sorted(s.PhotonPtSels.keys())[:]
MetSels = sorted(s.MetSels.keys())[1:2]

yields = {}
for loc in s.Locations[:1]:
    yields[loc] = {}
    for pid in PhotonIds:
        yields[loc][pid] = {}
        for ptCut in PhotonPtSels:
            yields[loc][pid][ptCut] = {}
            for metCut in MetSels: 
                yields[loc][pid][ptCut][metCut] = {}
                dirName = tune + '_' + loc+'_'+pid+'_'+ptCut+'_'+metCut
                print dirName

                # Get Data Yields
                dataFileName = os.path.join(versDir,dirName,"results.out") 
                match = False
                try:
                    dataFile = open(dataFileName)

                    count = [1., 0.]
                    for line in dataFile:
                        if "# of real photons is:" in line:
                            # print line
                            tmp = line.split()
                            if tmp:
                                match = True
                                # pprint(tmp)
                                count[0] = float(tmp[-1].strip("(),"))
                                #print count
                        elif "Total unc yield is:" in line:
                            # print line
                            tmp = line.split()
                            if tmp:
                                match = True
                                # pprint(tmp)
                                count[1] = float(tmp[-1].strip("(),"))
                                #print count

                        # dataFile.close()

                    dataFile.close()

                except IOError:
                    print "No data eff file found for skim:", dirName
                    yields[loc][pid][ptCut][metCut]['data'] = (-1., 0.0)
                    
                if match:
                    yields[loc][pid][ptCut][metCut]['data'] = tuple(count)

                else:
                    print "No data yields found for skim:", dirName
                    yields[loc][pid][ptCut][metCut]['data'] = (-1., 0.0)


                # get mc effs
                mcFileName = os.path.join(versDir,dirName,"mceff.out") 
                gjMatch = False
                wjMatch = False
                    
                try:
                    mcFile = open(mcFileName)

                    gjCount = [1., 0.]
                    wjCount = [1., 0.]

                    count = [1., 0.]
                    for line in mcFile:
                        if "gj04 efficiency" in line:
                            # print line
                            tmp = line.split()
                            if tmp: 
                                gjMatch = True
                                # pprint(tmp)
                                gjCount[0] = float(tmp[-4].strip("(),+-"))
                                gjCount[1] = float(tmp[-3].strip("(),+-"))
                                #print count

                        elif "wlnun efficiency" in line:
                            # print line
                            tmp = line.split()
                            if tmp: 
                                wjMatch = True
                                # pprint(tmp)
                                wjCount[0] = float(tmp[-4].strip("(),+-"))
                                wjCount[1] = 0.14 * wjCount[0]
                                #print count

                    mcFile.close()

                except IOError:
                    print "No mc eff file found for skim:", dirName
                    yields[loc][pid][ptCut][metCut]['mc'] = (-1., 0.0)

                    
                if gjMatch and wjMatch:
                    count[0] = gjCount[0] + wjCount[0]
                    count[1] = math.sqrt(gjCount[1]**2 + wjCount[1]**2)

                    yields[loc][pid][ptCut][metCut]['mc'] = tuple(count)

                else:
                    print "No mc yields file found for skim:", dirName
                    yields[loc][pid][ptCut][metCut]['mc'] = (-1., 0.0)
                    
                    
pprint(yields)

canvas = SimpleCanvas(lumi = s.sphLumi)
rcanvas = SimpleCanvas(lumi = s.sphLumi, name = 'effs')

scalefactors = {}

passes = base+mods[2]
totals = base+mods[0]

for loc in s.Locations[:1]:
    scalefactors[loc] = {}
    for base in bases:
        scalefactors[loc][base] = {}
        print '\n' + base
        for metCut in MetSels:
            scalefactors[loc][base][metCut] = {}

            rcanvas.cd()
            rcanvas.Clear()
            rcanvas.legend.Clear()
            rcanvas.legend.setPosition(0.7, 0.8, 0.9, 0.9)

            canvas.cd()
            canvas.Clear()
            canvas.legend.Clear()
            canvas.legend.setPosition(0.7, 0.75, 0.9, 0.85)

            gDataEff = r.TGraphAsymmErrors()
            gDataEff.SetName(loc+'-'+base+mod+'-'+metCut+'-data')
            
            gMcEff = r.TGraphAsymmErrors()
            gMcEff.SetName(loc+'-'+base+mod+'-'+metCut+'-mc')
            
            gSF = r.TGraphAsymmErrors()
            gSF.SetName(loc+'-'+base+mod+'-'+metCut+'-sf')

            for iB, ptCut in enumerate(PhotonPtSels):        
                mcPasses = yields[loc][passes][ptCut][metCut]['mc']
                mcTotals = yields[loc][totals][ptCut][metCut]['mc']

                mcEff = mcPasses[0] / mcTotals[0]
                mcCorr = 0.
                mcEffError = mcEff * math.sqrt( (mcPasses[1]/mcPasses[0])**2 + (mcTotals[1]/mcTotals[0])**2 + 2*mcCorr*(mcPasses[1]/mcPasses[0])*(mcTotals[1]/mcPasses[0]) )

                dataPasses = yields[loc][passes][ptCut][metCut]['data']
                dataTotals = yields[loc][totals][ptCut][metCut]['data']

                dataEff = dataPasses[0] / dataTotals[0]
                dataCorr = 1.0
                dataEffError = dataEff * math.sqrt( (dataPasses[1]/dataPasses[0])**2 + (dataTotals[1]/dataTotals[0])**2 + 2*dataCorr*(dataPasses[1]/dataPasses[0])*(dataTotals[1]/dataPasses[0]) )

                sf = dataEff / mcEff
                sfErrLow = sf * math.sqrt( (dataEffError / dataEff)**2 + (mcEffError / mcEff)**2)
                sfErrHigh = sfErrLow

                scalefactors[loc][base][metCut][ptCut] = (sf, sfErrLow, dataEffError / dataEff, mcEffError / mcEff)

                if 'Inclusive' in ptCut:
                    continue
                else:
                    lowEdge = float(ptCut.split('t')[2])
                    highEdge = ptCut.split('to')[-1]
                    if highEdge == 'Inf':
                        highEdge = 500.
                    highEdge = float(highEdge)

                center = (lowEdge + highEdge) / 2.
                exl = center - lowEdge
                exh = highEdge - center

                gMcEff.SetPoint(iB, center, mcEff)
                gMcEff.SetPointError(iB, exl, exh, mcEffError, mcEffError)

                gDataEff.SetPoint(iB, center, dataEff)
                gDataEff.SetPointError(iB, exl, exh, dataEffError, dataEffError)

                gSF.SetPoint(iB, center, sf)
                gSF.SetPointError(iB, exl, exh, sfErrLow, sfErrHigh)

            outFile.cd()
            gMcEff.Write()
            gDataEff.Write()
            gSF.Write()

            rcanvas.legend.add("mc", title = 'mc', mcolor = r.kRed, lcolor = r.kRed, lwidth = 2)
            rcanvas.legend.apply("mc", gMcEff)
            rcanvas.addHistogram(gMcEff, drawOpt = 'EP')
            
            rcanvas.legend.add("data", title = "data", mcolor = r.kBlack, lcolor = r.kBlack, lwidth = 2)
            rcanvas.legend.apply("data", gDataEff)
            rcanvas.addHistogram(gDataEff, drawOpt = 'EP')

            canvas.legend.add(loc+'-'+base, title = loc+' '+base, color = r.kBlack, lwidth = 2)
            canvas.legend.apply(loc+'-'+base, gSF)
            canvas.addHistogram(gSF, drawOpt = 'EP')
            
            rcanvas.xlimits = (175., 500.)
            rcanvas.ylimits = (0.8, 1.0)
            rcanvas.ytitle = 'Pixel Veto Efficiency'
            rcanvas.xtitle = 'E_{T}^{#gamma} (GeV)'
            # rcanvas.SetGridy(True)

            suffix = str(tune) + '_' + str(metCut) + '_' + str(loc) + '_'  +str(base)

            plotName = 'efficiency_' + suffix
            rcanvas.printWeb('purity/'+s.Version+'/ScaleFactors', plotName, logy = False)
            
            canvas.xlimits = (175., 500.)
            canvas.ylimits = (0.95, 1.05)
            canvas.ytitle = 'Pixel Veto Scale Factor'
            canvas.xtitle = 'E_{T}^{#gamma} (GeV)'
            # canvas.SetGridy(True)

            plotName = 'scalefactor_' + suffix
            canvas.printWeb('purity/'+s.Version+'/ScaleFactors', plotName, logy = False, drawLegend = False)

outFile.Close()

for loc in s.Locations[:1]:
    for base in bases:
        for metCut in MetSels:
            suffix = str(tune) + '_' + str(metCut) + '_' + str(loc) + '_'  +str(base)

            outFileName = 'table_' + suffix + '.tex'
            outFilePath = outDir + '/' + outFileName
            outFile = open(outFilePath, 'w')

            outFile.write(r"\documentclass{article}")
            outFile.write("\n")
            outFile.write(r"\usepackage[paperwidth=115mm, paperheight=58mm, margin=5mm]{geometry}")
            outFile.write("\n")
            outFile.write(r"\begin{document}")
            outFile.write("\n")
            outFile.write(r"\pagenumbering{gobble}")
            outFile.write("\n")

            # table header based on ID
            outFile.write(r"\begin{tabular}{ |c|c|c c c| }")
            outFile.write("\n")
            outFile.write(r"\hline")
            outFile.write("\n")
            outFile.write(r"\multicolumn{5}{ |c| }{Pixel Veto Scale Factor for " + loc + " " + base +r" photons} \\")
            outFile.write("\n")
            outFile.write(r"\hline")
            outFile.write("\n")

            # column headers: | pT Range | nominal+/-unc | uncA uncB uncC uncD |
            outFile.write(r"$p_{T}$ Range (GeV) & Nominal & \multicolumn{3}{ |c| }{Relative Uncertainty (\%)} \\")
            outFile.write("\n")
            outFile.write(r" & & SF & Data Eff. & MC Eff \\")
            outFile.write(r"\hline")
            outFile.write("\n")

            for iB, ptCut in enumerate(PhotonPtSels):
                # string formatting to make pT label look nice
                if 'Inclusive' in ptCut:
                    ptString = 'Inclusive'
                    outFile.write(r"\hline")
                    outFile.write("\n")

                else:
                    lowEdge = ptCut.split('t')[2]
                    highEdge = ptCut.split('to')[-1]
                    if highEdge == 'Inf':
                        highEdge = r'$\infty$'

                    ptString = ' (' + lowEdge +', ' + highEdge +') '

                sf = scalefactors[loc][base][metCut][ptCut]
                print sf

                # fill in row with sf / uncertainty values properly
                nomString = '$%.3f \\pm %.3f$' % tuple(sf[:2])
                systString = '%.2f & %.2f & %.2f' % (sf[1] / sf[0] * 100., sf[2] * 100., sf[3] * 100.)
                rowString = ptString + ' & ' + nomString + ' & ' + systString + r' \\'

                outFile.write(rowString)
                outFile.write('\n')

            # end table
            outFile.write(r"\hline")
            outFile.write("\n")
            outFile.write(r"\end{tabular}")
            outFile.write("\n")

            # end tex file
            outFile.write(r"\end{document}")
            outFile.close()

            # convert tex to pdf
            pdflatex = Popen( ["pdflatex",outFilePath,"-interaction nonstopmode"]
                              ,stdout=PIPE,stderr=PIPE,cwd=outDir)
            pdfout = pdflatex.communicate()
            print pdfout[0]
            if not pdfout[1] == "":
                print pdfout[1]

            # convert tex/pdf to png
            convert = Popen( ["convert",outFilePath.replace(".tex",".pdf")
                              ,outFilePath.replace(".tex",".png") ]
                             ,stdout=PIPE,stderr=PIPE,cwd=outDir)
            conout = convert.communicate()
            print conout[0]
            if not conout[1] == "":
                print conout[1]    
