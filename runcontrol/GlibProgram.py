"""
Extensions to XDAQTools specific to projects running on the GLIB

Author Mark Grimes (mark.grimes@bristol.ac.uk)
Date 29/Aug/2013
"""

import XDAQTools
import time
import math
import os

class I2cRegister :
	"""
	Class to hold details about an I2C register for the CBC test stand.
	 
	Author Mark Grimes (mark.grimes@bristol.ac.uk)
	Date 08/Aug/2013
	"""
	def __init__(self,name,address,defaultValue,value) :
		self.name=name
		self.address=int(address,0)
		self.defaultValue=int(defaultValue,0)
		self.value=int(value,0)
	def writeToFile(self,file) :
		file.write( self.name.ljust(20)+hex(self.address).ljust(8)+hex(self.defaultValue).ljust(8)+hex(self.value).ljust(8)+"\n" )

class I2cChip :
	"""
	Class to hold several instances of an I2cRegister.
	@author Mark Grimes (mark.grimes@bristol.ac.uk)
	@date 08/Aug/2013
	"""
	def __init__( self, filename=None ) :
		self.registers=[]
		
		if filename!=None :
			inputFile = open(filename,'r')
			for line in inputFile.readlines() :
				if line[0]!='#' and line[0]!='*' and len(line)>0:
					splitLine = line.split()
					newRegister = I2cRegister( splitLine[0], splitLine[1], splitLine[2], splitLine[3] )
					self.addRegister( newRegister )


	def addRegister(self,register) :
		self.registers.append(register)

	def getRegister(self,registerName) :
		"""
		Returns the Register instance with the given name
		"""
		for register in self.registers :
			if register.name==registerName : return register
		# If control got this far then no register was found
		return None
	
	def setChannelTrim( self, channelNumber, value ) :
		"""
		Set the register with the name "Channel<channelNumber>" to the supplied value
		"""
		name = "Channel"+str(channelNumber)
		register = self.getRegister(name)
		if register==None : raise Exception( "Nothing known about channel "+str(channelNumber) )
		register.value=value

	def writeToFilename( self, filename ) :
		file = open( filename, 'w' )
		for register in self.registers :
			register.writeToFile(file)
		file.close()

	def writeTrimsToFilename( self, filename ) :
		file = open( filename, 'w' )
		for register in self.registers :
			if register.name[0:7]=='Channel' :register.writeToFile(file)
		file.close()


