from ROOT import TFile, TEfficiency, TCanvas, gStyle, gROOT
import sys



if len(sys.argv) != 2 : raise Exception('Incorrect number of arguments. The histogram filename should be the only argument')
inputFilename=sys.argv[1]

inputFile=TFile.Open(inputFilename)

#gStyle.SetOptStat('')
print gStyle.GetOptFit()
gStyle.SetOptFit(1100)
print gStyle.GetOptFit()

canvas=[]
print gStyle.GetOptFit()
for cbcNumber in range(0,1) :
	print 'CBC Number :',cbcNumber,gStyle.GetOptFit()
	canvas.append( TCanvas() )
	print gStyle.GetOptFit()
	for channelNumber in range(0,1): #range(0,254) :
		print channelNumber,gStyle.GetOptFit()
		path="/CBC %02d/Strip %03d"%(cbcNumber, channelNumber)
		efficiency=inputFile.Get(path)
		print gStyle.GetOptFit()
		if efficiency!=None :
			#print "Drawing histogram '"+path+"'"
			if channelNumber==0 :
				# Change the title, since all plots will use it
				print 'Drawing first'
				efficiency.SetTitle("CBC "+str(cbcNumber))
				#efficiency.Draw()
			else : efficiency.Draw("same")
			
			#paintedHistogram=efficiency.GetPaintedGraph()
			#if paintedHistogram!=None : print "Got painted histogram"
			#else : print "Couldn't get the painted histogram"
			#stats = canvas[-1].GetPrimitive("stats")
			#stats.SetY1NDC(.4);
			#stats.SetY2NDC(.6);

		else : print "Couldn't get histogram '"+path+"'"
print gStyle.GetOptFit()
raw_input("Waiting")
