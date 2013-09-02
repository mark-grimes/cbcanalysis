import xdglib
import xml.etree.ElementTree as ElementTree

class ElementExtension( ElementTree._ElementInterface ) :
	""" Extension to the ElementTree element interface that adds methods to get children with
		a particular name, regardless of the xml namespace. """
	def __init__( self, baseclass ) :
		self=baseclass
	def getchildrennamed( self, name ) :
		returnValue=[]
		for child in self.getchildren():
			splitByNamespace=child.tag.split("}")
			if len(splitByNamespace)==1 : tagname=splitByNamespace[0]
			elif len(splitByNamespace)==2 : tagname=splitByNamespace[1]
			if name==tagname :
				child.__class__=ElementExtension
				returnValue.append( child )
		return returnValue
	def getchildnamed( self, name ) :
		""" Returns the first child with the supplied name (or None), ignoring xml namespaces. """
		result=self.getchildrennamed( name )
		if len(result)==0 : return None
		else : return result[0]

class Context :
	def __init__( self, elementTreeNode, configFilename ) :
		self.processes = []
		self.configFilename = configFilename
		self.jobid = -1
		# Split off anything that is part of the xml namespace (in ElementTree this
		# is encapsulated in curly braces).
		splitByNamespace=elementTreeNode.tag.split("}")
		if len(splitByNamespace)==1 : tagname=splitByNamespace[0]
		elif len(splitByNamespace)==2 : tagname=splitByNamespace[1]
		else : raise Exception( "Couldn't split off the namespace in '"+elementTreeNode.tag+"'" )
		if tagname!="Context" : raise Exception( "Not a Context node" )
		# Loop over the items and record the url and port
		for item in elementTreeNode.items() :
			if item[0]=="url" : currentURL=item[1]
		if currentURL==None : raise Exception( "Couldn't get the URL for this context" )
		self.host=currentURL.split(":")[-2].split("/")[-1] # Get everything after "http://" and before the port (i.e. last ":" separator)
		self.port=currentURL.split(":")[-1]
		# Now loop over all of the children and look for Application nodes
		for child in elementTreeNode.getchildren() :
			# Split off the namespace as before
			splitByNamespace=child.tag.split("}")
			if len(splitByNamespace)==1 : tagname=splitByNamespace[0]
			elif len(splitByNamespace)==2 : tagname=splitByNamespace[1]
			else : raise Exception( "Couldn't split off the namespace in '"+child.tag+"'" )
			if tagname=="Application" :
				# Loop over the items and record the url and port
				for item in child.items() :
					if item[0]=="class" : className=item[1]
					elif item[0]=="instance" : instance=item[1]
				# Now try and create the Process object and add it to the return value
				newProcess=Process( self.host, int(self.port), className, int(instance) )
				self.processes.append( newProcess )
	def startProcess(self) :
		self.jobid=-1
		response=ElementTree.fromstring( xdglib.sendConfigurationStartCommand( "http://"+self.host+":"+self.port, self.configFilename ) )
		response.__class__=ElementExtension
		self.jobid = response.getchildnamed("Body").getchildnamed("jidResponse").getchildnamed("jid").text

	def killProcess(self) :
		response=ElementTree.fromstring( xdglib.sendConfigurationKillCommand( "http://"+self.host+":"+self.port, self.jobid ) )
		response.__class__=ElementExtension
		reply=response.getchildnamed("Body").getchildnamed("getStateResponse").getchildnamed("reply").text
		if reply=='no job killed.' : return False
		elif reply=='killed by JID' : return True

class Process :
	def __init__(self, host, port, className, instance, configFilename=None ) :
		self.host=host
		self.port=port
		self.className=className
		self.instance=instance
		self.jid=-1
		self.configFilename=configFilename
	def __str__(self) :
		return self.host+","+str(self.port)+","+self.className+","+str(self.instance)
	def __repr__(self) :
		return "<XDAQ Process "+self.host+", "+str(self.port)+", "+self.className+", "+str(self.instance)+">"
	def sendCommand( self, command ) :
		return xdglib.sendSOAPCommand( self.host, self.port, self.className, self.instance, command )
	def getState(self) :
		try :
			result=ElementTree.fromstring( self.sendCommand('ParameterQuery') )
			result.__class__=ElementExtension
			try :
				return result.getchildnamed("Body").getchildnamed("ParameterQueryResponse").getchildnamed("properties").getchildnamed("stateName").text
			except :
				return "<unknown>"
		except : return "<uncontactable>"

