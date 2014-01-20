#!/usr/local/bin/python

import sys, os, inspect, socket, time, signal
from CGIHandlerFromStrings import CGIHandlerFromStrings

directoryOfThisFile = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
BasePath = os.path.abspath(os.path.join(directoryOfThisFile, os.pardir, os.pardir))
sys.path.append( os.path.join( BasePath, "runcontrol" ) )
import SimpleGlibRun

class GlibControlService:
	"""
	Class that invokes the Glib control methods in response to JSON RPC calls.
	
	There should be no logic pertaining to the Glib here - this should solely
	pass on any commands that you want externally visible to the correct method
	in the python control library.
	
	@author Mark Grimes (mark.grimes@bristol.ac.uk)
	@date 11/Jan/2014
	"""
	def __init__(self):
		self.boardAddress = "192.168.0.175"
		self.program = SimpleGlibRun.SimpleGlibProgram( os.path.join( BasePath, "runcontrol", "GlibSuper.xml" ) )
		for context in self.program.contexts :
			context.forcedEnvironmentVariables = {'APVE_ROOT': '/opt/APVe',
				'CMSSW_BASE': '/home/xtaldaq/CBCAnalyzer/CMSSW_5_3_4',
				'CMSSW_RELEASE_BASE': '/home/xtaldaq/cmssw/slc5_amd64_gcc462/cms/cmssw/CMSSW_5_3_4',
				'CMSSW_SEARCH_PATH': '/home/xtaldaq/CBCAnalyzer/CMSSW_5_3_4/src:/home/xtaldaq/CBCAnalyzer/CMSSW_5_3_4/external/slc5_amd64_gcc462/data:/home/xtaldaq/cmssw/slc5_amd64_gcc462/cms/cmssw/CMSSW_5_3_4/src:/home/xtaldaq/cmssw/slc5_amd64_gcc462/cms/cmssw/CMSSW_5_3_4/external/slc5_amd64_gcc462/data',
				'CMSSW_VERSION': 'CMSSW_5_3_4',
				'ENV_CMS_TK_APVE_ROOT': '/home/xtaldaq/trackerDAQ-3.1//TrackerOnline/APVe',
				'ENV_CMS_TK_CAEN_ROOT': '/opt/xdaq',
				'ENV_CMS_TK_DIAG_ROOT': '/home/xtaldaq/trackerDAQ-3.1//DiagSystem',
				'ENV_CMS_TK_FEC_ROOT': '/home/xtaldaq/trackerDAQ-3.1//FecSoftwareV3_0',
				'ENV_CMS_TK_FED9U_ROOT': '/home/xtaldaq/trackerDAQ-3.1//TrackerOnline/Fed9U/Fed9USoftware',
				'ENV_CMS_TK_HAL_ROOT': '/opt/xdaq',
				'ENV_CMS_TK_HARDWARE_ROOT': '/opt/trackerDAQ',
				'ENV_CMS_TK_LTC_ROOT': '/opt/ttc-6.05.02/TTCSoftware',
				'ENV_CMS_TK_PARTITION': 'XY_10-JUN-2009_2',
				'ENV_CMS_TK_SBS_ROOT': '',
				'ENV_CMS_TK_TTCCI_ROOT': '/opt/ttc-6.05.02/TTCSoftware',
				'ENV_CMS_TK_TTC_ROOT': '/opt/ttc-6.05.02/TTCSoftware',
				'ENV_TRACKER_DAQ': '/home/xtaldaq/trackerDAQ-3.1/opt/trackerDAQ',
				'HOME': '/home/xtaldaq',
				'HOSTNAME': 'localhost.localdomain',
				'LD_LIBRARY_PATH': '/usr/local/lib:/opt/xdaq/lib:/opt/CBCDAQ/lib/:/home/xtaldaq/CBCAnalyzer/CMSSW_5_3_4/lib/slc5_amd64_gcc462:/home/xtaldaq/cmssw/slc5_amd64_gcc462/cms/cmssw/CMSSW_5_3_4/lib/slc5_amd64_gcc462/:/home/xtaldaq/cmssw/slc5_amd64_gcc462/cms/cmssw/CMSSW_5_3_4/external/slc5_amd64_gcc462/lib:/home/xtaldaq/cmssw/slc5_amd64_gcc462/external/gcc/4.6.2/lib64:/home/xtaldaq/cmssw/slc5_amd64_gcc462/lcg/root/5.32.00-cms17/lib',
				'POOL_OUTMSG_LEVEL': '4',
				'POOL_STORAGESVC_DB_AGE_LIMIT': '10',
				'PYTHONHOME': '/usr/lib64/python2.4',
				'PYTHONPATH': '/usr/lib64/python2.4:/home/xtaldaq/cmssw/slc5_amd64_gcc462/cms/cmssw/CMSSW_5_3_4/src:/home/xtaldaq/cmssw/slc5_amd64_gcc462/cms/cmssw/CMSSW_5_3_4/cfipython/slc5_amd64_gcc462',
				'ROOTSYS': '/home/xtaldaq/cmssw/slc5_amd64_gcc462/lcg/root/5.32.00-cms17/',
				'SCRATCH': '/tmp',
				'SEAL_PLUGINS': '/opt/cmsswLocal/module',
				'XDAQ_DOCUMENT_ROOT': '/opt/xdaq/htdocs',
				'XDAQ_ELOG': 'SET',
				'XDAQ_OS': 'linux',
				'XDAQ_PLATFORM': 'x86',
				'XDAQ_ROOT': '/opt/xdaq',
				'USER': 'xtaldaq'
			}
		
	def getStates(self, msg):
		"""
		Returns the states of all the active XDAQ applications as an array. Each element is
		itself a two element array of the application name and the state.
		"""
		try:
			results = []
			for context in self.program.contexts :
				for application in context.applications :
					results.append( [application.className,application.getState()] )
			return results
		except Exception as error:
			return "Exception: "+str(error)

	def connectedCBCNames(self, msg):
		"""
		Returns the names of the connected CBCs.
		"""
		return self.program.supervisor.connectedCBCNames()
	
	def I2CRegisterValues(self, msg):
		return self.program.supervisor.I2CRegisterValues(msg)
			
	def setI2CRegisterValues(self, msg):
		chipNames = msg.keys()
		registerNameValueTuple = msg[chipNames[0]]
		return self.program.supervisor.setI2c( registerNameValueTuple, chipNames )
		
	def startProcesses(self, msg):
		"""
		Starts all of the XDAQ processes
		"""
		try:
			self.program.startAllProcesses()
			return None
		except Exception as error:
			return "Exception: "+str(error)

	def killProcesses(self, msg):
		"""
		Kills all of the XDAQ processes
		"""
		try:
			self.program.killAllProcesses()
			return None
		except Exception as error:
			return "Exception: "+str(error)
	
	def boardIsReachable( self, msg ):
		"""
		Pings the board to see if it is available
		"""
		# return true or false depending on whether the board can be pinged
		return testStandTools.ping( self.boardAddress )


