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


import XDAQTools, time, math, httplib, urllib, os

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
		
		if filename!=None :
			inputFile = open(filename,'r')
			for line in inputFile.readlines() :
				if line[0]!='#' and line[0]!='*' and len(line)>0:
					splitLine = line.split()
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
	
	def setChannelTrim( self, channelNumber, value ) :
		"""
		Set the register with the name "Channel<channelNumber>" to the supplied value
		"""
		# I don't know of the channel numbers are padded with zeros in the register
		# name, so I'll try a few possibilities
		possibleNames = [ "Channel%d"%(channelNumber), "Channel%02d"%(channelNumber), "Channel%03d"%(channelNumber) ]
		for name in possibleNames :
			register = self.getRegister(name)
			if register == None : print name+" doesn't work"
			else : name+" works"
		if register==None :
			raise Exception( "Nothing known about channel "+str(channelNumber) )
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
			'user_wb_ttc_fmc_regs_pc_commands_TRIGGER_SEL':'off',  # turn off triggering from TTC
			'user_wb_ttc_fmc_regs_pc_commands_INT_TRIGGER_FREQ':4, # 4 corresponds to 16Hz. Look on the webconfig to see the other values
			'user_wb_ttc_fmc_regs_pc_commands2_FE0_masked':'off',
			'user_wb_ttc_fmc_regs_pc_commands2_FE1_masked':'off',
			'user_wb_ttc_fmc_regs_pc_commands_ACQ_MODE':'on',      # Continuous storage
			'user_wb_ttc_fmc_regs_pc_commands_CBC_DATA_GENE':'on', # External data
			'user_wb_ttc_fmc_regs_pc_commands2_negative_logic_CBC':'on'
		}
		self.saveParametersResource = "/urn:xdaq-application:lid="+str(self.id)+"/saveParameters"
		# See what I2C registers there are
		try :
			self.I2cChip = I2cChip(I2cRegisterFilename)
		except :
			self.I2cChip = None
		## Parameters and resource for reading an I2C address file
		self.readI2cParameters = { 'i2CFile':I2cRegisterFilename }
		self.readI2cResource = "/urn:xdaq-application:lid="+str(self.id)+"/i2cRead"
		# The write I2C request takes no parameters, the filename has to be set
		# before hand with a read I2C request (not very RESTful but hey ho).
		self.writeI2cParameters = {}
		self.writeI2cResource = "/urn:xdaq-application:lid="+str(self.id)+"/i2cWriteFileValues"
		
		# These are flags to say which FMCs are connected. I don't actually have the code to set
		# these properly yet, until then I'll hard code it.
		# Note that for some reason, the GlibSupervisor calls FMC1 "FE1" and FMC2 "FE0"
		self.isFMC1Connected = False
		self.isFMC2Connected = True


	def setConfigureParameters( self, triggerRate=None ) :
		"""
		Configure the parameters on the GLIB with the values required for data taking.
		You can optionally set a trigger rate in Hz which will be rounded down to the
		nearest power of 2.
		Note that these parameters aren't sent to the board unti the "Configure" state
		transition.
		"""
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
		
		The GlibSupervisor uses a hard coded filename within a user specified directory (e.g. "FE0CBC0.txt").
		The directory can only be set with a call to i2cRead, so to perform a write the file is copied to
		a temporary directory with 
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
		"""
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
		response=self.httpRequest( "GET", self.writeI2cResource, self.writeI2cParameters, True )
		if response.status!= 200 : raise Exception( "GlibSupervisor.sendI2cFile during write got the response "+str(response.status)+" - "+response.reason )
		return response


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
			if streamerStateLine[8:28]=="Short pause duration":
				# The table to modify parameters is showing which means data is not being taken
				return "Stopped"
			elif streamerStateLine[8:49]=='<input type="submit" value="Start saving"':
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
		
	def initialise( self, triggerRate=16, numberOfEvents=100, timeout=5.0 ) :
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
		
	def configure( self, timeout=5.0 ) :
		self.supervisor.sendCommand( "Configure" )
		self.streamer.sendCommand( "configure" )
		
		if timeout>0 : self.supervisor.waitForState( "Configured", timeout )
		
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
	def __init__ ( self, host, port ):
		self.connection=httplib.HTTPConnection( host+":"+str(port) )
		# Make sure the connection is closed, because all the other methods assume
		# it's in that state. Presumably the connection will have failed at that
		# stage anyway.
		self.connection.close()

	def httpGetRequest( self, resource, parameters={} ) :
		"""
		For some reason httplib doesn't send the parameters as part of the URL. Not sure if it's
		supposed to but I thought it was. My mini http server running in C++ can't decode these
		(at the moment) so I'll add the parameters to the URL by hand.
		"""
		try:
			self.connection.connect()
			headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
			self.connection.request( "GET", "/"+urllib.quote(resource)+"?"+urllib.urlencode(parameters), {}, headers )
			response = self.connection.getresponse()
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
		self.httpGetRequest( "analyseFile", { "filename" : filename } )

	def saveHistograms( self, threshold ) :
		self.httpGetRequest( "saveHistograms", { "filename" : filename } )

	def setThreshold( self, threshold ) :
		self.httpGetRequest( "setThreshold", { "value" : str(threshold) } )