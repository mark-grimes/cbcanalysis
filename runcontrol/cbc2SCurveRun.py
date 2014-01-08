"""
Example of how to do an SCurve run. The standaloneCBCAnalyser executable needs to already be running
on port 50000 before this script starts. To make sure it's working properly go to
http://127.0.0.1:50000 in a webbrowser and make sure you can see the instruction page.

@author Mark Grimes (mark.grimes@bristol.ac.uk)
@date 06/Jan/2014
"""

import SimpleGlibRun

daqProgram = SimpleGlibRun.SimpleGlibProgram( "/home/xtaldaq/trackerDAQ-3.2/CBCDAQ/GlibSupervisor/xml/GlibSuper.xml" )
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

#
# Now change the CBC I2C registers as required.
#