def parseXDAQConfigFile( filename ) :
	""" Parses the XDAQ xml configuration file supplied and returns an array of Process objects.
		Largely copied from xdglib.parseConfigurationFile """
	returnValue = []
	tree=ElementTree.parse( filename )
	for node in tree.getroot().getchildren() :
		try :
			newContext=Context( node, filename )
			returnValue.append( newContext )
		except Exception as error :
			print "Unable to create context for node",str(node),"because",str(error)
	return returnValue
	

class MultiContext :
	def __init__(self):
		self.processes={
			'TrackerManager' : Process('localhost.localdomain', 20000, 'TrackerManager', 0),
			'evm' : Process( 'localhost.localdomain', 20000, 'rubuilder::evm::Application', 0 ),
			'ru' : Process( 'localhost', 10001, 'rubuilder::ru::Application', 0 ),
			'bu' : Process( 'localhost', 10001, 'rubuilder::bu::Application', 0 ),
			'StorageManager' : Process( 'localhost', 10004, 'StorageManager', 0 ),
			'otherFUEventProcessor' : Process( 'localhost', 10002, 'evf::FUEventProcessor', 1 ),
			'myFUEventProcessor' : Process( 'localhost', 10005, 'evf::FUEventProcessor', 0 ),
			'FUResourceBroker' : Process( 'localhost', 10003, 'evf::FUResourceBroker', 0 ),
			'GlibSupervisor' : Process( 'localhost', 10000, 'GlibSupervisor', 0 ),
			'GlibStreamer' : Process( 'localhost', 10001, 'GlibStreamer', 0 )
		}
	def printStates(self):
		for processName in self.processes :
			process=self.processes[processName]
			print process.className.ljust(28)+"("+str(process.instance)+") -",process.getState().ljust(12),"  ("+processName+")"
	def sendAllCommand( self, command ) :
		for processName in self.processes :
			process=self.processes[processName]
			process.sendCommand(command)
	def initialise(self):
		xdglib.sendSOAPCommand( 'localhost.localdomain', 20000, 'TrackerManager', 0, 'Initialise' )
		xdglib.sendSOAPCommand( 'localhost.localdomain', 20000, 'pt::atcp::PeerTransportATCP', 2, 'Configure' )
		xdglib.sendSOAPCommand( 'localhost', 10000, 'pt::atcp::PeerTransportATCP', 0, 'Configure' )
		xdglib.sendSOAPCommand( 'localhost', 10001, 'pt::atcp::PeerTransportATCP', 1, 'Configure' )
		xdglib.sendSOAPCommand( 'localhost', 10002, 'pt::atcp::PeerTransportATCP', 3, 'Configure' )
		xdglib.sendSOAPCommand( 'localhost', 10003, 'pt::atcp::PeerTransportATCP', 4, 'Configure' )
		xdglib.sendSOAPCommand( 'localhost', 10004, 'pt::atcp::PeerTransportATCP', 5, 'Configure' )
		xdglib.sendSOAPCommand( 'localhost', 10005, 'pt::atcp::PeerTransportATCP', 6, 'Configure' )
		xdglib.sendSOAPCommand( 'localhost.localdomain', 20000, 'pt::atcp::PeerTransportATCP', 2, 'Enable' )
		xdglib.sendSOAPCommand( 'localhost', 10000, 'pt::atcp::PeerTransportATCP', 0, 'Enable' )
		xdglib.sendSOAPCommand( 'localhost', 10001, 'pt::atcp::PeerTransportATCP', 1, 'Enable' )
		xdglib.sendSOAPCommand( 'localhost', 10002, 'pt::atcp::PeerTransportATCP', 3, 'Enable' )
		xdglib.sendSOAPCommand( 'localhost', 10003, 'pt::atcp::PeerTransportATCP', 4, 'Enable' )
		xdglib.sendSOAPCommand( 'localhost', 10004, 'pt::atcp::PeerTransportATCP', 5, 'Enable' )
		xdglib.sendSOAPCommand( 'localhost', 10005, 'pt::atcp::PeerTransportATCP', 6, 'Enable' )
		xdglib.sendSOAPCommand( 'localhost.localdomain', 20000, 'rubuilder::evm::Application', 0, 'Configure' )
		xdglib.sendSOAPCommand( 'localhost', 10001, 'rubuilder::ru::Application', 0, 'Configure' )
		xdglib.sendSOAPCommand( 'localhost', 10001, 'rubuilder::bu::Application', 0, 'Configure' )
		xdglib.sendSOAPCommand( 'localhost', 10004, 'StorageManager', 0, 'Configure' )
		xdglib.sendSOAPCommand( 'localhost', 10002, 'evf::FUEventProcessor', 0, 'Configure' )
		xdglib.sendSOAPCommand( 'localhost', 10005, 'evf::FUEventProcessor', 1, 'Configure' )
		xdglib.sendSOAPCommand( 'localhost', 10003, 'evf::FUResourceBroker', 0, 'Configure' )
		xdglib.sendSOAPCommand( 'localhost', 10000, 'GlibSupervisor', 0, 'Initialise' )
		xdglib.sendSOAPCommand( 'localhost.localdomain', 20000, 'rubuilder::evm::Application', 0, 'Enable' )
		xdglib.sendSOAPCommand( 'localhost', 10001, 'rubuilder::ru::Application', 0, 'Enable' )
		xdglib.sendSOAPCommand( 'localhost', 10001, 'rubuilder::bu::Application', 0, 'Enable' )
		xdglib.sendSOAPCommand( 'localhost', 10004, 'StorageManager', 0, 'Enable' )
	
	def configure(self):
		xdglib.sendSOAPCommand( 'localhost', 10000, 'GlibSupervisor', 0, 'Configure' )
		xdglib.sendSOAPCommand( 'localhost.localdomain', 20000, 'TrackerManager', 0, 'Configure' )
	
	def enable(self):
		xdglib.sendSOAPCommand( 'localhost', 10000, 'GlibSupervisor', 0, 'Enable' )
		xdglib.sendSOAPCommand( 'localhost.localdomain', 20000, 'TrackerManager', 0, 'Enable' )
		xdglib.sendSOAPCommand( 'localhost', 10002, 'evf::FUEventProcessor', 0, 'Enable' )
		xdglib.sendSOAPCommand( 'localhost', 10005, 'evf::FUEventProcessor', 1, 'Enable' )
		xdglib.sendSOAPCommand( 'localhost', 10003, 'evf::FUResourceBroker', 0, 'Enable' )
		xdglib.sendSOAPCommand( 'localhost', 10001, 'GlibStreamer', 0, 'start' )
	
	def halt(self):
		xdglib.sendSOAPCommand( 'localhost', 10001, 'GlibStreamer', 0, 'stop' )
		xdglib.sendSOAPCommand( 'localhost', 10000, 'GlibSupervisor', 0, 'Halt' )
		xdglib.sendSOAPCommand( 'localhost.localdomain', 20000, 'TrackerManager', 0, 'Halt' )
		xdglib.sendSOAPCommand( 'localhost', 10004, 'StorageManager', 0, 'Halt' )
		xdglib.sendSOAPCommand( 'localhost', 10002, 'evf::FUEventProcessor', 0, 'Halt' )
		xdglib.sendSOAPCommand( 'localhost', 10005, 'evf::FUEventProcessor', 1, 'Halt' )
		xdglib.sendSOAPCommand( 'localhost', 10003, 'evf::FUResourceBroker', 0, 'Halt' )
	
	def stopRun(self):
		xdglib.sendSOAPCommand( 'localhost', 10001, 'GlibStreamer', 0, 'stop' )
		xdglib.sendSOAPCommand( 'localhost', 10000, 'GlibSupervisor', 0, 'Halt' )
		xdglib.sendSOAPCommand( 'localhost', 10002, 'evf::FUEventProcessor', 0, 'Stop' )
		xdglib.sendSOAPCommand( 'localhost', 10005, 'evf::FUEventProcessor', 1, 'Stop' )
		xdglib.sendSOAPCommand( 'localhost', 10003, 'evf::FUResourceBroker', 0, 'Stop' )
		xdglib.sendSOAPCommand( 'localhost', 10000, 'GlibSupervisor', 0, 'Configure' )
		xdglib.sendSOAPCommand( 'localhost.localdomain', 20000, 'rubuilder::evm::Application', 0, 'Stop' )
		xdglib.sendSOAPCommand( 'localhost', 10001, 'rubuilder::ru::Application', 0, 'Stop' )
		xdglib.sendSOAPCommand( 'localhost', 10001, 'rubuilder::bu::Application', 0, 'Stop' )
	
	def startRun(self):
		xdglib.sendSOAPCommand( 'localhost', 10000, 'GlibSupervisor', 0, 'Enable' )
		xdglib.sendSOAPCommand( 'localhost', 10002, 'evf::FUEventProcessor', 0, 'Enable' )
		xdglib.sendSOAPCommand( 'localhost', 10005, 'evf::FUEventProcessor', 1, 'Enable' )
		xdglib.sendSOAPCommand( 'localhost', 10003, 'evf::FUResourceBroker', 0, 'Enable' )
		xdglib.sendSOAPCommand( 'localhost', 10001, 'GlibStreamer', 0, 'start' )
		xdglib.sendSOAPCommand( 'localhost.localdomain', 20000, 'rubuilder::evm::Application', 0, 'Enable' )
		xdglib.sendSOAPCommand( 'localhost', 10001, 'rubuilder::ru::Application', 0, 'Enable' )
		xdglib.sendSOAPCommand( 'localhost', 10001, 'rubuilder::bu::Application', 0, 'Enable' )



