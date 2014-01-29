#!/usr/local/bin/python

# RPC service that takes any commands and pipes them through to another script, listens for
# for the response and then returns it. This is all done over Unix sockets. If the script
# that it wants to pipe to isn't running, then it starts it.
#
# This is a bit over complicated, but apache starts this script in a new process for each
# request. Hence it cannot have persistent state. To get around this it starts the other
# script which runs permanently and communicates with that.
#
# @author Mark Grimes (mark.grimes@bristol.ac.uk)
# @date 17/Jan/2014

# The "os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))" part of
# this line gets the directory of this file. I then look three parents up to get the directory
# of the CBCAnalysis installation.
INSTALLATION_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))), os.pardir, os.pardir))

if __name__ == '__main__':
	# The important settings.
	logging=False      # Whether to dump debugging information to a log.
	sendAddress="/tmp/CBCTestStand_rpc_server"  # The socket address that the receiving script listens on
	# The script that will answer my requests
	receivingScript=INSTALLATION_PATH+"/gui/serverProcess/GlibControlService.py"
	
	#	# this is if JSONService.py is run as a CGI
	#	from jsonrpc.cgihandler import handleCGIRequest
	#	handleCGIRequest(GlibControlService())
	import socket, os, sys, time
	if not os.path.exists( sendAddress ):
		# Server isn't running, so start it
		procID=os.spawnlp(os.P_NOWAIT, 'nohup', 'nohup', 'python2.6', receivingScript )
		time.sleep(1) # Sleep for a second to allow the new process to open the port
	
	client = socket.socket( socket.AF_UNIX, socket.SOCK_DGRAM )
	client.connect( sendAddress )
	
	listeningAddress="/tmp/CBCTestStand_rpc_server_response-"+str(os.getpid())
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
