"""
Extensions to XDAQTools specific to projects running on the GLIB. This script is intended to
use a simple XDAQ setup with just the GlibStreamer and GlibSupervisor. These will be configured
to dump a temporary file and the standaloneCBCAnalyser program will be instructed to analyse it.

SimpleGlibProgram is class that controls the DAQ side of things, AnalyserControl is a class that
communicates with the standaloneCBCAnalyser program and tells it what to do.

At the moment standaloneCBCAnalyser is not started automatically, so it has to be started externally.

Author Mark Grimes (mark.grimes@bristol.ac.uk)
Date 06/Jan/2014
"""


import XDAQTools, time, math, httplib, urllib, os, json, re

class I2cRegister :
	"""
	Class to hold details about an I2C register for the CBC test stand.
	 
	Author Mark Grimes (mark.grimes@bristol.ac.uk)
	Date 08/Aug/2013
	"""
	def __init__(self,name,page,address,defaultValue,value) :
		self.name=name
		self.page=int(page,0)
		self.address=int(address,0)
		self.defaultValue=int(defaultValue,0)
		self.value=int(value,0)
	def __repr__(self) :
		return "<I2cRegister "+self.name+", "+hex(self.value)+">"
	def writeToFile(self,file) :
		file.write( self.name.ljust(20)+hex(self.page).ljust(8)+hex(self.address).ljust(8)+hex(self.defaultValue).ljust(8)+hex(self.value).ljust(8)+"\n" )

class I2cChip :
	"""
	Class to hold several instances of an I2cRegister.
	@author Mark Grimes (mark.grimes@bristol.ac.uk)
	@date 08/Aug/2013
	"""
	def __init__( self, filename=None ) :
		self.registers=[]
		if filename!=None : self.loadFromFile(filename)

	def loadFromFile( self, filename ) :
		"""
		Loads information about register names, addresses and values from the provided text file.
		Overwrites any registers that were present before, but leaves ones not mentioned in the
		text file alone.
		"""
		inputFile = open(filename,'r')
		for line in inputFile.readlines() :
			# Take everything before any comments (comments start with either '#' or '*'
			# and continue until the end of the line).
			lineNoComments=line.split('#')[0]
			lineNoComments=lineNoComments.split('*')[0]
			if len(lineNoComments)>0:
				splitLine = lineNoComments.split()
				if len(splitLine) != 5 : raise Exception("I2C file appears to be in an incorrect format. Line '"+line+"' should split into 5 columns")
				newRegister = I2cRegister( splitLine[0], splitLine[1], splitLine[2], splitLine[3], splitLine[4] )
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
	
	def getValues(self,registerNames=None) :
		"""
		Returns the value of each register in {"<name>": <value>, ...} tuple form. If an array of
		registerNames is specified only those are returned.
		"""
		returnValue = {}
		for register in self.registers :
			addThisValue=True
			if registerNames!=None :
				if registerNames.count(register.name)==0 : addThisValue=False
			if addThisValue : returnValue[register.name]=register.value
		return returnValue
	
	def setChannelTrim( self, channelNumber, value ) :
		"""
		Set the register with the name "Channel<channelNumber+1>" to the supplied value.
		
		Note that the argument starts counting from zero, whereas the register string
		name starts counting from 1. So calling setChannelTrim( 23, <value> ) will
		change the register named "Channel024". This is because all other code regarding
		channels starts counting from zero.
		"""
		# I don't know of the channel numbers are padded with zeros in the register
		# name, so I'll try a few possibilities
		possibleNames = [ "Channel%d"%(channelNumber+1), "Channel%02d"%(channelNumber+1), "Channel%03d"%(channelNumber+1) ]
		for name in possibleNames :
			register = self.getRegister(name)
		if register==None :
			raise Exception( "Nothing known about channel "+str(channelNumber) )
		register.value=value

	def getChannelTrim( self, channelNumber ) :
		"""
		Returns the value in register "Channel<channelNumber+1>".
		
		Note that the argument starts counting from zero, whereas the register string
		name starts counting from 1. So calling getChannelTrim( 23 ) will return the
		value of the register named "Channel024". This is because all other code regarding
		channels starts counting from zero.
		"""
		# I don't know of the channel numbers are padded with zeros in the register
		# name, so I'll try a few possibilities
		possibleNames = [ "Channel%d"%(channelNumber+1), "Channel%02d"%(channelNumber+1), "Channel%03d"%(channelNumber+1) ]
		for name in possibleNames :
			register = self.getRegister(name)
		if register==None :
			raise Exception( "Nothing known about channel "+str(channelNumber) )
		return register.value
		
	def writeToFilename( self, filename, registerNames=None ) :
		"""
		Writes all currently held values to the given filename. If registerNames is specified only those
		registers are saved.
		"""
		file = open( filename, 'w+' )
		for register in self.registers :
			shouldWrite=True
			if registerNames != None :
				if registerNames.count(register.name)==0 : shouldWrite=False
			if shouldWrite : register.writeToFile(file)
		file.close()

	def writeTrimsToFilename( self, filename ) :
		file = open( filename, 'w+' )
		for register in self.registers :
			if register.name[0:7]=='Channel' :register.writeToFile(file)
		file.close()

