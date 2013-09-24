import xml.etree.ElementTree as ElementTree
import httplib, urllib
#import xdglib
import time
import os

class ETElementExtension( ElementTree._ElementInterface ) :
	"""
	Extension to the ElementTree element interface that adds methods to get children with
	a particular name, regardless of the xml namespace.
	
	Author Mark Grimes (mark.grimes@bristol.ac.uk)
	Date 28/Aug/2013
	"""
	def __init__( self, baseclass ) :
		self=baseclass
	def getchildrennamed( self, name ) :
		returnValue=[]
		for child in self.getchildren():
			splitByNamespace=child.tag.split("}")
			if len(splitByNamespace)==1 : tagname=splitByNamespace[0]
			elif len(splitByNamespace)==2 : tagname=splitByNamespace[1]
			if name==tagname :
				child.__class__=ETElementExtension
				returnValue.append( child )
		return returnValue
	def getchildnamed( self, name ) :
		""" Returns the first child with the supplied name (or None), ignoring xml namespaces. """
		result=self.getchildrennamed( name )
		if len(result)==0 : return None
		else : return result[0]

def sendSoapMessage( host, port, soapBody, className=None, instance=None ):
	"""
	Sends a soap message with the body provided to the host and port provided.
	No checking is provided that the soapBody provided is valid.
	
	If a className and instance are provided they are sent in the SOAPAction header. If either one is "None"
	then the SOAPAction header is "urn:xdaq-application:lid=10". No idea why, but that's what it was in xdglib

	Author Mark Grimes (mark.grimes@bristol.ac.uk) but heavily copied from a file called xdglib.py
	Date 16/Sep/2013
	"""
	message = """<?xml version="1.0" encoding="UTF-8"?>
	<SOAP-ENV:Envelope
	 SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"
	 xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
	 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
	 xmlns:xsd="http://www.w3.org/2001/XMLSchema"
	 xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/">
	<SOAP-ENV:Header>
	</SOAP-ENV:Header>
	<SOAP-ENV:Body>"""
	message += soapBody
	message += """</SOAP-ENV:Body>
	</SOAP-ENV:Envelope>"""
	
	if className==None or instance==None:	
		headers = {"Content-Type":"text/xml", "charset":"utf-8","Content-Description":"SOAP Message", "SOAPAction":"urn:xdaq-application:lid=10"}
		listeningUrl=host+":9999" # The port that the xdaq daemon listens on
	else:
		headers = {"Content-Type":"text/xml", "charset":"utf-8","Content-Description":"SOAP Message", "SOAPAction":"urn:xdaq-application:class="+className+",instance="+str(instance)}
		listeningUrl=host+":"+str(port)

	connection = httplib.HTTPConnection( listeningUrl )
	connection.request("POST", urllib.quote("/cgi-bin/query"), ElementTree.tostring( ElementTree.XML(message) ), headers )
	response = connection.getresponse()
	if (response.status != 200):
		connection.close()
		raise Exception( "Unable to send soap message because: "+str(response.status)+" - "+response.reason )
	data = response.read()
	connection.close()
	return data

