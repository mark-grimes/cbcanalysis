#!/usr/local/bin/python


if __name__ == '__main__':
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
	
	processID=os.getpid()
	response = socket.socket( socket.AF_UNIX, socket.SOCK_DGRAM )
	response.bind("/tmp/python_unix_sockets_response-"+str(processID))
	
	contLen=int(os.environ['CONTENT_LENGTH'])
	data = sys.stdin.read(contLen)
	data=str(processID)+" "+data
	client.send(data)
	
	packetSize=1024 # The size of the chunks I receive on the pipe
	datagram = response.recv( packetSize )
	firstSpacePosition=datagram.find(' ')
	messageLength=datagram[0:firstSpacePosition]
	message=datagram[firstSpacePosition+1:]
	file=open('/tmp/dumpFile','a')
	file.write(message)
	file.close()

	sys.stdout.write(message)

	# The message could be longer than the amount I've got, so I need to work out
	# how much is left.
	messageLength-=( packetSize-firstSpacePosition )
	while messageLength > 0 :
		datagram = response.recv( packetSize )
		file=open('/tmp/dumpFile','a')
		file.write(datagram)
		file.close()
		sys.stdout.write(datagram)
		messageLength-=packetSize

	
	client.close()
	response.close()
	os.remove("/tmp/python_unix_sockets_response-"+str(processID))

else:
	# this is if JSONService.py is run from mod_python:
	# rename .htaccess.mod_python to .htaccess to activate,
	# and restart Apache2
	raise Exception( "I haven't figured out how to run this from mod_python yet")
	#from jsonrpc.apacheServiceHandler import handler
