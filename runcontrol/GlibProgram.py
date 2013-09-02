"""
Extensions to XDAQTools specific to projects running on the GLIB

Author Mark Grimes (mark.grimes@bristol.ac.uk)
Date 29/Aug/2013
"""

import XDAQTools

class GlibSupervisorApplication( XDAQTools.Application ) :
	def __init__( self, host=None, port=None, className=None, instance=None ) :
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
		self.saveParametersResource = "/urn:xdaq-application:lid=30/saveParameters"
		## Parameters and resource for reading an I2C address file
		#self.readI2cParameters = { 'i2CFile':I2cRegisterFilename }
		#self.readI2cResource = "/urn:xdaq-application:lid=30/i2cRead"
		# The write I2C request takes no parameters, the filename has to be set
		# before hand with a read I2C request (not very RESTful but hey ho).
		self.writeI2cParameters = {}
		self.writeI2cResource = "/urn:xdaq-application:lid=30/i2cWriteFileValues"

	def configure( self, triggerRate=None ) :
		"""
		Configure the parameters on the GLIB with the values required for data taking.
		You can optionally set a trigger rate in Hz which will be rounded down to the
		nearest power of 2.
		"""
		if triggerRate!=None :
			triggerRateCode = int( math.log( triggerRate, 2 ) )
			self.parameters['triggerFreq']=triggerRateCode
		response=self.httpRequest( "POST", self.saveParametersResource, self.parameters )
		if response.status!= 200 : raise Exception( "GlibSupervisor.configure got the response "+str(response.status)+" - "+response.reason )

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
		self.saveParametersResource = "/urn:xdaq-application:lid=200/validParam"
		self.forceStartResource = "/urn:xdaq-application:lid=200/forceStartXgi"
	
	def configure( self, numberOfEvents=None ) :
		if numberOfEvents!=None : self.parameters['nbAcq']=numberOfEvents
		response=self.httpRequest( "POST", self.saveParametersResource, self.parameters )
		if response.status!= 200 : raise Exception( "GlibStreamer.configure got the response "+str(response.status)+" - "+response.reason )
	
	def startRecording( self ) :
		self.connection.connect()
		response=self.httpRequest( "GET", self.forceStartResource )
		if response.status!= 200 : raise Exception( "GlibStreamer.startRecording got the response "+str(response.status)+" - "+response.reason )

class GlibProgram( XDAQTools.Program ) :
	def __init__( self, xdaqConfigFilename ) :
		super(GlibProgram,self).__init__( xdaqConfigFilename )
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

	def initialise(self) :
		self.sendAllMatchingApplicationsCommand( "Initialise", "TrackerManager" )
		self.sendAllMatchingApplicationsCommand( "Configure", "pt::atcp::PeerTransportATCP" )
		self.sendAllMatchingApplicationsCommand( "Enable", "pt::atcp::PeerTransportATCP" )
						
		self.sendAllMatchingApplicationsCommand( "Configure", "rubuilder::evm::Application" )
		self.sendAllMatchingApplicationsCommand( "Configure", "rubuilder::ru::Application" )
		self.sendAllMatchingApplicationsCommand( "Configure", "rubuilder::bu::Application" )
		self.sendAllMatchingApplicationsCommand( "Configure", "StorageManager" )
		self.sendAllMatchingApplicationsCommand( "Configure", "evf::FUEventProcessor" )
		self.sendAllMatchingApplicationsCommand( "Configure", "evf::FUResourceBroker" )

		self.sendAllMatchingApplicationsCommand( "Initialise", "GlibSupervisor" )

		self.sendAllMatchingApplicationsCommand( "Enable", "rubuilder::evm::Application" )
		self.sendAllMatchingApplicationsCommand( "Enable", "rubuilder::ru::Application" )
		self.sendAllMatchingApplicationsCommand( "Enable", "rubuilder::bu::Application" )
		self.sendAllMatchingApplicationsCommand( "Enable", "StorageManager" )

	def configure(self) :
		self.supervisor.configure()
		self.streamer.configure()
		self.sendAllMatchingApplicationsCommand( "Configure", "GlibSupervisor" )
		self.sendAllMatchingApplicationsCommand( "Configure", "TrackerManager" )

	def enable(self) :
		self.sendAllMatchingApplicationsCommand( "Enable", "GlibSupervisor" )
		self.sendAllMatchingApplicationsCommand( "Enable", "TrackerManager" )
		self.sendAllMatchingApplicationsCommand( "Enable", "evf::FUEventProcessor" )
		self.sendAllMatchingApplicationsCommand( "Enable", "evf::FUResourceBroker" )
		self.sendAllMatchingApplicationsCommand( "start", "GlibStreamer" )
		
