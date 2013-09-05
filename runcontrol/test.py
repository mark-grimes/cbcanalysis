import GlibProgram
import time

program=GlibProgram.GlibProgram( "analysisTest.xml" )


delay=60

for trim in [0,63,127,191,255]:#range(0,256) :
	
	program.startAllProcesses()
	print "Waiting for processes to start"
	program.waitUntilAllProcessesStarted(60) # wait 60 seconds or until all processes have started
	print "Acquisition state="+program.streamer.acquisitionState()
	print "Initialising"
	program.initialise()
	print "Acquisition state="+program.streamer.acquisitionState()

	#program.supervisor.setChannelTrim( 63, trim )
	#program.supervisor.sendI2c()

	print "Configuring"
	program.configure()
	print "Acquisition state="+program.streamer.acquisitionState()
	print "Enabling"
	program.enable()
	print "Acquisition state="+program.streamer.acquisitionState()

	program.streamer.startRecording()
	print "Sleeping for "+str(delay)+" seconds while taking data"
	time.sleep(1)
	print "Acquisition state="+program.streamer.acquisitionState()
	time.sleep(1)
	print "Acquisition state="+program.streamer.acquisitionState()
	time.sleep(delay)
	
	if trim==255:
		print "Halting"
		program.halt()
	else:
		print "Stopping"
		program.stop()

	print "Killing the processes"
	program.killAllProcesses()
	program.waitUntilAllProcessesKilled(30)