class SingleContext:
	def initialise():
		xdglib.sendSOAPCommand( 'localhost', 13000, 'TrackerManager', 0, 'Initialise' )
		xdglib.sendSOAPCommand( 'localhost', 13000, 'rubuilder::evm::Application', 0, 'Configure' )
		xdglib.sendSOAPCommand( 'localhost', 13000, 'rubuilder::ru::Application', 0, 'Configure' )
		xdglib.sendSOAPCommand( 'localhost', 13000, 'rubuilder::bu::Application', 0, 'Configure' )
		xdglib.sendSOAPCommand( 'localhost', 13000, 'evf::FUEventProcessor', 0, 'Configure' )
		xdglib.sendSOAPCommand( 'localhost', 13000, 'evf::FUResourceBroker', 0, 'Configure' )
		xdglib.sendSOAPCommand( 'localhost', 13000, 'GlibSupervisor', 0, 'Initialise' )
		xdglib.sendSOAPCommand( 'localhost', 13000, 'rubuilder::evm::Application', 0, 'Enable' )
		xdglib.sendSOAPCommand( 'localhost', 13000, 'rubuilder::ru::Application', 0, 'Enable' )
		xdglib.sendSOAPCommand( 'localhost', 13000, 'rubuilder::bu::Application', 0, 'Enable' )
	
	def configure():
		xdglib.sendSOAPCommand( 'localhost', 13000, 'GlibSupervisor', 0, 'Configure' )
	
		
	def enable():
		xdglib.sendSOAPCommand( 'localhost', 13000, 'GlibSupervisor', 0, 'Enable' )
		xdglib.sendSOAPCommand( 'localhost', 13000, 'evf::FUEventProcessor', 0, 'Enable' )
		xdglib.sendSOAPCommand( 'localhost', 13000, 'evf::FUResourceBroker', 0, 'Enable' )
		xdglib.sendSOAPCommand( 'localhost', 13000, 'GlibStreamer', 0, 'start' )
	
	def halt():
		xdglib.sendSOAPCommand( 'localhost', 13000, 'GlibStreamer', 0, 'stop' )
		xdglib.sendSOAPCommand( 'localhost', 13000, 'GlibSupervisor', 0, 'Halt' )
		xdglib.sendSOAPCommand( 'localhost', 13000, 'evf::FUEventProcessor', 0, 'Halt' )
		xdglib.sendSOAPCommand( 'localhost', 13000, 'evf::FUResourceBroker', 0, 'Halt' )