if __name__ == '__main__':	

	listeningAddress="/tmp/python_unix_sockets_example"
	
	if os.path.exists( listeningAddress ):
		os.remove( listeningAddress )
	
	#print "Opening socket..."
	server = socket.socket( socket.AF_UNIX, socket.SOCK_DGRAM )
	server.bind(listeningAddress)
	
	# Add a signal handler to remove the socket file if anyone sends a SIGTERM.
	# Ideally I would also do this if anyone sends a SIGKILL but SIGKILL can't
	# be caught.
	def signalHandler( signum, frame ) :
		server.close()
		os.remove( listeningAddress )
	signal.signal( signal.SIGTERM, signalHandler )
	
	try :
		logging=False
		myservice=CGIHandlerFromStrings(GlibControlService(),messageDelimiter="\n")
	
		#print "Listening..."
		while True:
			

			# First peek at the start of the message, i.e. look at it without removing it. I need to
			# see what size the message is so that I can then request using a correct buffer size.
			# The format I'm expecting is the process ID, then a space, then the message length, then
			# another space, then the message. The message length given doesn't include the extra bits
			# of information.
			packetSize=1024 # The size of the chunks I receive on the pipe
			datagram = server.recv( packetSize, socket.MSG_PEEK ) # Look but don't remove
			firstNewlinePosition=datagram.find('\n')
			secondNewlinePosition=datagram.find('\n',firstNewlinePosition+1)
			addressToReply=datagram[0:firstNewlinePosition]
			dataLength=int(datagram[firstNewlinePosition+1:secondNewlinePosition])
			messageLength=dataLength+secondNewlinePosition+1
			while packetSize < messageLength : packetSize=packetSize*2 # keep as a power of 2
			# Now that I have the correct packet size, I can get the full message and remove
			# it from the queue.
			datagram = server.recv( packetSize )
			message=datagram[secondNewlinePosition+1:]

			# I should have the full RPC message, so I can pass it on to the service to work
			# out what to do with it.
			response=myservice.handle( message )

			if logging :
				logFile=open('/tmp/serverDumpFile.log','a')
				logFile.write("REQUEST was:'"+datagram+"'\n")
				logFile.write("addressToReply was:'"+addressToReply+"'\n")
				logFile.write("messageLength was:'"+str(messageLength)+"'\n")
				logFile.write("RESPONSE is:'"+response+"'\n")
				logFile.flush()
				
			try :
				client = socket.socket( socket.AF_UNIX, socket.SOCK_DGRAM )
				client.connect( addressToReply )
				# First send the size of the response, then a space, then the actual response
				client.send( str(len(response))+'\n'+response )
				client.close()
				if logging: logFile.write('Respone has been written\n')
			except Exception as error:
				if logging : logFile.write("Exception: "+str(error)+str(error.args))
				print "Exception: "+str(error)+str(error.args)

			if logging : logFile.close()
		
		#print "-" * 20
		#print "Shutting down..."
		server.close()
		os.remove( listeningAddress )
	except :
		server.close()
		os.remove( listeningAddress )
		raise
	