class GlibSupervisorApplication( XDAQTools.Application ) :
	def __init__( self, host=None, port=None, className=None, instance=None, I2cRegisterFilename="/home/xtaldaq/trackerDAQ-3.1/CBCDAQ/GlibSupervisor/config/CBCv1_i2cSlaveAddrTable.txt" ) :
		# Because there's a chance I might reassign the class of a base Application instance to this
		# class, I'll check and see if the base has been initialised before calling the super class
		# constructor.
		if not hasattr( self, "host" ) : super(GlibSupervisorApplication,self).__init__( host, port, className, instance )

		# Note that because of the way the GlibSupervisor is coded, if some of these are missing
		# the supervisor will crash. So always make sure all of these are included in the POST
		# request, even if they're already set at the required values.
		self.parameters = {
			'dataSize':1,
			'triggerSel':'off',  # turn off triggering from TTC
			'triggerFreq':4,     # 4 corresponds to 16Hz. Look on the webconfig to see the other values
			'continuousStorage':'on',
			'externalData':'on',
			'clockShift':'off',
			'negativeLogicStts':'off',
			'negativeLogicCbc':'on',
			'resetSelection':0,
			'triggerMode':0,
			'triggerCyclicFreq':0
		}
		self.saveParametersResource = "/urn:xdaq-application:lid="+str(self.id)+"/saveParameters"
		# See what I2C registers there are
		self.I2cChip = I2cChip(I2cRegisterFilename)
		## Parameters and resource for reading an I2C address file
		self.readI2cParameters = { 'i2CFile':I2cRegisterFilename }
		self.readI2cResource = "/urn:xdaq-application:lid="+str(self.id)+"/i2cRead"
		# The write I2C request takes no parameters, the filename has to be set
		# before hand with a read I2C request (not very RESTful but hey ho).
		self.writeI2cParameters = {}
		self.writeI2cResource = "/urn:xdaq-application:lid="+str(self.id)+"/i2cWriteFileValues"


	def configure( self, triggerRate=None ) :
		"""
		Configure the parameters on the GLIB with the values required for data taking.
		You can optionally set a trigger rate in Hz which will be rounded down to the
		nearest power of 2.
		"""
		if triggerRate!=None :
			triggerRateCode = int( math.log( triggerRate, 2 ) )
			self.parameters['triggerFreq']=triggerRateCode
		response=self.httpRequest( "POST", self.saveParametersResource, self.parameters, False )
		if response.status!= 200 : raise Exception( "GlibSupervisor.configure got the response "+str(response.status)+" - "+response.reason )
		# I'll initialise with the I2C registers set to what is required to
		# set the comparator from an external voltage.
		self.sendI2cFile( os.getenv("CMSSW_BASE")+"/src/XtalDAQ/OnlineCBCAnalyser/runcontrol/I2CValues_comparatorExternalVoltage.txt" )

	def setAllChannelTrims( self, value ) :
		"""
		Sets the trim for all channels. Note that this isn't written to the board until sendI2C is called
		"""
		for channel in range(0,128) :
			self.setChannelTrim( channel, value )
	
	def setChannelTrim( self, channel, value ) :
		"""
		Sets the trim for the specified channel. Note that this isn't written to the board until sendI2C is called
		"""
		self.I2cChip.setChannelTrim( channel, value )

	def sendI2c( self, registerNames=None ) :
		temporaryFilename = "/tmp/i2CFileToSendToBoard.txt"
		self.I2cChip.writeTrimsToFilename( temporaryFilename )
		self.sendI2cFile( temporaryFilename )

	def sendI2cFile( self, fileName ) :
		"""
		Tells the supervisor to set the I2C values that are in the file with the given filename.
		"""
		# The supervisor C++ code keeps the filename for a write in memory from the last
		# read. Not very RESTful, but there you go. So I have to do a read to set the
		# filename before I perform a write.
		self.readI2cParameters['i2CFile']=fileName
		response=self.httpRequest( "POST", self.readI2cResource, self.readI2cParameters, False )
		if response.status!= 200 : raise Exception( "GlibSupervisor.sendI2cFile during read got the response "+str(response.status)+" - "+response.reason )
		# Now that the read has set the filename, I can perform the write
		response=self.httpRequest( "GET", self.writeI2cResource, self.writeI2cParameters, False )
		if response.status!= 200 : raise Exception( "GlibSupervisor.sendI2cFile during write got the response "+str(response.status)+" - "+response.reason )

class GlibStreamerApplication( XDAQTools.Application ) :
	def __init__( self, host=None, port=None, className=None, instance=None ) :
		# Because there's a chance I might reassign the class of a base Application instance to this
		# class, I'll check and see if the base has been initialised before calling the super class
		# constructor.
		if not hasattr( self, "host" ) : super(GlibStreamerApplication,self).__init__( host, port, className, instance )
		# Now do the stuff specific to this subclass
		self.parameters = {
			'destination':'',
			'sharedMem':'on',    # pass the data to the RU
			'memToFile':'off',
			'shortPause':4,      # this what the default was, so I'll leave it as is.
			'longPause':2000,    # this what the default was, so I'll leave it as is.
			'nbAcq':100,         # The number of events to take. 100 is an arbitrary testing value.
			'log':'off',         # Just controls the display on the webpage.
			'flags':'off',       # Just controls the display on the webpage.
			'dataflags':'off',   # Just controls the display on the webpage.
			'counters':'off',    # Just controls the display on the webpage.
			'hardwareCounter':'off',
			'simulated':'off',
			'dataFile':''
		}
		self.headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
		self.saveParametersResource = "/urn:xdaq-application:lid="+str(self.id)+"/validParam"
		self.forceStartResource = "/urn:xdaq-application:lid="+str(self.id)+"/forceStartXgi"

	def getState(self) :
		"""
		Override of base XDAQTools.Application because GlibStreamer doesn't report it's state
		in the answer to a "ParameterQuery". This is a massive hack because it's the only way
		I know to get the state.
		"""
		try:
			# The streamer doesn't have any soap commands to query to the state of the acquisition. The
			# only external way I can find to see if data is being recorded is to check the html status
			# page. There's not a specific status display, but depending on the information shown the
			# status can be inferred.
			response=self.httpRequest( "GET", "/urn:xdaq-application:lid="+str(self.id) )
		except :
			self.connection.close() # Just in case something left it open and this method is being polled
			return "<uncontactable>"		
		try:
			# The only way I've figured out how to get this information is by using some
			# hard coded knowledge about where it's stored
			streamerState=response.fullMessage.splitlines()[19].split('>')[1].split('<')[0]
			return streamerState
		except: return "<unknown>"

	def configure( self, numberOfEvents=None ) :
		if numberOfEvents!=None : self.parameters['nbAcq']=numberOfEvents
		response=self.httpRequest( "POST", self.saveParametersResource, self.parameters, False )
		if response.status!= 200 : raise Exception( "GlibStreamer.configure got the response "+str(response.status)+" - "+response.reason )
	
	def startRecording( self ) :
		response=self.httpRequest( "GET", self.forceStartResource, {}, False )
		if response.status!= 200 : raise Exception( "GlibStreamer.startRecording got the response "+str(response.status)+" - "+response.reason )

	def acquisitionState(self):
		"""
		Reports whether data is being taken or not.
		"""
		# The streamer doesn't have any soap commands to query to the state of the acquisition. The
		# only external way I can find to see if data is being recorded is to check the html status
		# page. There's not a specific status display, but depending on the information shown the
		# status can be inferred.
		try:
			response=self.httpRequest( "GET", "/urn:xdaq-application:lid="+str(self.id) )
		except:
			self.connection.close() # Just in case something left it open and this method is being polled
			return "<uncontactable>"		
		try:			
			# The only way I've figured out how to get this information is by using some
			# hard coded knowledge what the webpage shows in different states.
			streamerStateLine=response.fullMessage.splitlines()[34]
			if streamerStateLine[8:28]=="Short pause duration":
				# The table to modify parameters is showing which means data is not being taken
				return "Stopped"
			elif streamerStateLine[8:49]=='<input type="submit" value="Start saving"':
				return "Running"
			else: return "<unknown>"
		except: return "<unknown>"
		
		

