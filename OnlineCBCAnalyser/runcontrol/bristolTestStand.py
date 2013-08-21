import httplib, urllib, time


class I2cRegister :
	''' Class to hold details about an I2C register for the CBC test stand. 
		@author Mark Grimes (mark.grimes@bristol.ac.uk)
		@date 08/Aug/2013 '''
	def __init__(self,name,address,defaultValue,value) :
		self.name=name
		self.address=int(address,0)
		self.defaultValue=int(defaultValue,0)
		self.value=int(value,0)
	def writeToFile(self,file) :
		file.write( self.name.ljust(20)+hex(self.address).ljust(8)+hex(self.defaultValue).ljust(8)+hex(self.value).ljust(8)+"\n" )

class I2cChip :
	''' Class to hold several instances of an I2cRegister.
		@author Mark Grimes (mark.grimes@bristol.ac.uk)
		@date 08/Aug/2013 '''
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
		''' Returns the Register instance with the given name '''
		for register in self.registers :
			if register.name==registerName : return register
		# If control got this far then no register was found
		return None
	
	def setChannelTrim( self, channelNumber, value ) :
		''' Set the register with the name "Channel<channelNumber>" to the supplied value '''
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


class GlibSupervisor :
	def __init__( self, url="localhost.localdomain:10000", I2cRegisterFilename="/home/xtaldaq/trackerDAQ-3.1/CBCDAQ/GlibSupervisor/config/CBCv1_i2cSlaveAddrTable.txt" ) :
		self.I2cChip = I2cChip(I2cRegisterFilename)
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
		# I copied this from an example on stack overflow
		self.headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
		# This address is taken from the xml configuration file "realBoard.xml"
		self.connection = httplib.HTTPConnection(url)
		# Close connection immediately because the other methods assume closed connections
		self.connection.close()
		# I took this from examining the html presented to see what the html form name was.
		self.saveParametersResource = "/urn:xdaq-application:lid=30/saveParameters"
		# Parameters and resource for reading an I2C address file
		self.readI2cParameters = { 'i2CFile':I2cRegisterFilename }
		self.readI2cResource = "/urn:xdaq-application:lid=30/i2cRead"
		self.writeI2cParameters = {}
		self.writeI2cResource = "/urn:xdaq-application:lid=30/i2cWriteFileValues"

	def configure(self,triggerRate=None) :
		if triggerRate!=None : self.parameters['triggerFreq']=triggerRate
		self.connection.connect()
		self.connection.request( "POST", urllib.quote(self.saveParametersResource), urllib.urlencode(self.parameters), self.headers )
		response = self.connection.getresponse()
		self.connection.close()
		if response.status!= 200 : raise Exception( "GlibSupervisor.configure got the response "+str(response.status)+" - "+response.reason )
	
	def setAllChannelTrims( self, value ) :
		for channel in range(0,128) :
			self.setChannelTrim( channel, value )
	
	def setChannelTrim( self, channel, value ) :
		self.I2cChip.setChannelTrim( channel, value )

	def sendI2c( self, registerNames=None ) :
		temporaryFilename = "/tmp/i2CFileToSendToBoard.txt"
		sendCommandsIndividually=False
		if not sendCommandsIndividually:
			self.I2cChip.writeTrimsToFilename( temporaryFilename )
			self.readI2cParameters['i2CFile']=temporaryFilename
			self.connection.connect()
			self.connection.request( "POST", urllib.quote(self.readI2cResource), urllib.urlencode(self.readI2cParameters), self.headers )
			response = self.connection.getresponse()
			self.connection.close()
			if response.status!= 200 : raise Exception( "GlibSupervisor.sendI2c got the response "+str(response.status)+" - "+response.reason )
			self.connection.connect()
			self.connection.request( "GET", urllib.quote(self.writeI2cResource), urllib.urlencode(self.writeI2cParameters), self.headers )
			response = self.connection.getresponse()
			self.connection.close()
			if response.status!= 200 : raise Exception( "GlibSupervisor.sendI2c got the response "+str(response.status)+" - "+response.reason )
		else :
			for register in self.I2cChip.registers :
				file = open( temporaryFilename, 'w' )
				register.writeToFile(file)
				file.close()
				self.readI2cParameters['i2CFile']=temporaryFilename
				self.connection.connect()
				self.connection.request( "POST", urllib.quote(self.readI2cResource), urllib.urlencode(self.readI2cParameters), self.headers )
				response = self.connection.getresponse()
				self.connection.close()
				if response.status!= 200 : raise Exception( "GlibSupervisor.sendI2c got the response "+str(response.status)+" - "+response.reason )
				self.connection.connect()
				self.connection.request( "GET", urllib.quote(self.writeI2cResource), urllib.urlencode(self.writeI2cParameters), self.headers )
				response = self.connection.getresponse()
				self.connection.close()
				if response.status!= 200 : raise Exception( "GlibSupervisor.sendI2c got the response "+str(response.status)+" - "+response.reason )
				#time.sleep(1)
				
	def setAndSendI2c( self, registerName, value ):
		register=self.I2cChip.getRegister(registerName)
		if register==None : raise Exception( "Nothing known about register "+registerName )
		register.value=value
		temporaryFilename = "/tmp/i2CSingleValue.txt"
		file = open( temporaryFilename, 'w' )
		register.writeToFile(file)
		file.close()
		self.readI2cParameters['i2CFile']=temporaryFilename
		self.connection.connect()
		self.connection.request( "POST", urllib.quote(self.readI2cResource), urllib.urlencode(self.readI2cParameters), self.headers )
		response = self.connection.getresponse()
		self.connection.close()
		if response.status!= 200 : raise Exception( "GlibSupervisor.setAndSendI2c got the response "+str(response.status)+" - "+response.reason )
		self.connection.connect()
		self.connection.request( "GET", urllib.quote(self.writeI2cResource), urllib.urlencode(self.writeI2cParameters), self.headers )
		response = self.connection.getresponse()
		self.connection.close()
		if response.status!= 200 : raise Exception( "GlibSupervisor.setAndSendI2c got the response "+str(response.status)+" - "+response.reason )

		
		


