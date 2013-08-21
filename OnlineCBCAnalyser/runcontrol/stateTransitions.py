import xdglib

class MultiContext :
	def initialise():
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
	
	def configure():
		xdglib.sendSOAPCommand( 'localhost', 10000, 'GlibSupervisor', 0, 'Configure' )
		xdglib.sendSOAPCommand( 'localhost.localdomain', 20000, 'TrackerManager', 0, 'Configure' )
	
	def enable():
		xdglib.sendSOAPCommand( 'localhost', 10000, 'GlibSupervisor', 0, 'Enable' )
		xdglib.sendSOAPCommand( 'localhost.localdomain', 20000, 'TrackerManager', 0, 'Enable' )
		xdglib.sendSOAPCommand( 'localhost', 10002, 'evf::FUEventProcessor', 0, 'Enable' )
		xdglib.sendSOAPCommand( 'localhost', 10005, 'evf::FUEventProcessor', 1, 'Enable' )
		xdglib.sendSOAPCommand( 'localhost', 10003, 'evf::FUResourceBroker', 0, 'Enable' )
		xdglib.sendSOAPCommand( 'localhost', 10001, 'GlibStreamer', 0, 'start' )
	
	def halt():
		xdglib.sendSOAPCommand( 'localhost', 10001, 'GlibStreamer', 0, 'stop' )
		xdglib.sendSOAPCommand( 'localhost', 10000, 'GlibSupervisor', 0, 'Halt' )
		xdglib.sendSOAPCommand( 'localhost.localdomain', 20000, 'TrackerManager', 0, 'Halt' )
		xdglib.sendSOAPCommand( 'localhost', 10004, 'StorageManager', 0, 'Halt' )
		xdglib.sendSOAPCommand( 'localhost', 10002, 'evf::FUEventProcessor', 0, 'Halt' )
		xdglib.sendSOAPCommand( 'localhost', 10005, 'evf::FUEventProcessor', 1, 'Halt' )
		xdglib.sendSOAPCommand( 'localhost', 10003, 'evf::FUResourceBroker', 0, 'Halt' )
	
	def stopRun():
		xdglib.sendSOAPCommand( 'localhost', 10001, 'GlibStreamer', 0, 'stop' )
		xdglib.sendSOAPCommand( 'localhost', 10000, 'GlibSupervisor', 0, 'Halt' )
		xdglib.sendSOAPCommand( 'localhost', 10002, 'evf::FUEventProcessor', 0, 'Stop' )
		xdglib.sendSOAPCommand( 'localhost', 10005, 'evf::FUEventProcessor', 1, 'Stop' )
		xdglib.sendSOAPCommand( 'localhost', 10003, 'evf::FUResourceBroker', 0, 'Stop' )
		xdglib.sendSOAPCommand( 'localhost', 10000, 'GlibSupervisor', 0, 'Configure' )
		xdglib.sendSOAPCommand( 'localhost.localdomain', 20000, 'rubuilder::evm::Application', 0, 'Stop' )
		xdglib.sendSOAPCommand( 'localhost', 10001, 'rubuilder::ru::Application', 0, 'Stop' )
		xdglib.sendSOAPCommand( 'localhost', 10001, 'rubuilder::bu::Application', 0, 'Stop' )
	
	def startRun():
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