class GlibProgram( XDAQTools.Program ) :
	def __init__( self, xdaqConfigFilename ) :
		super(GlibProgram,self).__init__( xdaqConfigFilename )
		self._extendStreamerAndSupervisor()
		
	def _extendStreamerAndSupervisor( self ) :
		# The super class constructor will create all of the Context and Application instances.
		# After that I need to run through each Application and find which ones are the
		# GlibSupervisor and GlibStreamer. Once I find them, I'll change the class type to my
		# Application subclasses defined above, and keep a note of which ones they are.
		for context in self.contexts :
			for application in context.applications :
				if application.className=="GlibStreamer" :
					application.__class__=GlibStreamerApplication # Change the class type to my extension
					application.__init__() # Call the constructor. A check is made to not reinitialise the base.
					self.streamer=application # Make a note so I can access it easily later
				elif application.className=="GlibSupervisor" :
					application.__class__=GlibSupervisorApplication # Change the class type to my extension
					application.__init__() # Call the constructor. A check is made to not reinitialise the base.
					self.supervisor=application # Make a note so I can access it easily later

	def reloadXDAQConfig( self ) :
		del self.streamer
		del self.supervisor
		super(GlibProgram,self).reloadXDAQConfig()
		self._extendStreamerAndSupervisor()
		
	def initialise( self, timeout=5.0 ) :
		"""
		Starts the initialise process. If "timeout" is positive then control will block
		until all the applications have reached the required state, or until "timeout"
		seconds have passed.
		"""
		self.sendAllMatchingApplicationsCommand( "Initialise", "TrackerManager" )
		self.sendAllMatchingApplicationsCommand( "Configure", "pt::atcp::PeerTransportATCP" )
		self.sendAllMatchingApplicationsCommand( "Enable", "pt::atcp::PeerTransportATCP" )
						
		self.sendAllMatchingApplicationsCommand( "Configure", "rubuilder::evm::Application" )
		self.sendAllMatchingApplicationsCommand( "Configure", "rubuilder::ru::Application" )
		self.sendAllMatchingApplicationsCommand( "Configure", "rubuilder::bu::Application" )
		self.sendAllMatchingApplicationsCommand( "Configure", "evf::FUEventProcessor" )
		self.sendAllMatchingApplicationsCommand( "Configure", "evf::FUResourceBroker" )
		self.sendAllMatchingApplicationsCommand( "Configure", "StorageManager" )

		self.sendAllMatchingApplicationsCommand( "Initialise", "GlibSupervisor" )


		startTime=time.time() # Since they don't run concurrently, I need to subtract previous waits
		self.waitAllMatchingApplicationsForState( "Ready", timeout, "rubuilder::evm::Application" )
		self.sendAllMatchingApplicationsCommand( "Enable", "rubuilder::evm::Application" )
		
		self.waitAllMatchingApplicationsForState( "Ready", timeout-(time.time()-startTime), "rubuilder::ru::Application" )
		self.sendAllMatchingApplicationsCommand( "Enable", "rubuilder::ru::Application" )

		self.waitAllMatchingApplicationsForState( "Ready", timeout-(time.time()-startTime), "rubuilder::bu::Application" )
		self.sendAllMatchingApplicationsCommand( "Enable", "rubuilder::bu::Application" )

		if timeout>0:
			self.waitAllMatchingApplicationsForState( "Halted", timeout, "TrackerManager" )
			self.waitAllMatchingApplicationsForState( "Halted", timeout-(time.time()-startTime), "GlibSupervisor" )
			self.waitAllMatchingApplicationsForState( "Enabled", timeout-(time.time()-startTime), "rubuilder::evm::Application" )
			self.waitAllMatchingApplicationsForState( "Enabled", timeout-(time.time()-startTime), "rubuilder::ru::Application" )
			self.waitAllMatchingApplicationsForState( "Enabled", timeout-(time.time()-startTime), "rubuilder::bu::Application" )
