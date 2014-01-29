"""
Example of how to do an SCurve run. The standaloneCBCAnalyser executable needs to already be running
on port 50000 before this script starts. To make sure it's working properly go to
http://127.0.0.1:50000 in a webbrowser and make sure you can see the instruction page.

@author Mark Grimes (mark.grimes@bristol.ac.uk)
@date 06/Jan/2014
"""

import SimpleGlibRun, time

daqProgram = SimpleGlibRun.SimpleGlibProgram( "GlibSuper.xml" )
analysisControl = SimpleGlibRun.AnalyserControl( "127.0.0.1", "50000" )


daqProgram.startAllProcesses();
daqProgram.waitUntilAllProcessesStarted();
daqProgram.initialise()
daqProgram.setOutputFilename( "/tmp/scurveOutputFile.dat" )


#
# Pause execution and make any additional changes to the configuration here if
# you want to. You can use the hyperdaq interface, and the changes will be sent
# to the board when configure() is called.
# Note that GlibSupervisor will reset the CBC I2C registers when it configures,
# so save any of that configuration until afterwards.
#

daqProgram.configure()

for threshold in range(100,151) :
	print "Setting threshold to: "+str(threshold)
	daqProgram.setAndSendI2c( { "VCth" : threshold } )
	analysisControl.setThreshold( threshold )

	daqProgram.play()
	print "Taking data"
	while daqProgram.streamer.acquisitionState()!="Stopped":
		time.sleep(2)
	
	daqProgram.pause()
	analysisControl.analyseFile( "/tmp/scurveOutputFile.dat" )

analysisControl.saveHistograms( "/tmp/histograms.root" )
daqProgram.killAllProcesses()
daqProgram.waitUntilAllProcessesKilled();