def sendSoapStartCommand( host, port, configFilename ):
	xdglibEnvironmentVariables={
		"XDAQ_ROOT":"/opt/xdaq",
		"XDAQ_OS":"linux",
		"XDAQ_PLATFORM":"x86_64_slc5",
		"XDAQ_DOCUMENT_ROOT":"/opt/xdaq/htdocs",
		"XDAQ_ELOG":"SET",
		"ROOTSYS":"/home/xtaldaq/root/",
		"LD_LIBRARY_PATH":"/usr/local/lib:/opt/xdaq/lib:/opt/CBCDAQ/lib/:/home/xtaldaq/cmssw/slc5_amd64_gcc462/cms/cmssw/CMSSW_5_3_4/lib/slc5_amd64_gcc462/:/home/xtaldaq/cmssw/slc5_amd64_gcc462/cms/cmssw/CMSSW_5_3_4/external/slc5_amd64_gcc462/lib:/home/xtaldaq/cmssw/slc5_amd64_gcc462/external/gcc/4.6.2/lib64:/home/xtaldaq/cmssw/slc5_amd64_gcc462/lcg/root/5.32.00-cms17/lib",
		"PYTHONPATH":"/usr/lib64/python2.4:/home/xtaldaq/cmssw/slc5_amd64_gcc462/cms/cmssw/CMSSW_5_3_4/src:/home/xtaldaq/cmssw/slc5_amd64_gcc462/cms/cmssw/CMSSW_5_3_4/cfipython/slc5_amd64_gcc462",
		"PYTHONHOME":"/usr/lib64/python2.4",
		"CMSSW_SEARCH_PATH":"/home/xtaldaq/cmssw/slc5_amd64_gcc462/cms/cmssw/CMSSW_5_3_4/src/",
		"ENV_CMS_TK_FEC_ROOT":"/opt/trackerDAQ",
		"ENV_CMS_TK_FED9U_ROOT":"/opt/trackerDAQ",
		"ENV_CMS_TK_TTC_ROOT":"/opt/TTCSoftware",
		"ENV_CMS_TK_LTC_ROOT":"/opt/TTCSoftware",
		"ENV_CMS_TK_TTCCI_ROOT":"/opt/TTCSoftware",
		"HOME":"/home/xtaldaq",
		"ENV_CMS_TK_PARTITION":"XY_10-JUN-2009_2",
		"ENV_CMS_TK_CAEN_ROOT":"/opt/xdaq",
		"ENV_CMS_TK_HARDWARE_ROOT":"/opt/trackerDAQ",
		"ENV_CMS_TK_APVE_ROOT":"/opt/APVe",
		"ENV_CMS_TK_SBS_ROOT":"/opt/trackerDAQ",
		"ENV_CMS_TK_HAL_ROOT":"/opt/xdaq",
		"APVE_ROOT":"/opt/APVe",
		"ENV_CMS_TK_DIAG_ROOT":"/opt/trackerDAQ",
		"HOSTNAME":"localhost",
		"SCRATCH":"/tmp",
		"ENV_TRACKER_DAQ":"/opt/trackerDAQ",
		"SEAL_PLUGINS":"/opt/cmsswLocal/module",
		"CMSSW_BASE":"/home/xtaldaq/cmssw/slc5_amd64_gcc462/cms/cmssw/CMSSW_5_3_4",
		"CMSSW_VERSION":"CMSSW_5_3_4",
		"POOL_OUTMSG_LEVEL":"4",
		"POOL_STORAGESVC_DB_AGE_LIMIT":"10"}
	forcedEnvironmentVariables={"XDAQ_ELOG":"SET",
		"PYTHONHOME":"/usr/lib64/python2.4",
		#"PYTHONHOME":"/home/xtaldaq/cmssw/slc5_amd64_gcc462/external/python/2.6.4/lib/python2.6",
		#"PYTHONHOME":"/usr",
		#"PYTHONPATH":os.getenv("PYTHONPATH")+":/home/xtaldaq/cmssw/slc5_amd64_gcc462/external/python/2.6.4/lib/python2.6",
		"PYTHONPATH":"/usr/lib64/python2.4:/home/xtaldaq/cmssw/slc5_amd64_gcc462/cms/cmssw/CMSSW_5_3_4/src:/home/xtaldaq/cmssw/slc5_amd64_gcc462/cms/cmssw/CMSSW_5_3_4/cfipython/slc5_amd64_gcc462",
		"ENV_CMS_TK_PARTITION":"XY_10-JUN-2009_2",
		"ENV_CMS_TK_HARDWARE_ROOT":"/opt/trackerDAQ",
		"APVE_ROOT":"/opt/APVe",
		"SCRATCH":"/tmp",
		"SEAL_PLUGINS":"/opt/cmsswLocal/module",
		"POOL_OUTMSG_LEVEL":"4",
		"POOL_STORAGESVC_DB_AGE_LIMIT":"10",
		"XDAQ_ROOT":"/opt/xdaq",
		#"LD_LIBRARY_PATH":"/opt/xdaq/libs:/opt/CBCDAQ/lib"+os.getenv("LD_LIBRARY_PATH"),
		"LD_LIBRARY_PATH":"/usr/local/lib:/opt/xdaq/lib:/opt/CBCDAQ/lib/:/home/xtaldaq/CBCAnalyzer/CMSSW_5_3_4/lib/slc5_amd64_gcc462:/home/xtaldaq/cmssw/slc5_amd64_gcc462/cms/cmssw/CMSSW_5_3_4/lib/slc5_amd64_gcc462/:/home/xtaldaq/cmssw/slc5_amd64_gcc462/cms/cmssw/CMSSW_5_3_4/external/slc5_amd64_gcc462/lib:/home/xtaldaq/cmssw/slc5_amd64_gcc462/external/gcc/4.6.2/lib64:/home/xtaldaq/cmssw/slc5_amd64_gcc462/lcg/root/5.32.00-cms17/lib",
		"XDAQ_DOCUMENT_ROOT":"/opt/xdaq/htdocs"}
	requiredEnvironmentVariableNames=['XDAQ_ROOT',
		'XDAQ_OS',
		'XDAQ_PLATFORM',
		'XDAQ_DOCUMENT_ROOT',
		'XDAQ_ELOG',
		'ROOTSYS',
		'LD_LIBRARY_PATH',
		'PYTHONHOME',
		'PYTHONPATH',
		'CMSSW_SEARCH_PATH',
		'ENV_CMS_TK_FEC_ROOT',
		'ENV_CMS_TK_FED9U_ROOT',
		'ENV_CMS_TK_TTC_ROOT',
		'ENV_CMS_TK_LTC_ROOT',
		'ENV_CMS_TK_TTCCI_ROOT',
		'HOME',
		'ENV_CMS_TK_PARTITION',
		'ENV_CMS_TK_CAEN_ROOT',
		'ENV_CMS_TK_HARDWARE_ROOT',
		'ENV_CMS_TK_APVE_ROOT',
		'ENV_CMS_TK_SBS_ROOT',
		'ENV_CMS_TK_HAL_ROOT',
		'APVE_ROOT',
		'ENV_CMS_TK_DIAG_ROOT',
		'HOSTNAME',
		'SCRATCH',
		'ENV_TRACKER_DAQ',
		'SEAL_PLUGINS',
		'CMSSW_BASE',
		'CMSSW_RELEASE_BASE',
		'CMSSW_VERSION',
		'POOL_OUTMSG_LEVEL',
		'POOL_STORAGESVC_DB_AGE_LIMIT']
	environmentVariables={}
	for variableName in requiredEnvironmentVariableNames:
		try:
			environmentVariables[variableName]=forcedEnvironmentVariables[variableName]
		except KeyError:
			variable=os.getenv(variableName)
			if variable==None: raise Exception("Environment variable "+variableName+" has not been set and is not available from the current environment")
			environmentVariables[variableName]=variable
	
	# Now I have all of the environment variables figured out I can craft the message body
	soapBody = '<xdaq:startXdaqExe execPath="'+environmentVariables['XDAQ_ROOT']+'/bin/xdaq.exe" user="'+os.getenv("USER")+'" argv="-p '+str(port)+' -l INFO" xmlns:xdaq="urn:xdaq-soap:3.0" >\n'
	soapBody += '<EnvironmentVariable '
	
	environmentVariables=xdglibEnvironmentVariables
	environmentVariables["CMSSW_BASE"]=os.getenv("CMSSW_BASE")
	environmentVariables["CMSSW_RELEASE_BASE"]=os.getenv("CMSSW_RELEASE_BASE")
	environmentVariables["LD_LIBRARY_PATH"]=environmentVariables["CMSSW_BASE"]+"/lib/slc5_amd64_gcc462:"+environmentVariables["LD_LIBRARY_PATH"]
	environmentVariables["PYTHONPATH"]="/usr/lib64/python2.4:"+environmentVariables["CMSSW_BASE"]+"/python:"+environmentVariables["CMSSW_RELEASE_BASE"]+"/python:"+environmentVariables["CMSSW_RELEASE_BASE"]+"/cfipython/slc5_amd64_gcc462"
	
	for key in environmentVariables:
		soapBody+=key+'="'+environmentVariables[key]+'" '
	soapBody += """/>
	<ConfigFile>
	<![CDATA[\n"""
		
	configFile=open(configFilename)
	for line in configFile.readlines():
		soapBody += line
	  
	soapBody += """]]>
	</ConfigFile>
	</xdaq:startXdaqExe>"""
	
	return sendSoapMessage( host, port, soapBody )

		
