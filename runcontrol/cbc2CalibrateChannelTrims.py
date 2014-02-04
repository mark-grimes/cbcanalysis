"""
@brief Example script to calibrate the channel trims on a CBC2

@author Mark Grimes (mark.grimes@bristol.ac.uk)
@date 23/Jan/2014
"""

from pythonlib.SimpleGlibProgram import SimpleGlibProgram
from pythonlib.AnalyserControl import AnalyserControl
from cbc2SCurveRun import cbc2SCurveRun


def takeRun( targets, thresholdRange ) :
	analysisControl.reset()
	cbc2SCurveRun( daqProgram, analysisControl, thresholdRange, silent=False )
	#analysisControl.restoreFromRootFile( "/tmp/newHistograms.root" )
	fitParameters=analysisControl.fitParameters()
	for target in targets :
		channelNumber=target['channelNumber']
		cbcName=target['cbcName']
		target['previousResults'].append(
			{'trim':daqProgram.supervisor.getChannelTrim(channelNumber,[cbcName]),
			'mean':fitParameters[cbcName][channelNumber]['mean'] }
		)

def simpleLinearFit( xCoords, yCoords ) :
	"""
	Simple linear fit. Didn't want to bring in an external dependency for something so simple.
	"""
	if len(xCoords)!=len(yCoords) : raise Exception( "simpleLinearFit - the xCoords and yCoords arrays need to be the same size")
	if len(xCoords)<2 : raise Exception( "simpleLinearFit - you need at least two datapoints")
	xyBar=0.0
	xBar=0.0
	yBar=0.0
	xSquaredBar=0.0
	for index in range(0,len(xCoords)) :
		xyBar+=(xCoords[index]*yCoords[index])
		xBar+=xCoords[index]
		yBar+=yCoords[index]
		xSquaredBar+=(xCoords[index]*xCoords[index]);
	xyBar/=len(xCoords)
	xBar/=len(xCoords)
	yBar/=len(xCoords)
	xSquaredBar/=len(xCoords)
	
	slope=(xyBar-xBar*yBar)/(xSquaredBar-xBar*xBar);
	intercept=yBar-slope*xBar;
	return {'slope':slope,'intercept':intercept}

def fitPreviousResults( target ) :
	xCoords=[]
	yCoords=[]
	for previousResult in target['previousResults'] :
		xCoords.append( previousResult['trim'] )
		yCoords.append( previousResult['mean'] )
	# If there is only one point then add (0,0)
	if len(xCoords)==1 :
		xCoords.append(0)
		yCoords.append(0)
	return simpleLinearFit( xCoords, yCoords )

def setToBestPreviousResult( target ) :
	closestdifferenceFromTarget=9999
	newTrim=-1
	newMean=-1
	for previousResult in target['previousResults'] :
		differenceFromTarget=abs( target['target']-previousResult['mean'] )
		if differenceFromTarget<closestdifferenceFromTarget :
			newTrim=previousResult['trim'] # This previous result is better so use that
			closestdifferenceFromTarget=differenceFromTarget
			newMean=previousResult['mean'] # store this so that I can return it for info
	if newTrim==-1 : raise Exception( "Unable to find a previous trim result")
	daqProgram.supervisor.setChannelTrim(target['channelNumber'],newTrim,[target['cbcName']])
	# Return the trim and the mean you get from it in case the caller is intersted
	return {'trim':newTrim,'mean':newMean}
	
def setNewTrims( targets ) :
	# This will be filled with things to take out of the targets array,
	# either because the target has been met or because it looks like
	# a dead channel.
	targetsToRemove=[]
	
	for target in targets :
		# First see if the last iteration was successful
		if int(target['previousResults'][-1]['mean']+0.5)==target['target'] : # Add .5 to round properly
			targetsToRemove.append(target) # Found the trim, so no longer consider this
			continue
		# Look at all the previous results and try a linear fit to estimate
		# a trim that will give the relationship between trim and mean.
		fit=fitPreviousResults( target )
		# If the fit is exactly flat then the channel is probably dead
		# I'll take it out of the targets, but I can't remove it mid-loop.
		if fit['slope']==0 :
			targetsToRemove.append( target )
			continue
		#print "Slope="+str(fit['slope'])+" intercept="+str(fit['intercept'])
		# invert y=mx+c to get x=(y-c)/m
		newTrim=int( (target['target']-fit['intercept'])/fit['slope'] + 0.5 ) # add .5 to round properly
		if newTrim<0 : newTrim=0
		elif newTrim>255 : newTrim=255
		# Look through the previous results to make sure I haven't tried
		# this trim before.
		newTrimHasAlreadyBeenTried=True # Set to true to get it in the loop for the first time
		modificationDirection=0 # I'll set this to -1 if decreasing the trim, +1 if increasing, 0 if undefined
		while newTrimHasAlreadyBeenTried :
			newTrimHasAlreadyBeenTried=False
			for previousResult in target['previousResults'] :
				if previousResult['trim']==newTrim :
					if previousResult['mean']>target['target'] : directionToChange=1
					else : directionToChange=-1
					# If modificationDirection is not zero then I've changed the trim at least
					# once. If the direction to change this time is different to the previous
					# one then I'm not able to find a matching trim. Just set to the best match
					# and remove it from the list of channels to calibrate
					if modificationDirection!=0 and modificationDirection!=directionToChange :
						targetsToRemove.append(target)
						newTrim=-1 # Set this to something invalid so that I can check it later
						break
					else :
						modificationDirection=directionToChange
						newTrim+=modificationDirection
						newTrimHasAlreadyBeenTried=True
			
		#print "Setting trim for ["+target['cbcName']+"]["+str(target['channelNumber'])+"]="+str(newTrim)
		if newTrim!=-1 : daqProgram.supervisor.setChannelTrim(target['channelNumber'],newTrim,[target['cbcName']])
		else : setToBestPreviousResult(target)
		
	# Now I've finished looping over targets I can safely take
	# out the entries I want to.
	for item in targetsToRemove :
		targets.remove( item )


