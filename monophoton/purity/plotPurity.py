import os
import sys
from pprint import pprint
from array import array
from subprocess import Popen, PIPE
import ROOT as r

basedir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if basedir not in sys.path:
    sys.path.append(basedir)
import config
from plotstyle import WEBDIR, SimpleCanvas
import selections as s

versDir = WEBDIR + '/purity/'+s.Version
outDir = os.path.join(versDir, 'Fitting')
if not os.path.exists(outDir):
    os.makedirs(outDir)

tune = 'GJetsCWIso' # 'Spring16'

outFile = r.TFile("../data/impurity_" + tune + ".root", "RECREATE")

bases = s.bases
mods = s.mods
titles = ['e/#gamma only',  'e/#gamma + pixel veto', 'e/#gamma + pixel veto + #gamma-specific'] #
PhotonIds = [base+mod for base in bases for mod in mods]
PhotonPtSels = sorted(s.PhotonPtSels.keys())[:-1]
MetSels = sorted(s.MetSels.keys())[1:2]

purities = {}
for loc in s.Locations[:1]:
    purities[loc] = {}
    for pid in PhotonIds:
        purities[loc][pid] = {}
        for ptCut in PhotonPtSels:
            purities[loc][pid][ptCut] = {}
            for metCut in MetSels:
                purities[loc][pid][ptCut][metCut] = {}
                
                dirName = tune + '_' + loc+'_'+pid+'_'+ptCut+'_'+metCut 
                resultsName = "results.out"
                condorFileName = os.path.join(versDir,dirName,resultsName)
                print condorFileName
                try:
                    condorFile = open(condorFileName)

                    match = False
                    purity = [1, 0, 0, 0, 0, 0]
                    for line in condorFile:
                        if "Nominal purity is:" in line:
                            tmp = line.split()
                            if tmp:
                                match = True
                                # pprint(tmp)
                                purity[0] = (1.0 - float(tmp[-1].strip("(),"))) * 100
                                # print purity[0]
                        elif "Total uncertainty is:" in line:
                            # print line
                            tmp = line.split()
                            if tmp:
                                match = True
                                # pprint(tmp)
                                purity[1] = float(tmp[-1].strip("(),")) * 100
                                #print purity
                        elif "Sideband uncertainty is:" in line:
                            # print line
                            tmp = line.split()
                            if tmp:
                                match = True
                                # pprint(tmp)
                                purity[2] = float(tmp[-1].strip("(),")) * 100
                                #print purity
                        elif "Method uncertainty is:" in line:
                            # print line
                            tmp = line.split()
                            if tmp:
                                match = True
                                # pprint(tmp)
                                purity[3] = float(tmp[-1].strip("(),")) * 100
                                #print purity
                        elif "Signal shape uncertainty is:" in line: # need to add t back
                            # print line
                            tmp = line.split()
                            if tmp:
                                match = True
                                # pprint(tmp)
                                purity[4] = float(tmp[-1].strip("(),")) * 100
                                #print purity
                        elif "Background stat uncertainty is:" in line:
                            # print line
                            tmp = line.split()
                            if tmp:
                                match = True
                                # pprint(tmp)
                                purity[5] = float(tmp[-1].strip("(),")) * 100
                                #print purity
                    purities[loc][pid][ptCut][metCut] = tuple(purity)

                    if not match:
                        print "No purity found for skim:", dirName
                        purities[loc][pid][ptCut][metCut] = (102.5, 0.0, 0.0, 0.0, 0.0, 0.0)

                    condorFile.close()
                except:
                    print "No purity file found for skim:", dirName
                    purities[loc][pid][ptCut][metCut] = (102.5, 0.0, 0.0, 0.0, 0.0, 0.0)
                       
pprint(purities)

canvas = SimpleCanvas(lumi = s.sphLumi)