class Context(object) :
	"""
	Class representing XDAQ Contexts, including all of the Applications in the Context.
	
	Author Mark Grimes (mark.grimes@bristol.ac.uk)
	Date 28/Aug/2013
	"""
	def __init__( self, elementTreeNode, configFilename ) :
		self.applications = []
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
					elif item[0]=="id" : id=item[1]
					elif item[0]=="instance" : instance=item[1]
				# Now try and create the Application object and add it to the return value
				newApplication=Application( self.host, int(self.port), className, int(instance), int(id) )
				self.applications.append( newApplication )

	def __repr__(self) :
		return "<XDAQ Context "+self.host+", "+str(self.port)+", "+str(self.jobid)+">"

	def startProcess(self) :
		self.jobid=-1
		#response=ElementTree.fromstring( xdglib.sendConfigurationStartCommand( "http://"+self.host+":"+self.port, self.configFilename ) )
		response=ElementTree.fromstring( sendSoapStartCommand( self.host, self.port, self.configFilename ) )
		try:
			response.__class__=ETElementExtension
			self.jobid = response.getchildnamed("Body").getchildnamed("jidResponse").getchildnamed("jid").text
		except:
			raise Exception( "Couldn't start process. Response was: "+ElementTree.tostring(response) )
		
	def killProcess(self) :
		if self.jobid==-1 :
			return False
		#response=ElementTree.fromstring( xdglib.sendConfigurationKillCommand( "http://"+self.host+":"+self.port, self.jobid ) )
		response=ElementTree.fromstring( sendSoapMessage( self.host, self.port, '<xdaq:killExec user="xtaldaq" jid="'+self.jobid+'" xmlns:xdaq="urn:xdaq-soap:3.0" />' ) )
		try:
			response.__class__=ETElementExtension
			reply=response.getchildnamed("Body").getchildnamed("getStateResponse").getchildnamed("reply").text
			if reply=='no job killed.' : return False
			elif reply=='killed by JID' :
				self.jobid=-1
				return True
		except:
			raise Exception( "Couldn't kill process. Response was: "+ElementTree.tostring(response) )

	def waitUntilProcessStarted( self, timeout=30.0 ) :
		"""
		Blocks until the process has started and all applications are contactable, or throws an exception if
		"timeout" seconds have passed.
		"""
		timeoutEndTime=time.time()+timeout;
		while True :
			allAplicationsStarted=True
			for application in self.applications:
				if application.getState()=="<uncontactable>": allAplicationsStarted=False
				if allAplicationsStarted: return
				if timeoutEndTime<time.time() : raise Exception("Context "+repr(self)+" did not start all applications within "+str(timeout)+" seconds.")
				time.sleep(0.5)

	def waitUntilProcessKilled( self, timeout=10.0 ) :
		"""
		Blocks until the process has stopped and all applications are uncontactable, or throws an exception if
		"timeout" seconds have passed.
		"""
		timeoutEndTime=time.time()+timeout;
		while True :
			allAplicationsStopped=True
			for application in self.applications:
				if application.getState()!="<uncontactable>": allAplicationsStopped=False
				if allAplicationsStopped: return
				if timeoutEndTime<time.time() : raise Exception("Context "+repr(self)+" did not kill all applications within "+str(timeout)+" seconds.")
				time.sleep(0.5)