def cbc2CalibrateChannelTrims( daqProgram, analysisControl, scanRange, midPointTarget, interimOutputFilename=None, maxLoops=10 ) :
	"""
	Tries to calibrate the channel trims on all the connected CBCs so that the midpoint
	of their s-curves sits on mitPointTarget.
	
	If interimOutputFilename is not 'None' then the files from each loop willbe saved to
	files and directories starting with that name.
	
	@author Mark Grimes (mark.grimes@bristol.ac.uk)
	@date 24/Jan/2014
	"""
	# Before making any changes to the CBC I2C parameters I have to initialise
	# the CBC information in the control program. This isn't in the __init__
	# because it requires starting the XDAQ process which might not be what the
	# user wants
	daqProgram.initialiseCBCs()

	# Set up the targets that I want the channels to be on. This is where I want the midpoint
	# of the s-curve to sit.
	targets=[]
	for cbcName in daqProgram.supervisor.connectedCBCNames() :
		for channelNumber in range(0,254) :
			targets.append( {'cbcName':cbcName, 'channelNumber':channelNumber, 'target':midPointTarget, 'previousResults':[] } )

	loop=0
	scurvesAlign = False
	
	# I perform linear fits of the previous results to estimate what the trim to be.
	# For this to work I'll start off taking one run with very low trims and with
	# high trims so that I have enough data points for the fit.
		
	# Take a run a quarter of the way along the range
	for target in targets :
		daqProgram.supervisor.setChannelTrim(target['channelNumber'],63,[target['cbcName']])
	print "Taking run with trims at 1/4"
	takeRun( targets, range(50,150) )
	if interimOutputFilename!=None : analysisControl.saveHistograms( interimOutputFilename+"-low.root" )
	
	# Take a run a quarter from the end of the range
	for target in targets :
		daqProgram.supervisor.setChannelTrim(target['channelNumber'],191,[target['cbcName']])
	print "Taking run with trims at 3/4"
	takeRun( targets, range(50,150) )
	if interimOutputFilename!=None : analysisControl.saveHistograms( interimOutputFilename+"-high.root" )
	
	# For debugging print the results
	#print "Results after high and low scans"
	#for target in targets :
	#	print target
		
	setNewTrims( targets )
	#print "Trims set to"
	#for target in targets :
	#	channelNumber=target['channelNumber']
	#	cbcName=target['cbcName']
	#	trim=daqProgram.supervisor.getChannelTrim(channelNumber,[cbcName])
	#	print cbcName+"["+str(channelNumber)+"]="+str(trim)


	while not scurvesAlign :
		loop+=1
		print "Starting loop "+str(loop)+". Channels still to calibrate="+str(len(targets))
		for target in targets :
			print target
		takeRun( targets, scanRange )
		setNewTrims( targets )
		if interimOutputFilename!=None : analysisControl.saveHistograms( interimOutputFilename+"-loop"+str(loop)+".root" )
		# Might as well save the trims as I go in case something goes wrong
		if interimOutputFilename!=None : daqProgram.supervisor.saveI2c( interimOutputFilename+"-loop"+str(loop) )
		# Decide whether to drop out or not
		if len(targets)==0 : scurvesAlign=True
		elif loop>maxLoops :
			# Create a message to let the user know which channels failed. Any channels
			# that have converged will have been taken out of the targets array.
			failMessage="Reached "+str(maxLoops)+" loops and the s-curves for channels "
			for failedTarget in targets :
				bestResult=setToBestPreviousResult( failedTarget )
				failMessage+=failedTarget['cbcName']+"["+str(failedTarget['channelNumber'])+"] (managed to calibrate to "+str(bestResult['mean'])+"), "
			failMessage+="failed to converge."
			print failMessage
			scurvesAlign=True


if __name__ == '__main__':
	daqProgram = SimpleGlibProgram( "GlibSuper.xml" )
	analysisControl = AnalyserControl( "127.0.0.1", "50000" )
	
	cbc2CalibrateChannelTrims( daqProgram, analysisControl, range(100,150), 127, "/tmp/calibrateChannelTrims" )
	
	print "Saving calibrated trims to '/tmp/calibratedTrims'"
	daqProgram.supervisor.saveI2c( "/tmp/calibratedTrims" )