#			self.waitAllMatchingApplicationsForState( "Ready", timeout-(time.time()-startTime), "rubuilder::evm::Application" )
#			self.waitAllMatchingApplicationsForState( "Ready", timeout-(time.time()-startTime), "rubuilder::ru::Application" )
#			self.waitAllMatchingApplicationsForState( "Ready", timeout-(time.time()-startTime), "rubuilder::bu::Application" )
			self.waitAllMatchingApplicationsForState( "Ready", timeout-(time.time()-startTime), "evf::FUEventProcessor" )
			self.waitAllMatchingApplicationsForState( "Ready", timeout-(time.time()-startTime), "evf::FUResourceBroker" )
			self.waitAllMatchingApplicationsForState( "Ready", timeout-(time.time()-startTime), "StorageManager" )
			self.waitAllMatchingApplicationsForState( "Enabled", timeout-(time.time()-startTime), "pt::atcp::PeerTransportATCP" )
		
	def configure( self, triggerRate=16, numberOfEvents=100, timeout=5.0 ) :
		self.supervisor.configure(triggerRate)
		self.streamer.configure(numberOfEvents)
		self.sendAllMatchingApplicationsCommand( "Configure", "GlibSupervisor" )
		self.sendAllMatchingApplicationsCommand( "Configure", "TrackerManager" )
		
		if timeout>0:
			startTime=time.time() # Since they don't run concurrently, I need to subtract previous waits
			self.waitAllMatchingApplicationsForState( "Configured", timeout, "TrackerManager" )
			self.waitAllMatchingApplicationsForState( "Configured", timeout-(time.time()-startTime), "GlibSupervisor" )
		
		

	def enable( self, timeout=5.0 ) :
		self.sendAllMatchingApplicationsCommand( "Enable", "GlibSupervisor" )
		self.sendAllMatchingApplicationsCommand( "Enable", "TrackerManager" )
		self.sendAllMatchingApplicationsCommand( "Enable", "evf::FUEventProcessor" )
		self.sendAllMatchingApplicationsCommand( "Enable", "evf::FUResourceBroker" )
		self.sendAllMatchingApplicationsCommand( "start", "GlibStreamer" )