class Application(object) :
	"""
	Class representing XDAQ Applications.
	
	Author Mark Grimes (mark.grimes@bristol.ac.uk)
	Date 28/Aug/2013
	"""
	def __init__(self, host, port, className, instance, id ) :
		self.host=host
		self.port=port
		self.className=className
		self.instance=instance
		self.id=id
		self.connection=httplib.HTTPConnection( self.host+":"+str(self.port) )
		# Make sure the connection is closed, because all the other methods assume
		# it's in that state. Presumably the connection will have failed at that
		# stage anyway.
		self.connection.close()

	def __repr__(self) :
		return "<XDAQ Application "+self.host+", "+str(self.port)+", "+self.className+", "+str(self.instance)+">"

	def sendCommand( self, command ) :
		return sendSoapMessage( self.host, self.port, '<xdaq:'+command+' xmlns:xdaq="urn:xdaq-soap:3.0"/>', self.className, self.instance )
		#return xdglib.sendSOAPCommand( self.host, self.port, self.className, self.instance, command )

	def getState(self) :
		try :
			result=ElementTree.fromstring( self.sendCommand('ParameterQuery') )
			result.__class__=ETElementExtension
			try :
				return result.getchildnamed("Body").getchildnamed("ParameterQueryResponse").getchildnamed("properties").getchildnamed("stateName").text
			except :
				return "<unknown>"
		except : return "<uncontactable>"

	def waitForState(self,state,timeout=5.0):
		"""
		Blocks until the state of the application has reached the one specified, or if "timeout" seconds
		have passed then an exception will be thrown. If timeout is negative then the application must
		already be in the desired state or the exception is thrown immediately.
		"""
		timeoutEndTime=time.time()+timeout;
		while True :
			if self.getState()==state : return
			if timeoutEndTime<time.time() : raise Exception("Application "+repr(self)+" did not reach state "+state+" within "+str(timeout)+" seconds.")
			time.sleep(0.2)
			
	def httpRequest( self, requestType, resource, parameters={}, storeMessage=True ) :
		"""
		Send an http request to the application to the resource specified, with
		optional parameters specified as a dictionary. "requestType" is the http
		type, e.g. "GET" or "POST".
		"""
		self.connection.connect()
		# I copied this from an example on stack overflow
		headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
		self.connection.request( requestType, urllib.quote(resource), urllib.urlencode(parameters), headers )
		response = self.connection.getresponse()
		if storeMessage:
			# I need to "read" the response message before the connection gets closed.
			# I'll store the message in a custom member of the response class that gets
			# returned to the user.
			response.fullMessage=response.read()
		self.connection.close()
		return response


