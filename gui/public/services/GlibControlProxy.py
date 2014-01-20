#!/usr/local/bin/python


if __name__ == '__main__':
	logging=False
	#	# this is if JSONService.py is run as a CGI
	#	from jsonrpc.cgihandler import handleCGIRequest
	#	handleCGIRequest(GlibControlService())
	import socket, os, sys, time
	if not os.path.exists( "/tmp/python_unix_sockets_example" ):
		# Server isn't running, so start it
		procID=os.spawnlp(os.P_NOWAIT, 'nohup', 'nohup', 'python2.6', '/home/xtaldaq/CBCAnalyzer/CMSSW_5_3_4/src/XtalDAQ/OnlineCBCAnalyser/gui/serverProcess/GlibControlService.py')
		time.sleep(1) # Sleep for a second to allow the new process to open the port
	
	client = socket.socket( socket.AF_UNIX, socket.SOCK_DGRAM )
	client.connect( "/tmp/python_unix_sockets_example" )
	
	listeningAddress="/tmp/python_unix_sockets_response-"+str(os.getpid())
	response = socket.socket( socket.AF_UNIX, socket.SOCK_DGRAM )
	response.bind( listeningAddress )
	
	contLen=int(os.environ['CONTENT_LENGTH'])
	data = sys.stdin.read(contLen)
	data=listeningAddress+"\n"+str(len(data))+"\n"+data
	client.send(data)
	
	packetSize=1024 # The size of the chunks I receive on the pipe
	datagram = response.recv( packetSize, socket.MSG_PEEK ) # Look but don't remove
	firstNewlinePosition=datagram.find('\n')
	dataLength=int(datagram[0:firstNewlinePosition])
	messageLength=dataLength+firstNewlinePosition+1
	while packetSize < messageLength : packetSize=packetSize*2 # keep as a power of 2
	# Now that I have the correct packet size, I can get the full message and remove
	# it from the queue.
	datagram = response.recv( packetSize )
	message=datagram[firstNewlinePosition+1:]
	if logging:
		logFile=open('/tmp/proxyDumpFile.log','a')
		logFile.write(message)

	sys.stdout.write(message)


	if logging: logFile.close()
	
	client.close()
	response.close()
	os.remove(listeningAddress)

else:
	# this is if JSONService.py is run from mod_python:
	# rename .htaccess.mod_python to .htaccess to activate,
	# and restart Apache2
	raise Exception( "I haven't figured out how to run this from mod_python yet")
	#from jsonrpc.apacheServiceHandler import handler
