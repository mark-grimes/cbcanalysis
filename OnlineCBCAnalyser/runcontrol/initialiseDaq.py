# Python file which basically follows the example on http://sbgcmstrackerupgrade.in2p3.fr/, but
# uses a real board and adds some HTTP requests to configure the GlibStreamer and GlibSupervisor.
# Once everything is set up also sends a HTTP request for "Force BG0-START detection" which starts
# the chain taking data.
#
# @author Mark Grimes (mark.grimes@bristol.ac.uk)
# @date 31/Jul/2013

import bristolTestStand
import xdglib
import time

supervisor = bristolTestStand.GlibSupervisor()
streamer = bristolTestStand.GlibStreamer()


s=xdglib.IlcSetup("onlineAnalysis.xml")


# First set all of the trims to 0
s.CreateExecutives()
s.Initialise()
supervisor.configure()
supervisor.setAndSendI2c("Icomp",255)
supervisor.setAllChannelTrims(0)
supervisor.sendI2c()
s.DestroyExecutives()
del s


triggerCode=5
events=100

eventsPerSecond=2**triggerCode
delay=9+float(events)/float(eventsPerSecond) *1.5 # add arbitrary 50% extra delay for safety
delay=100

time.sleep(3)

# Then loop over one of the channels and increase that trim slowly
for trim in [0,255]:#range(0,256) :
	s=xdglib.IlcSetup("/home/xtaldaq/trackerDAQ-3.1/CBCDAQ/GlibSupervisor/xml/onlineAnalysis.xml")
	s.CreateExecutives()
	s.Initialise()
	supervisor.configure(triggerRate=triggerCode)
	supervisor.setChannelTrim( 63, trim )
	supervisor.sendI2c()

	s.Configure()
	streamer.configure(numberOfEvents=events)
	s.Enable()

	streamer.startRecording()
	print "Sleeping for "+str(delay)+" seconds while taking data"
	time.sleep(delay)
	
	#xdglib.sendSOAPCommand( 'localhost', 10005, 'evf::FUEventProcessor', 1, 'Halt' )
	xdglib.sendSOAPCommand( 'localhost', 10003, 'evf::FUResourceBroker', 0, 'Halt' )
	time.sleep(5)
	
	s.DestroyExecutives()
	del s
	time.sleep(5)
	