for loc in s.Locations[:1]:
    for base in bases:
        for metCut in MetSels:
            canvas.cd()
            canvas.Clear()
            canvas.legend.Clear()
            canvas.legend.setPosition(0.25, 0.725, 0.8, 0.925)

            for iMod, mod in enumerate(mods):
                
                pGraph = r.TGraphAsymmErrors()
                pGraph.SetName(loc+'-'+base+mod+'-'+metCut)

                for iB, ptCut in enumerate(PhotonPtSels):
                    if 'Inclusive' in ptCut:
                        lowEdge = 175.
                        highEdge = 500.
                    else:
                        lowEdge = float(ptCut.split('t')[2])
                        highEdge = ptCut.split('to')[-1]
                        if highEdge == 'Inf':
                            highEdge = 500.
                        highEdge = float(highEdge)

                    center = (lowEdge + highEdge) / 2.
                    exl = center - lowEdge
                    exh = highEdge - center

                    purity = purities[loc][base+mod][ptCut][metCut]

                    pGraph.SetPoint(iB, center, purity[0])
                    pGraph.SetPointError(iB, exl, exh, purity[1], purity[1])

               #  if not 'max' in mod:
                canvas.legend.add(base+mod, title = titles[mods.index(mod)], mcolor = r.kBlue+iMod, lcolor = r.kBlue+iMod, lwidth = 2)
                canvas.legend.apply(base+mod, pGraph)
                canvas.addHistogram(pGraph, drawOpt = 'EP')

                outFile.cd()
                pGraph.Write()
                
            canvas.xlimits = (175., 500.)
            canvas.ylimits = (0.0, 10.0)
            canvas.ytitle = 'Photon Impurity (%)'
            canvas.xtitle = 'E_{T}^{#gamma} (GeV)'
            # canvas.SetGridy(True)

            plotName = 'Plot_' + tune + '_impurity_' + str(metCut) + '_' + str(loc) + '_' + str(base)
            canvas.printWeb('purity/'+s.Version+'/Fitting', plotName, logy = False)

outFile.Close()

for loc in s.Locations[:1]:
    for base in bases:
        for metCut in MetSels:
            for iMod, mod in enumerate(mods):
                
                # start new table
                purityFileName = 'table_' + tune + '_impurity_' + str(metCut) + '_' + str(loc) + '_' + str(base+mod) + '.tex'
                purityFilePath = outDir + '/' + purityFileName
                purityFile = open(purityFilePath, 'w')

                purityFile.write(r"\documentclass{article}")
                purityFile.write("\n")
                purityFile.write(r"\usepackage[paperwidth=152mm, paperheight=58mm, margin=5mm]{geometry}")
                purityFile.write("\n")
                purityFile.write(r"\begin{document}")
                purityFile.write("\n")
                purityFile.write(r"\pagenumbering{gobble}")
                purityFile.write("\n")

                # table header based on ID
                purityFile.write(r"\begin{tabular}{ |c|c|c c c c| }")
                purityFile.write("\n")
                purityFile.write(r"\hline")
                purityFile.write("\n")
                purityFile.write(r"\multicolumn{6}{ |c| }{Impurity (\%) for " + loc + " " + base+mod +r" photons in data} \\")
                purityFile.write("\n")
                purityFile.write(r"\hline")
                purityFile.write("\n")

                # column headers: | pT Range | nominal+/-unc | uncA uncB uncC uncD |
                purityFile.write(r"$p_{T}$ Range & Nominal & \multicolumn{4}{ |c| }{Sources of Systematic Uncertainty} \\")
                purityFile.write("\n")
                purityFile.write(r" (GeV) & & Sideband & CH Iso Shape & Signal Shape & Bgkd. Stats \\")
                purityFile.write("\n")
                purityFile.write(r"\hline")
                purityFile.write("\n")

                for iB, ptCut in enumerate(PhotonPtSels):

                    # start new row

                    # string formatting to make pT label look nice
                    if 'Inclusive' in ptCut:
                        ptString = 'Inclusive'
                    else:
                        lowEdge = ptCut.split('t')[2]
                        highEdge = ptCut.split('to')[-1]
                        if highEdge == 'Inf':
                            highEdge = r'$\infty$'

                        ptString = ' (' + lowEdge +', ' + highEdge +') '

                    purity = purities[loc][base+mod][ptCut][metCut]
                    print purity

                    # fill in row with purity / uncertainty values properly
                    nomString = '$%.2f \\pm %.2f$' % tuple(purity[:2])

                    systString = '%.2f & %.2f & %.2f & %.2f' % tuple(purity[2:])

                    rowString = ptString + ' & ' + nomString + ' & ' + systString + r' \\'

                    purityFile.write(rowString)
                    purityFile.write('\n')

                # end table
                purityFile.write(r"\hline")
                purityFile.write("\n")
                purityFile.write(r"\end{tabular}")
                purityFile.write("\n")
                
                # end tex file
                purityFile.write(r"\end{document}")
                purityFile.close()
    
                # convert tex to pdf
                pdflatex = Popen( ["pdflatex",purityFilePath,"-interaction nonstopmode"]
                                  ,stdout=PIPE,stderr=PIPE,cwd=outDir)
                pdfout = pdflatex.communicate()
                print pdfout[0]
                if not pdfout[1] == "":
                    print pdfout[1]

                # convert tex/pdf to png
                convert = Popen( ["convert",purityFilePath.replace(".tex",".pdf")
                                  ,purityFilePath.replace(".tex",".png") ]
                                 ,stdout=PIPE,stderr=PIPE,cwd=outDir)
                conout = convert.communicate()
                print conout[0]
                if not conout[1] == "":
                    print conout[1]    
    
