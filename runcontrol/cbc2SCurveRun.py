"""
@brief Example of how to do an SCurve run.

There are two main components: daqProgram which controls the data aquasition by
communicating with XDAQ; and analysisControl which controls the data analysis
by communicating with the C++ code.

The two are pretty much completely separate. To date I haven't been able to get
the full DAQ chain running so that the C++ code can run online, hence why the
code is run by communicating to a server. When analysisControl is created, if
the C++ server is not running it will be started.

Since they're both separate, they need to be told individually what to do. Each
one is told the current threshold, then daqProgram is told where to save the file.
analysisControl is then told to analyse the output file. This process is repeated
for however many thresholds are required, and then at the end analysisControl is
told to save the histograms to an output file.

@author Mark Grimes (mark.grimes@bristol.ac.uk)
@date 06/Jan/2014
"""

from pythonlib.SimpleGlibProgram import SimpleGlibProgram
from pythonlib.AnalyserControl import AnalyserControl
import time

def cbc2SCurveRun( daqProgram, analysisControl, thresholds, temporaryOutputFilename="/tmp/cbc2SCurveRun_OutputFile.dat", silent=False ) :
	daqProgram.startAllProcesses( forceRestart=True ) # forceRestart will kill the XDAQ processes first if they're running
	daqProgram.waitUntilAllProcessesStarted();
	daqProgram.initialise()
	daqProgram.setOutputFilename( temporaryOutputFilename )
	
	
	#
	# Pause execution and make any additional changes to the configuration here if
	# you want to. You can use the hyperdaq interface, and the changes will be sent
	# to the board when configure() is called.
	# Note that GlibSupervisor will reset the CBC I2C registers when it configures,
	# so save any of that configuration until afterwards.
	#
	
	daqProgram.configure()
	
	for threshold in thresholds :
		daqProgram.setAndSendI2c( { "VCth" : threshold } )
		analysisControl.setThreshold( threshold )
	
		daqProgram.play()
		if not silent : print "Taking data at threshold "+str(threshold)
		while daqProgram.streamer.acquisitionState()!="Stopped":
			time.sleep(2)
		
		daqProgram.pause()
		analysisControl.analyseFile( temporaryOutputFilename )
	
	
	daqProgram.killAllProcesses()
	daqProgram.waitUntilAllProcessesKilled();

if __name__ == '__main__':
	daqProgram = SimpleGlibProgram( "GlibSuper.xml" )
	analysisControl = AnalyserControl( "127.0.0.1", "50000" )
	cbc2SCurveRun( daqProgram, analysisControl, range(100,150) )
	analysisControl.saveHistograms( "/tmp/histograms.root" )
	print "Histograms saved to '/tmp/histograms.root'"
