#!/usr/local/bin/python

import sys, os, inspect
directoryOfThisFile = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
BasePath = os.path.abspath(os.path.join(directoryOfThisFile, os.pardir, os.pardir, os.pardir))
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
		return self.supervisor.setI2c( registerNameValueTuple, chipNames )
		
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
	# this is if JSONService.py is run as a CGI
	from jsonrpc.cgihandler import handleCGIRequest
	handleCGIRequest(GlibControlService())
else:
	# this is if JSONService.py is run from mod_python:
	# rename .htaccess.mod_python to .htaccess to activate,
	# and restart Apache2
	from jsonrpc.apacheServiceHandler import handler
