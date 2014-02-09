import time
import threading

class OccupancyCheck(threading.Thread) :
	"""
	Thread that will take a quick run of 100 events. Once an instance has been constructed, call
	start() to start in a separate thread. For most scripting purposes this isn't what you want;
	to run in the current thread call run().
	
	If running in a separate thread you can set the "quit" member to true and the program will
	stop whatever it's doing and finish.
	
	The statusCallback object provided in the constructor is a way for the thread to update you
	about how far through it is. It should be an object with two methods:
	@code
		currentStatus( fractionComplete, statusString )
		finished()
	@endcode
	Other scripts require a "currentStatus" method as well, but since this is such a short run
	this is not used here. The finished method is called as the last thing before the thread
	terminates.
	You can set statusCallback to None if you don't want any progress updates.
	
	daqProgram should be an instance of pythonlib.SimpleGlibProgram and analysisControl should
	be an instance of pythonlib.AnalyserControl. Reset is called on analysisControl before starting,
	so you will lose any data that was in there beforehand.
	
	@author Mark Grimes (mark.grimes@bristol.ac.uk)
	@date 07/Feb/2014
	"""
	def __init__( self, statusCallback, daqProgram, analysisControl, temporaryOutputFilename="/tmp/cbc2SCurveRun_OutputFile.dat" ) :
		super(OccupancyCheck,self).__init__()
		self.statusCallback=statusCallback
		self.daqProgram=daqProgram
		self.analysisControl=analysisControl
		self.temporaryOutputFilename=temporaryOutputFilename
		self.quit=False

	def run( self ) :
		try :
			self.analysisControl.reset() # Clear any data that was there before hand
			self.daqProgram.startAllProcesses( forceRestart=True ) # forceRestart will kill the XDAQ processes first if they're running
			self.daqProgram.waitUntilAllProcessesStarted();
			self.daqProgram.initialise()
			self.daqProgram.setOutputFilename( self.temporaryOutputFilename )
			
			self.daqProgram.configure()
			
			self.daqProgram.play()
			while (not self.quit) and self.daqProgram.streamer.acquisitionState()=="Running":
				time.sleep(2)
			
			self.daqProgram.pause()
			if not self.quit : self.analysisControl.analyseFile( self.temporaryOutputFilename )
			
			self.daqProgram.killAllProcesses()
			self.daqProgram.waitUntilAllProcessesKilled();
			# If the user wants to be update tell them we've finished.
			if self.statusCallback!=None : self.statusCallback.finished()
		except :
			# If anything ever goes wrong, shut down the XDAQ processes before propagating the exception
			self.daqProgram.killAllProcesses()
			raise

if __name__ == '__main__':
	from pythonlib.SimpleGlibProgram import SimpleGlibProgram
	from pythonlib.AnalyserControl import AnalyserControl

	# Create an object that informs the user when the run is finished
	class PrintStatus(object) :
		def finished( self ) :
			print "Finished taking data"
	
	daqProgram = SimpleGlibProgram( "GlibSuper.xml" )
	# Temporary hack. At the moment I can't get this to run as myself so I'll start
	# as the xtaldaq user
	daqProgram.contexts[0].forcedEnvironmentVariables["USER"]="xtaldaq"
	daqProgram.contexts[0].forcedEnvironmentVariables["SCRATCH"]="/tmp"
	analysisControl = AnalyserControl( "127.0.0.1", "50000" )
	
	occupancyCheckRun=OccupancyCheck( PrintStatus(), daqProgram, analysisControl )
	# I have no interest in running this in a separate thread (that's mostly for gui
	# stuff) so I'll just call the run method directly. If I wanted to start it in a
	# separate thread I'd call "start" instead.
	occupancyCheckRun.run()
	
	occupancies=analysisControl.occupancies()
	# The C++ code doesn't know which CBCs are connected. Dummy data is in the output files
	# for unconnected CBCs. I'll check which CBCs are connected and only print the data for
	# those.
	for cbcName in  daqProgram.supervisor.connectedCBCNames() :
		try :
			occupancyArray=occupancies[cbcName]
			# First print some column headers
			print "Occupancies for "+cbcName
			print "    ", # Padding to account for row names
			for index in range( 0, 16 ) :
				print "CHx%X"%index,
			row=0
			print "\nCH%Xx"%row,
			for index in range( 0, len(occupancyArray) ) :
				print "%4d"%occupancyArray[index],
				if index%16 == 15 :
					row+=1
					print "\nCH%Xx"%row,
			print "\n"
		except KeyError :
			print "No data recorded for "+cbcName