class Program(object) :
	"""
	Class to control all XDAQ Contexts and Applications.
	
	Author Mark Grimes (mark.grimes@bristol.ac.uk)
	Date 29/Aug/2013
	"""
	def __init__( self, xdaqConfigFilename ) :
		self.xdaqConfigFilename = xdaqConfigFilename
		self._loadXDAQConfig()

	def _loadXDAQConfig( self ) :
		self.contexts = []
		tree=ElementTree.parse( self.xdaqConfigFilename )
		for node in tree.getroot().getchildren() :
			try :
				newContext=Context( node, self.xdaqConfigFilename )
				self.contexts.append( newContext )
			except Exception as error :
				# Some of these nodes might not be Contexts, so don't print any errors for those
				if( str(error)!="Not a Context node" ) :
					print "Unable to create context for node",str(node),"because",str(error)

	def reloadXDAQConfig( self ) :
		del self.contexts
		self._loadXDAQConfig()

	def startAllProcesses( self ) :
		for context in self.contexts:
			context.startProcess()

	def killAllProcesses( self ) :
		for context in self.contexts:
			context.killProcess()
			
	def waitUntilAllProcessesStarted( self, timeout=30.0 ) :
		startTime=time.time() # Since they don't run concurrently, I need to subtract previous waits
		for context in self.contexts:
			context.waitUntilProcessStarted( timeout-(time.time()-startTime) )
		# Add an arbitrary wait time because I've had cases where the process appears to be
		# running but the applications don't respond quite yet.
		time.sleep(2)

	def waitUntilAllProcessesKilled( self, timeout=10.0 ) :
		startTime=time.time() # Since they don't run concurrently, I need to subtract previous waits
		for context in self.contexts:
			context.waitUntilProcessKilled( timeout-(time.time()-startTime) )

	def sendAllCommand( self, command ) :
		for context in self.contexts :
			for application in context.applications :
				application.sendCommand( command )

	def printAllStates( self, hideComms=False ) :
		for context in self.contexts :
			firstApplication=True
			for application in context.applications :
				if (not hideComms) or application.className!="pt::atcp::PeerTransportATCP" :
					if firstApplication :
						contextString=context.host+":"+str(context.port)+" (job ID="+str(context.jobid)+")"
						firstApplication=False
					else : contextString=""
					print contextString.ljust(40)+application.className.ljust(30)+str(application.instance).rjust(4)+"   "+application.getState()

	def findAllMatchingApplications( self, className, instance=None ) :
		"""
		Returns an array of all the Applications that match the given className, and optional instance
		"""
		returnValue=[]
		for context in self.contexts :
			for application in context.applications :
				shouldAdd=False
				if application.className==className : shouldAdd=True
				if instance!=None :
					if instance!=application.instance : shouldAdd=False
				if shouldAdd : returnValue.append( application )
		return returnValue

	def sendAllMatchingApplicationsCommand( self, command, className, instance=None ) :
		matchingApps=self.findAllMatchingApplications( className, instance )
		for application in matchingApps :
			try:
				application.sendCommand( command )
			except:
				print "Unable to contact "+str(application)

	def waitAllMatchingApplicationsForState( self, state, timeout, className, instance=None ) :
		"""
		Blocks until all applications that match the specifics given reach the state given, or
		throws an exception if "timeout" seconds have elapsed.
		"""
		matchingApps=self.findAllMatchingApplications( className, instance )
		for application in matchingApps :
			try:
				application.waitForState( state, timeout )
			except Exception as error:
				print str(error)