class GlibSupervisorApplication( XDAQTools.Application ) :
	def __init__( self, host=None, port=None, className=None, instance=None, I2cRegisterDirectory="/home/xtaldaq/CBCAnalyzer/CMSSW_5_3_4/src/XtalDAQ/OnlineCBCAnalyser/runcontrol/i2c" ) :
		# Because there's a chance I might reassign the class of a base Application instance to this
		# class, I'll check and see if the base has been initialised before calling the super class
		# constructor.
		if not hasattr( self, "host" ) : super(GlibSupervisorApplication,self).__init__( host, port, className, instance )

		self._directoryForI2C=I2cRegisterDirectory
		# I2C parameters have to be saved to a file, and then the GlibSupervisor told to send the
		# file to the board. This is the temporary directory I'll use to store the files.
		self.tempDirectory="/tmp/cbcTestStandTempFiles/supervisor"
		try :
			os.makedirs( self.tempDirectory )
		except Exception as error:
			# Acceptable if the directory already exists, but any other error is a problem
			if error.args[1] != 'File exists' : raise
		
		# Note that because of the way the GlibSupervisor is coded, if some of these are missing
		# the supervisor will crash. So always make sure all of these are included in the POST
		# request, even if they're already set at the required values.
		self.parameters = {
			'user_wb_ttc_fmc_regs_pc_commands_TRIGGER_SEL':'off',  # turn off triggering from TTC
			'user_wb_ttc_fmc_regs_pc_commands_INT_TRIGGER_FREQ':7, # 4 corresponds to 16Hz. Look on the webconfig to see the other values
			'user_wb_ttc_fmc_regs_pc_commands2_FE0_masked':'off',
			'user_wb_ttc_fmc_regs_pc_commands2_FE1_masked':'off',
			'user_wb_ttc_fmc_regs_pc_commands_ACQ_MODE':'on',      # Continuous storage
			'user_wb_ttc_fmc_regs_pc_commands_CBC_DATA_GENE':'on', # External data
			'user_wb_ttc_fmc_regs_pc_commands2_negative_logic_CBC':'on'
		}
		self.saveParametersResource = "/urn:xdaq-application:lid="+str(self.id)+"/saveParameters"
		## Parameters and resource for reading an I2C address file
		self.readI2cParameters = { 'i2CFile':I2cRegisterDirectory+"/FE0CBC0.txt" }
		self.readI2cResource = "/urn:xdaq-application:lid="+str(self.id)+"/i2cRead"
		# The write I2C request takes no parameters, the filename has to be set
		# before hand with a read I2C request (not very RESTful but hey ho).
		self.writeI2cParameters = {}
		self.writeI2cResource = "/urn:xdaq-application:lid="+str(self.id)+"/i2cWriteFileValues"

		# I can only do the setup for the CBCs once this application has gone to the configured
		# state. I'll have to check this parameter in all methods and configure if it hasn't been
		# done yet.
		self._connectedCBCsHaveBeenInitialised=False
		# I expect this call to fail, but there's a chance the XDAQ process is already running
		# and this python representation of it is just re-connecting to it.
		try:
			self._initConnectedCBCs()
		except:
			pass

	def _initConnectedCBCs( self ) :
		"""
		Initialise information about the connected CBCs. This is only possible after this
		application has been sent the "Initialise" message, which means the XDAQ process
		must have already been started.
		"""
		# First need to know which FMCs are connected. The only place I've found
		# this information is available is in the main webpage, and it is only
		# available there after moving to the "Initialised" state. Otherwise I
		# could do this during __init__.
		
		try: 
			webpage = self.httpRequest( "GET", '/urn:xdaq-application:lid='+str(self.id), {}, True )
		except:
			# The XDAQ process probably hasn't been started. Replace the 'connection refused' error
			# with one that is more discriptive to the user.
			raise Exception("Couldn't connect to the XDAQ process to get information about the connected CBCs. Is the XDAQ process running and GlibSupervisor initialised?")
		# Perform a regular expression search on the HTML to see what the
		# state of each FMC is. I do this by looking at the alt text.
		fmcState=re.findall( """(?<=alt=')\w+(?='/> FMC 1<)""", webpage.fullMessage )
		if len(fmcState)!=1 : raise Exception( "Failed when querying which FMCs are connected. This information is only available after GlibSupervisor has been initialised.")
		elif fmcState[0]=='ON' : self.isFMC1Connected=True
		elif fmcState[0]=='OFF' : self.isFMC1Connected=False
		else : raise Exception( "Failed when querying which FMCs are connected. FMC 1 reported '"+fmcState[0]+"' which is not equal to either 'ON' or 'OFF'.")
		# Do the same for FMC 2
		fmcState=re.findall( """(?<=alt=')\w+(?='/> FMC 2<)""", webpage.fullMessage )
		if len(fmcState)!=1 : raise Exception( "Failed when querying which FMCs are connected. This information is only available after GlibSupervisor has been initialised.")
		elif fmcState[0]=='ON' : self.isFMC2Connected=True
		elif fmcState[0]=='OFF' : self.isFMC2Connected=False
		else : raise Exception( "Failed when querying which FMCs are connected. FMC 2 reported '"+fmcState[0]+"' which is not equal to either 'ON' or 'OFF'.")
		
		self._connectedCBCsHaveBeenInitialised=True
		
		self.i2cChips = {}
		if self.isFMC1Connected :
			self.i2cChips['FE1CBC0'] = I2cChip()
			self.i2cChips['FE1CBC1'] = I2cChip()
		if self.isFMC2Connected :
			self.i2cChips['FE0CBC0'] = I2cChip()
			self.i2cChips['FE0CBC1'] = I2cChip()

		# Try and load the default parameters
		failedChipNames = []
		for chipName in self.i2cChips.keys() :
			try :
				self.i2cChips[chipName].loadFromFile(self._directoryForI2C+'/'+chipName+'.txt')
			except :
				failedChipNames.append(chipName)

		if len(failedChipNames)!=0 : raise Exception( "Couldn't load values for chips: "+str(failedChipNames) )
		

	def connectedCBCNames(self) :
		if not self._connectedCBCsHaveBeenInitialised : self._initConnectedCBCs()
		return self.i2cChips.keys()
	
	def I2CRegisterValues( self, chipNames=None ) :
		if not self._connectedCBCsHaveBeenInitialised : self._initConnectedCBCs()
		if chipNames==None : cbcNames=self.connectedCBCNames()
		else : cbcNames=chipNames
		returnValue = {}
		for name in cbcNames :
			returnValue[name]=self.i2cChips[name].getValues()
		return returnValue


	def setConfigureParameters( self, triggerRate=None ) :
		"""
		Configure the parameters on the GLIB with the values required for data taking.
		You can optionally set a trigger rate in Hz which will be rounded down to the
		nearest power of 2.
		Note that these parameters aren't sent to the board unti the "Configure" state
		transition.
		"""
		if not self._connectedCBCsHaveBeenInitialised : self._initConnectedCBCs()
		if triggerRate!=None :
			triggerRateCode = int( math.log( triggerRate, 2 ) )
			self.parameters['user_wb_ttc_fmc_regs_pc_commands_INT_TRIGGER_FREQ']=triggerRateCode
		response=self.httpRequest( "POST", self.saveParametersResource, self.parameters, False )
		if response.status!= 200 : raise Exception( "GlibSupervisor.configure got the response "+str(response.status)+" - "+response.reason )
		# I'll initialise with the I2C registers set to what is required to
		# set the comparator from an external voltage.
		#self.sendI2cFile( os.getenv("CMSSW_BASE")+"/src/XtalDAQ/OnlineCBCAnalyser/runcontrol/I2CValues_comparatorExternalVoltage.txt" )

	def setAllChannelTrims( self, value ) :
		"""
		Sets the trim for all channels. Note that this isn't written to the board until sendI2C is called
		"""
		if not self._connectedCBCsHaveBeenInitialised : self._initConnectedCBCs()
		for channel in range(0,254) :
			self.setChannelTrim( channel, value )
	
	def setChannelTrim( self, channel, value, chipNames=None ) :
		"""
		Sets the trim for the specified channel. Note that this isn't written to the board until sendI2C is called.
		By default acts on all CBCs, but this can be limited by specifying an array for 'chipNames'.
		"""
		if not self._connectedCBCsHaveBeenInitialised : self._initConnectedCBCs()
		if chipNames==None : chipNames=self.i2cChips.keys()
		for name in chipNames :
			self.i2cChips[name].setChannelTrim( channel, value )

	def getChannelTrim( self, channel, chipNames=None ) :
		"""
		Returns a map of the channel trim for each chip. If only one chip is requested
		returns the value instead of a map.
		"""
		if not self._connectedCBCsHaveBeenInitialised : self._initConnectedCBCs()
		if chipNames==None : chipNames=self.i2cChips.keys()
		result = {}
		for name in chipNames :
			result[name]=self.i2cChips[name].getChannelTrim( channel )
		if len(chipNames)==1 : return result[chipNames[0]] # Don't bother with a map if it's only one chip
		else : return result

	def setI2c( self, registerNameValueTuple, chipNames=None ) :
		"""
		Sets the registers named by the keys in the tuple to the values in the tuple. By default
		does so for all connected CBCs, but this can be limited by specifying an array for 'chipNames'.
		
		Note this doesn't set the register on the chip, only in the internal representation. Changes
		will not be sent to the chip until sendI2c is called.
		"""
		if not self._connectedCBCsHaveBeenInitialised : self._initConnectedCBCs()
		
		if chipNames==None : chipNames=self.i2cChips.keys()
		for name in chipNames :
			chip = self.i2cChips[name]
			for name in registerNameValueTuple :
				register = chip.getRegister(name)
				register.value = registerNameValueTuple[name]

	def sendI2c( self, registerNames=None, chipNames=None ) :
		"""
		Sends all of the I2C registers to the chips by writing to temporary files and asking the
		GlibSupervisor to send these files. By default does so for all connected CBCs, but this
		can be limited by specifying an array for 'chipNames'.
		"""
		if not self._connectedCBCsHaveBeenInitialised : self._initConnectedCBCs()
		
		self.saveI2c( self.tempDirectory, registerNames, chipNames )
		self.sendI2cFilesFromDirectory( self.tempDirectory )
	
	def saveI2c( self, directoryName, registerNames=None, chipNames=None ) :
		if not self._connectedCBCsHaveBeenInitialised : self._initConnectedCBCs()
		
		# First make sure there are no files left over from previous sends. Allow an error
		# of 'No such file or directory' but throw any other exceptions.
		for filename in ["FE0CBC0.txt","FE0CBC1.txt","FE1CBC0.txt","FE1CBC1.txt"] :
			try :
				os.remove( os.path.join(self.tempDirectory,filename) )
			except Exception as error :
				if error.args[1] != 'No such file or directory' : raise
		# make sure the directory exists
		try:
			os.makedirs( directoryName )
		except:
			pass
		
		if chipNames==None : chipNames=self.i2cChips.keys()
		for name in chipNames :
			self.i2cChips[name].writeToFilename( os.path.join(directoryName,name+".txt"), registerNames )

	def sendI2cFilesFromDirectory( self, directoryName ) :
		"""
		Asks the GlibSupervisor to send the files in the given directory to the CBC registers.
		There can be up to four CBCs connected - 2 on each of 2 FEs depending on how many FMCs
		are connected. The files in the directory have to be named "FE<number>CBC<number>.txt"
		with the numbers being either 0 or 1. This is hard coded into the GlibSupervisor.
		
		This method will look at the contents of the directory and tell the GlibSupervisor to
		load all the files that match the required filename style. So if you don't want to send
		anything to a particular CBC don't have the file in the directory.
		
		The directory can only be specified in a "read" call, so a read is sent first to set the
		directory name, then the write is sent.
		
		Note that this method completely bypasses the I2C representation held internally by this
		class.
		"""
		if not self._connectedCBCsHaveBeenInitialised : self._initConnectedCBCs()
		
		self.writeI2cParameters = {} # clear this of any previous entries
		# Note that for some reason, the GlibSupervisor calls FMC1 "FE1" and FMC2 "FE0".
		if self.isFMC1Connected :
			if os.path.isfile( directoryName+"/FE1CBC0.txt" ) : self.writeI2cParameters["chkFE1CBC0"]="on"
			if os.path.isfile( directoryName+"/FE1CBC1.txt" ) : self.writeI2cParameters["chkFE1CBC1"]="on"
		if self.isFMC2Connected :
			if os.path.isfile( directoryName+"/FE0CBC0.txt" ) : self.writeI2cParameters["chkFE0CBC0"]="on"
			if os.path.isfile( directoryName+"/FE0CBC1.txt" ) : self.writeI2cParameters["chkFE0CBC1"]="on"
		
		if len( self.writeI2cParameters ) == 0 :
			raise Exception( "GlibSupervisor.sendI2cFilesFromDirectory was given a directory name containing no files with the required names (e.g. \"FE0CBC0.txt\")" )

		# First need to set the directory name in the GlibSupervisor. The only way to do this is to
		# call a "read" first.
		self.readI2cParameters['i2CFiles']=directoryName
		response=self.httpRequest( "POST", self.readI2cResource, self.readI2cParameters, False )
		if response.status!= 200 : raise Exception( "GlibSupervisor.sendI2cFile during read got the response "+str(response.status)+" - "+response.reason )

		# Now the directory has been set I can tell GlibSupervisor to write the files in it
		response=self.httpRequest( "POST", self.writeI2cResource, self.writeI2cParameters, True )
		if response.status!= 200 : raise Exception( "GlibSupervisor.sendI2cFile during write got the response "+str(response.status)+" - "+response.reason )