#		self.sendAllMatchingApplicationsCommand( "Enable", "rubuilder::ru::Application" )
#		self.sendAllMatchingApplicationsCommand( "Enable", "rubuilder::evm::Application" )
#		self.sendAllMatchingApplicationsCommand( "Enable", "rubuilder::bu::Application" )
		self.sendAllMatchingApplicationsCommand( "Enable", "StorageManager" )

		if timeout>0:
			startTime=time.time() # Since they don't run concurrently, I need to subtract previous waits
			self.waitAllMatchingApplicationsForState( "Enabled", timeout, "TrackerManager" )
			self.waitAllMatchingApplicationsForState( "Enabled", timeout-(time.time()-startTime), "GlibSupervisor" )
			self.waitAllMatchingApplicationsForState( "Enabled", timeout-(time.time()-startTime), "evf::FUEventProcessor" )
			self.waitAllMatchingApplicationsForState( "Enabled", timeout-(time.time()-startTime), "evf::FUResourceBroker" )
			self.waitAllMatchingApplicationsForState( "Enabled", timeout-(time.time()-startTime), "rubuilder::ru::Application" )
			self.waitAllMatchingApplicationsForState( "Enabled", timeout-(time.time()-startTime), "rubuilder::evm::Application" )
			self.waitAllMatchingApplicationsForState( "Enabled", timeout-(time.time()-startTime), "rubuilder::bu::Application" )
			self.waitAllMatchingApplicationsForState( "Enabled", timeout-(time.time()-startTime), "StorageManager" )
		
	def stop( self, timeout=5.0 ) :
		self.sendAllMatchingApplicationsCommand( "stop", "GlibStreamer" )
		self.sendAllMatchingApplicationsCommand( "Stop", "GlibSupervisor" )
		self.sendAllMatchingApplicationsCommand( "Stop", "TrackerManager" )
		self.sendAllMatchingApplicationsCommand( "Stop", "rubuilder::ru::Application" )
		self.sendAllMatchingApplicationsCommand( "Stop", "rubuilder::evm::Application" )
		self.sendAllMatchingApplicationsCommand( "Stop", "rubuilder::bu::Application" )
		self.sendAllMatchingApplicationsCommand( "Stop", "evf::FUEventProcessor" )
		self.sendAllMatchingApplicationsCommand( "Stop", "evf::FUResourceBroker" )
		self.sendAllMatchingApplicationsCommand( "Stop", "StorageManager" )

		startTime=time.time() # Since they don't run concurrently, I need to subtract previous waits
		self.waitAllMatchingApplicationsForState( "PrePaused", timeout, "TrackerManager" )
		self.sendAllMatchingApplicationsCommand( "PostStop", "TrackerManager" )

		if timeout>0:
			self.waitAllMatchingApplicationsForState( "Configured", timeout, "TrackerManager" )
			self.waitAllMatchingApplicationsForState( "Configured", timeout-(time.time()-startTime), "GlibSupervisor" )
			self.waitAllMatchingApplicationsForState( "Ready", timeout-(time.time()-startTime), "rubuilder::ru::Application" )
			self.waitAllMatchingApplicationsForState( "Ready", timeout-(time.time()-startTime), "rubuilder::evm::Application" )
			self.waitAllMatchingApplicationsForState( "Ready", timeout-(time.time()-startTime), "rubuilder::bu::Application" )
			self.waitAllMatchingApplicationsForState( "Ready", timeout-(time.time()-startTime), "evf::FUEventProcessor" )
			self.waitAllMatchingApplicationsForState( "Ready", timeout-(time.time()-startTime), "evf::FUResourceBroker" )
			self.waitAllMatchingApplicationsForState( "Ready", timeout-(time.time()-startTime), "StorageManager" )

	def halt( self, timeout=5.0 ) :
		self.sendAllMatchingApplicationsCommand( "stop", "GlibStreamer" )
		self.sendAllMatchingApplicationsCommand( "Halt", "GlibSupervisor" )
		self.sendAllMatchingApplicationsCommand( "Halt", "TrackerManager" )
		self.sendAllMatchingApplicationsCommand( "Halt", "rubuilder::ru::Application" )
		self.sendAllMatchingApplicationsCommand( "Halt", "rubuilder::evm::Application" )
		self.sendAllMatchingApplicationsCommand( "Halt", "rubuilder::bu::Application" )
		self.sendAllMatchingApplicationsCommand( "Halt", "evf::FUEventProcessor" )
		self.sendAllMatchingApplicationsCommand( "Halt", "evf::FUResourceBroker" )
		self.sendAllMatchingApplicationsCommand( "Halt", "StorageManager" )

		startTime=time.time() # Since they don't run concurrently, I need to subtract previous waits
		self.waitAllMatchingApplicationsForState( "PrePaused", timeout, "TrackerManager" )
		self.sendAllMatchingApplicationsCommand( "PostHalt", "TrackerManager" )

		if timeout>0:
			self.waitAllMatchingApplicationsForState( "Halted", timeout, "TrackerManager" )
			self.waitAllMatchingApplicationsForState( "Halted", timeout-(time.time()-startTime), "GlibSupervisor" )
			self.waitAllMatchingApplicationsForState( "Halted", timeout-(time.time()-startTime), "evf::FUEventProcessor" )
			self.waitAllMatchingApplicationsForState( "Halted", timeout-(time.time()-startTime), "evf::FUResourceBroker" )
			self.waitAllMatchingApplicationsForState( "Halted", timeout-(time.time()-startTime), "rubuilder::evm::Application" )
			self.waitAllMatchingApplicationsForState( "Halted", timeout-(time.time()-startTime), "rubuilder::ru::Application" )
			self.waitAllMatchingApplicationsForState( "Halted", timeout-(time.time()-startTime), "rubuilder::bu::Application" )
			self.waitAllMatchingApplicationsForState( "Halted", timeout-(time.time()-startTime), "StorageManager" )
