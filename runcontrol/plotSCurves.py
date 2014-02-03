from ROOT import TFile, TEfficiency, TCanvas, gStyle, gROOT
import sys



if len(sys.argv) != 3 : raise Exception('Incorrect number of arguments. The histogram filename should be the only argument')
inputFilename=sys.argv[2]

inputFile=TFile.Open(inputFilename)

gStyle.SetOptStat('')
gStyle.SetOptFit(0)

canvas=[]
for cbcNumber in range(0,1) :
	canvas.append( TCanvas() )
	for channelNumber in range(0,254) :
		path="/CBC %02d/Strip %03d"%(cbcNumber, channelNumber)
		efficiency=inputFile.Get(path)
		if efficiency!=None :
			#print "Drawing histogram '"+path+"'"
			if channelNumber==0 :
				# Change the title, since all plots will use it
				efficiency.SetTitle("CBC "+str(cbcNumber))
				efficiency.Draw()
			else : efficiency.Draw("same")
			
			#paintedHistogram=efficiency.GetPaintedGraph()
			#if paintedHistogram!=None : print "Got painted histogram"
			#else : print "Couldn't get the painted histogram"
			#stats = canvas[-1].GetPrimitive("stats")
			#stats.SetY1NDC(.4);
			#stats.SetY2NDC(.6);

		else : print "Couldn't get histogram '"+path+"'"

canvas[0].SaveAs( "/tmp/histogramForCBC0.png" )
