import GlibProgram
import time

program=GlibProgram.GlibProgram( "analysisTest.xml" )

program.startAllProcesses()
print "Waiting for processes to start"
program.waitUntilAllProcessesStarted(60) # wait 60 seconds or until all processes have started
print "Initialising"
program.initialise()
print "Configuring"
program.configure(1,20)

#delay=60
#
#trims = range(0,256,10)
#
#for trimIndex in range(0,len(trims)) :
#
#	program.startAllProcesses()
#	print "Waiting for processes to start"
#	program.waitUntilAllProcessesStarted(60) # wait 60 seconds or until all processes have started
#	print "Initialising"
#	program.initialise()
#
#	program.supervisor.setAllChannelTrims( 0 )
#	program.supervisor.setChannelTrim( 63, trims[trimIndex] )
#	program.supervisor.sendI2c()
#
#	print "Configuring"
#	program.configure()
#	print "Enabling"
#	program.enable()
#
#	program.streamer.startRecording()
#	
#	print "Taking data"
#	while program.streamer.acquisitionState()!="Stopped":
#		time.sleep(2)
#	
#	if trimIndex==len(trims)-1:
#		print "Halting"
#		program.halt()
#	else:
#		print "Stopping"
#		program.stop()
#
#	#raw_input("Press <enter> to kill the processes and start the next run")
#	print "Killing the processes"
#	program.killAllProcesses()
#	program.waitUntilAllProcessesKilled(30)