class GlibStreamer :
	def __init__( self, url="localhost.localdomain:10001" ) :
		self.parameters = {
			'destination':'',
			'sharedMem':'on',   # pass the data to the RU
			'memToFile':'off',
			'shortPause':4,     # this what the default was, so I'll leave it as is.
			'longPause':2000,   # this what the default was, so I'll leave it as is.
			'nbAcq':100,        # The number of events to take. 100 is an arbitrary testing value.
			'log':'off',         # Just controls the display on the webpage.
			'flags':'off',       # Just controls the display on the webpage.
			'dataflags':'off',   # Just controls the display on the webpage.
			'counters':'off',    # Just controls the display on the webpage.
			'hardwareCounter':'off',
			'simulated':'off',
			'dataFile':''
		}
		self.headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
		self.connection = httplib.HTTPConnection("localhost.localdomain:10001")
		# Close connection immediately because the other methods assume closed connections
		self.connection.close()
		self.saveParametersResource = "/urn:xdaq-application:lid=200/validParam"
		self.forceStartResource = "/urn:xdaq-application:lid=200/forceStartXgi"
	
	def configure(self,numberOfEvents=None) :
		if numberOfEvents!=None : self.parameters['nbAcq']=numberOfEvents
		self.connection.connect()
		self.connection.request("POST", urllib.quote(self.saveParametersResource), urllib.urlencode(self.parameters), self.headers )
		response = self.connection.getresponse()
		self.connection.close()
		if response.status!= 200 : raise Exception( "GlibStreamer.configure got the response "+str(response.status)+" - "+response.reason )
	
	def startRecording(self) :
		self.connection.connect()
		self.connection.request("GET", urllib.quote(self.forceStartResource), urllib.urlencode({}), self.headers )
		response = self.connection.getresponse()
		self.connection.close()
		if response.status!= 200 : raise Exception( "GlibStreamer.startRecording got the response "+str(response.status)+" - "+response.reason )

