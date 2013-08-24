import xdglib
import xml.etree.ElementTree as ElementTree

class Process :
	def __init__(self, host, port, className, instance ) :
		self.host=host
		self.port=port
		self.className=className
		self.instance=instance
	def __str__(self) :
		return self.host+","+str(self.port)+","+self.className+","+str(self.instance)
	def __repr__(self) :
		return "<XDAQ Process "+self.host+", "+str(self.port)+", "+self.className+", "+str(self.instance)+">"
	def sendCommand( self, command ) :
		return xdglib.sendSOAPCommand( self.host, self.port, self.className, self.instance, command )
	def getState(self) :
		try :
			result=ElementTree.fromstring( self.sendCommand('ParameterQuery') )
			path="{http://schemas.xmlsoap.org/soap/envelope/}"+"Body/" \
				+ "{urn:xdaq-soap:3.0}"+"ParameterQueryResponse/" \
				+ "{urn:xdaq-application:"+self.className+"}"+"properties/" \
				+ "{urn:xdaq-application:"+self.className+"}"+"stateName"
			stateName=result.find(path)
			if stateName == None : return "<unknown>"
			else : return stateName.text
		except : return "<uncontactable>"
		

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