class GlibStreamerApplication( XDAQTools.Application ) :
	def __init__( self, host=None, port=None, className=None, instance=None ) :
		# Because there's a chance I might reassign the class of a base Application instance to this
		# class, I'll check and see if the base has been initialised before calling the super class
		# constructor.
		if not hasattr( self, "host" ) : super(GlibStreamerApplication,self).__init__( host, port, className, instance )
		# Now do the stuff specific to this subclass
		self.parameters = {
			'destination':'/tmp/scriptedRun.dat',
			'sharedMem':'off',    # pass the data to the RU
			'memToFile':'on',   # don't dump to a file
			'nbAcq':100, # The number of events to take. 100 is an arbitrary testing value.
			'acqMode':1, # The data format. 1 means "Full debug"; 3 means "Old format"
			'zeroSuppressed':'off'
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

	def setConfigureParameters( self, numberOfEvents=None ) :
		"""
		Sets the parameters ready for configuration. Note that these aren't sent to the board until
		the "Configure" state transition.
		"""
		if numberOfEvents!=None : self.parameters['nbAcq']=numberOfEvents
		response=self.httpRequest( "POST", self.saveParametersResource, self.parameters, False )
		if response.status!= 200 : raise Exception( "GlibStreamer.configure got the response "+str(response.status)+" - "+response.reason )

	def setOutputFilename( self, filename ) :
		"""
		This sets the filename of the DAQ output dump. Note that this change doesn't take effect
		until the next "Configure" state change (I think).
		"""
		self.parameters['destination']=filename
		response=self.httpRequest( "POST", self.saveParametersResource, self.parameters, False )
		if response.status!= 200 : raise Exception( "GlibStreamer.setOutputFilename got the response "+str(response.status)+" - "+response.reason )

	def setNumberOfEvents( self, numberOfEvents ) :
		"""
		The number of events that will be taken. Note that this change doesn't take effect
		until the next "Configure" state change (I think).
		"""
		self.parameters['nbAcq']=numberOfEvents
		response=self.httpRequest( "POST", self.saveParametersResource, self.parameters, False )
		if response.status!= 200 : raise Exception( "GlibStreamer.setNumberOfEvents got the response "+str(response.status)+" - "+response.reason )
		
	def acquisitionState(self):
		"""
		Reports whether data is being taken or not. Note that this is different to the state the
		GlibStreamer is in - it will still report "Running" after all events have been taken until
		the next state change.
		
		The streamer doesn't have any soap commands to query to the state of the acquisition. The
		only external way I can find to see if data is being recorded is to check the html status
		page. There's not a specific status display, but depending on the information shown the
		status can be inferred. This is likely to break with any change to the GlibStreamer.
		"""
		try:
			response=self.httpRequest( "GET", "/urn:xdaq-application:lid="+str(self.id) )
		except:
			return "<uncontactable>"		
		try:			
			# The only way I've figured out how to get this information is by using some
			# hard coded knowledge what the webpage shows in different states.
			streamerStateLine=response.fullMessage.splitlines()[34]
			if streamerStateLine[0:45]=="<table><tr><td><form action='saveHtmlValues'>":
				# The table to modify parameters is showing which means data is not being taken
				return "Stopped"
			elif streamerStateLine[0:33]=='<form action="pauseAcquisition" >':
				return "Running"
			else: return "<unknown>"
		except:
			return "<unknown>"

class SimpleGlibProgram( XDAQTools.Program ) :
	def __init__( self, xdaqConfigFilename ) :
		super(SimpleGlibProgram,self).__init__( xdaqConfigFilename )
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
		super(SimpleGlibProgram,self).reloadXDAQConfig()
		self._extendStreamerAndSupervisor()
		
	def initialise( self, triggerRate=None, numberOfEvents=100, timeout=5.0 ) :
		"""
		Starts the initialise process. If "timeout" is positive then control will block
		until all the applications have reached the required state, or until "timeout"
		seconds have passed.
		"""

		self.supervisor.sendCommand( "Initialise" )
		if timeout>0 : self.supervisor.waitForState( "Halted", timeout )
		
		# Now that everything is initialised, I'll set the parameters of the GlibSupervisor and
		# GlibStreamer to what I want to be the defaults. I'll set them here rather than at the
		# start of configure(..) so that the user can go into the web interface and make additional
		# changes on top. These settings aren't actually sent to the board until the streamer
		# and supervisor are sent the "Configure" command, so the user can make additional changes
		# and then call the configure(..) method.
		self.supervisor.setConfigureParameters(triggerRate)
		self.streamer.setConfigureParameters(numberOfEvents)

	def setOutputFilename( self, filename ) :
		self.streamer.setOutputFilename( filename )
		
	def setAndSendI2c( self, registerNameValueTuple, chipNames=None ) :
		self.supervisor.setI2c( registerNameValueTuple, chipNames )
		self.supervisor.sendI2c( registerNameValueTuple.keys(), chipNames )
	
	def configure( self, timeout=5.0 ) :
		self.supervisor.sendCommand( "Configure" )
		self.streamer.sendCommand( "configure" )
		
		if timeout>0 : self.supervisor.waitForState( "Configured", timeout )
		# Configuring the GlibSupervisor resets all I2C registers, so reset whatever
		# my settings are.
		self.supervisor.sendI2c()

	def stop( self, timeout=5.0 ) :
		self.streamer.sendCommand( "stop" )
		self.supervisor.sendCommand( "Stop" )

		if timeout>0 : self.supervisor.waitForState( "Configured", timeout )

	def enable( self, timeout=5.0 ) :
		self.supervisor.sendCommand( "Enable" )
		self.streamer.sendCommand( "start" )

		if timeout>0 : self.supervisor.waitForState( "Enabled", timeout )

	def halt( self, timeout=5.0 ) :
		self.supervisor.sendCommand( "Halt" )
		self.streamer.sendCommand( "halt" )

		if timeout>0 : self.supervisor.waitForState( "Halted", timeout )

	def pause( self, timeout=5.0 ) :
		self.streamer.sendCommand( "stop" )

	def play( self, timeout=5.0 ) :
		self.streamer.sendCommand( "start" )

class AnalyserControl :
	"""
	Class to interact with the C++ analysis program. This tells the program what to do by sending it
	HTTP requests.
	"""
	def __init__ ( self, host, port, startServerIfNotRunning=True ):
		self.connection=httplib.HTTPConnection( host+":"+str(port) )
		# Make sure the connection is closed, because all the other methods assume
		# it's in that state. Presumably the connection will have failed at that
		# stage anyway.
		self.connection.close()

		try :
			# Try and connect to see if the process is running. If it isn't, I'll have
			# to start it. Remove any data that has been left over from a previous run.
			self.httpGetRequest( "reset" )
		except:
			if startServerIfNotRunning :
				import subprocess
				print "AnalyserControl: server isn't running. Going to start on port "+str(port)+"."
				devnull=open("/dev/null")
				subprocess.Popen( ['standaloneCBCAnalyser','50000'], stdout=devnull, stderr=devnull )
				time.sleep(1) # Sleep for a second to allow the new process to open the port
			else :
				raise Exception( "The standaloneCBCAnalyser server is not running. Either start it manually or retry with startServerIfNotRunning set to True." )
		

	def httpGetRequest( self, resource, parameters={}, returnResponse=False ) :
		"""
		For some reason httplib doesn't send the parameters as part of the URL. Not sure if it's
		supposed to but I thought it was. My mini http server running in C++ can't decode these
		(at the moment) so I'll add the parameters to the URL by hand.
		
		If returnResponse is True, the actual response from the server is returned. Otherwise
		True or False is returned depending on whether the server returned success or not.
		"""
		try:
			self.connection.connect()
			headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
			self.connection.request( "GET", "/"+urllib.quote(resource)+"?"+urllib.urlencode(parameters), {}, headers )
			response = self.connection.getresponse()
			if returnResponse :
				message=response.read()
				self.connection.close()
				return message
			else :
				self.connection.close()
				if response.status==200 : return True
				else : return False
		except :
			# Make sure the connection is closed before leaving this method, no
			# matter what the circumstances are. Otherwise the connection might
			# block next time I try to use it
			self.connection.close()
			# It's now okay to throw the original exception
			raise

	def analyseFile( self, filename ) :
		return self.httpGetRequest( "analyseFile", { "filename" : filename } )

	def saveHistograms( self, filename ) :
		return self.httpGetRequest( "saveHistograms", { "filename" : filename } )

	def setThreshold( self, threshold ) :
		return self.httpGetRequest( "setThreshold", { "value" : str(threshold) } )
	
	def reset( self ) :
		return self.httpGetRequest( "reset" )
	
	def restoreFromRootFile( self, filename ) :
		return self.httpGetRequest( "restoreFromRootFile", { "filename" : filename } )
	
	def fitParameters( self ) :
		jsonString=self.httpGetRequest( "fitParameters", returnResponse=True )
		analysisResult=json.loads( jsonString )
		# The CBC code indexes CBCs differently. I'll rearrange this structure to match
		# the python code.
		result={}
		for cbcName in analysisResult.keys() :
			if cbcName=='CBC 00' : pythonCbcName='FE0CBC0'
			elif cbcName=='CBC 01' : pythonCbcName='FE0CBC1'
			elif cbcName=='CBC 02' : pythonCbcName='FE1CBC0'
			elif cbcName=='CBC 03' : pythonCbcName='FE1CBC1'
			else : pythonCbcName=cbcName
			# The C++ code doesn't know if a CBC is connected or not, since unconnected CBCs
			# show up in the DAQ dumps as all on channels. I need to check whether these are
			# actually connected.
			arrayOfChannels=[]
			for channelNumber in range(0,254) :
				channelName="Channel %03d"%channelNumber
				try:
					arrayOfChannels.append( analysisResult[cbcName][channelName] )
				except:
					# The C++ code might not now about the channel and not return it. I need
					# the array to be the correct size though so I'll just add 'None'.
					arrayOfChannels.append( None )
			result[pythonCbcName]=arrayOfChannels

		return result
			
		
		
