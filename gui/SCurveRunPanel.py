# Pyjamas panel to take an s-curve run.
#
# @author Mark Grimes (mark.grimes@bristol.ac.uk)
# @date 17/Jan/2014

from pyjamas.ui.HorizontalPanel import HorizontalPanel
from pyjamas.ui.HTML import HTML
from pyjamas.ui.VerticalPanel import VerticalPanel
from pyjamas.ui.FlowPanel import FlowPanel
from pyjamas.ui.DisclosurePanel import DisclosurePanel
from pyjamas.ui.ListBox import ListBox
from pyjamas.ui.Label import Label
from pyjamas.ui.TextBox import TextBox
from ErrorMessage import ErrorMessage
from pyjamas.ui.Button import Button

class SCurveRunPanel :
	
	class onClickListener :
		def __init__(self, panel) :
			self._ClickPanel=panel
			self._ClickPanel.launchButton.setEnabled(False)
			
		def onRemoteResponse(self, response, request_info):
			self._ClickPanel.launchButton.setEnabled(False)
			
		def onRemoteError(self, code, message, request_info):
			ErrorMessage( "Unable to contact server" )
			
	class controlSCurveValueListener :
		def __init__(self, panel) :
			self._controlPanel=panel
			#self._controlPanel.launchButton.setEnabled(False)
			#self._controlPanel.echoSelection()
			
		def onRemoteResponse(self, response, request_info):
			self._controlPanel.launchButton.setEnabled(False)
			self._controlPanel.echoSelection()
			
		def onRemoteError(self, code, message, request_info):
			ErrorMessage( "Unable to contact server" )
	
	def __init__( self, rpcService ) :
		# This is the service that will be used to communicate with the DAQ software
		self.rpcService = rpcService

		self.mainPanel = VerticalPanel()
		self.mainPanel.setSpacing(15)
		
		self.controlValueEntries={} #controls the parameters of the s-curve
		
		self.rpcService.getSCurveValues( )	
		
		self.mainSettings=DisclosurePanel("Control Settings")
		self.startButton=VerticalPanel("Run Button")
		
		self.mainSettings.add(self.createControlPanel(["RangeLo","RangeHi","Steps","FileName"]))
		
		
		self.echo=Label()
		
		
		self.launchButton=Button("Launch Now")
		self.launchButton.addClickListener(self, self.onClick())
		self.launchButton.setEnabled(True)
		
		self.mainPanel.add(self.mainSettings)
		self.mainPanel.add(self.startButton)
		self.mainPanel.add(self.launchButton)
		self.mainPanel.add(self.echo)
		
	
	def echoSelection(self): #fb - a good "print screen" method
		msg = " You pressed: "
		msg += str(self.controlValueEntries)
			
		self.echo.setText(msg)	
	
	def onChange( self, sender ) :
		#if sender==self.
		self.rpcService.getSCurveValues(self.controlValueEntries, SCurveRunPanel.controlSCurveValueListener(self))
		#self.echoSelection()		
		
	def onClick(self, sender):
		return 0
		#self.rpcService.getSCurveValues(0, SCurveRunPanel.onClickListener(self))	
		#self.echoSelection()	

		
	def getPanel(self) :
		return self.mainPanel
        
	def createControlPanel(self, controlNames):
		flowPanel=FlowPanel()
		newLabels=[]
		for buttonName in controlNames:
			newPanel=HorizontalPanel()
			newLabels.append(Label(buttonName))
			newPanel.add(newLabels[-1])
			newTextBox=TextBox()
			newTextBox.setEnabled(True)
			newTextBox.setWidth(80)
			newPanel.add(newTextBox)	
			
			if buttonName=="FileName":
				newTextBox.setText("TestRun.png")
			else: newTextBox.setText("0")
			newTextBox.addChangeListener(self)
			newTextBox.setTitle(buttonName) 
			
			self.controlValueEntries[buttonName]=newTextBox	
			
			flowPanel.add(newPanel)
		

		# Set all of the widths of the labels to be the same, so that the boxes line up
		maxWidth=0
		for label in newLabels :
			# This doesn't work for some reason
			#if label.getWidth() > maxWidth : maxWidth=label.getWidth()
			if len(label.getText())*9 > maxWidth : maxWidth=len(label.getText())*9
		for label in newLabels :
			label.setWidth(maxWidth)

		return flowPanel
		
	

	


