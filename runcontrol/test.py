import GlibProgram
import time
import pythonlib.PowerSupply as PowerSupply


# Create an instance of the Glib control program and tell it the XDAQ
# configuration file to use.
program=GlibProgram.GlibProgram( "analysisTest.xml" )
# Create an instance of the program that controls the external power supply
# that supplies the voltage for the comparator threshold.
supply=PowerSupply.PowerSupply(verbose=False)


supply.setOutput(voltage=0)
supply.setOn()

events=1000
rate=32

# For testing just look at [min, halfway, max] comparator thresholds as
# a proof of concept.
numberOfMeasurements=3
voltages=[ voltageStep*5.0/(numberOfMeasurements-1.0) for voltageStep in range(0,numberOfMeasurements)]


# Loop over all of the specified voltages for the external power supply
for index in range(0,len(voltages)):
	supply.setOutput( voltage=voltages[index] )
	print "External voltage for comparator has been set to "+str(supply.getOutput()['voltage'])
	
	# Currently can't get XDAQ to play nicely so have to destroy the processes and
	# recreate them at the start of each run. The CMSSW modules have been written
	# to save state to disk and reload at the start of each run to get around this. 
	program.startAllProcesses()
	print "Waiting for processes to start"
	program.waitUntilAllProcessesStarted(60) # wait 60 seconds or until all processes have started
	print "Initialising"
	program.initialise()

	print "Configuring for "+str(events)+" events at "+str(rate)+"Hz"
	program.configure( triggerRate=rate, numberOfEvents=events )
	print "Enabling"
	program.enable()

	program.streamer.startRecording()
	
	# Sleep until data has finished being taken
	print "Taking data"
	while program.streamer.acquisitionState()!="Stopped":
		time.sleep(2)
	
	# Decide whether to tell XDAQ that just the run has finished ("Stop")
	# or if the whole job has finished ("Halt")
	if index==len(voltages)-1:
		print "Job finished. Halting"
		program.halt()
	else:
		print "Stopping the run ready for another"
		program.stop()

	raw_input("Press <enter> to kill the processes and start the next run")
	print "Killing the processes"
	program.killAllProcesses()
	program.waitUntilAllProcessesKilled(30)


# Put the power supply in a safe state and switch it off before finishing
supply.setOutput(voltage=0)
supply.setOff()
