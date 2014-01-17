# Client example from Amund Tveit's blog
# http://amundblog.blogspot.co.at/2008/12/ajax-with-python-combining-pyjs-and.html

# note: ui and JSONService were not prefixed with pyjamas, but that's needed
from pyjamas import Window
from pyjamas.ui.RootPanel import RootPanel
from pyjamas.ui.DockPanel import DockPanel
from pyjamas.ui.DisclosurePanel import DisclosurePanel
from pyjamas.ui.TextArea import TextArea
from pyjamas.ui.Label import Label
from pyjamas.ui.Button import Button
from pyjamas.ui.HTML import HTML
from pyjamas.ui.VerticalPanel import VerticalPanel
from pyjamas.ui.HorizontalPanel import HorizontalPanel
from pyjamas.ui.FlowPanel import FlowPanel
from pyjamas.ui.ListBox import ListBox
from pyjamas.ui.TextBox import TextBox
from pyjamas.JSONService import JSONProxy
from pyjamas.ui.CSS import StyleSheetCssFile
from pyjamas.ui.DialogBox import DialogBox
from I2CPanel import I2CPanel
from OccupancyCheckPanel import OccupancyCheckPanel
from SCurveRunPanel import SCurveRunPanel

from ErrorMessage import ErrorMessage

class Client:
	def onModuleLoad(self):
		#Window.setTitle("CBC Test Stand")
		StyleSheetCssFile("styleSheet.css")
		
		self.TEXT_WAITING = "Waiting for response..."
		self.TEXT_ERROR = "Server Error"

		self.status=Label()
		
		# This is the remote service
		self.remote_server = GlibControlService()
		self.I2CPanel=I2CPanel(self.remote_server)
		self.SCurveRunPanel=SCurveRunPanel(self.remote_server)
		self.OccupancyCheckPanel=OccupancyCheckPanel(self.remote_server)

		# mainPanel will have all of the working stuff in it
		self.mainPanel=DockPanel()
		#self.mainPanel.setSpacing(10)
		self.mainPanel.add( HTML(r"CBC Test Stand", StyleName="titleStyle"), DockPanel.NORTH )
		selectionPanel=VerticalPanel()
		
		self.activePanelButton=None
		self.activePanel=None

		self.registersButton=Label("I2C Registers", StyleName="areaStyle")
		self.occupanciesButton=Label("Test Occupancies", StyleName="areaStyle")
		self.scurveButton=Label("S-Curve Run", StyleName="areaStyle")

		self.registersButton.addClickListener( self )
		self.scurveButton.addClickListener( self )
		self.occupanciesButton.addClickListener( self )
		
		selectionPanel.add( self.registersButton )
		selectionPanel.add( self.occupanciesButton )
		selectionPanel.add( self.scurveButton )

		self.mainPanel.add( selectionPanel, DockPanel.WEST )
		
#		self.I2CPanel.getPanel().setStyleName("selectedAreaStyle")
#		self.mainPanel.add( self.I2CPanel.getPanel(), DockPanel.CENTER )
				
		self.mainPanel.add( self.status, DockPanel.SOUTH )
		RootPanel().add(self.mainPanel)

		self.setNewMainPanel( self.registersButton )
		
#		try:
#			if self.remote_server.I2CRegisterValues( None, self ) < 0:
#				self.status.setText(self.TEXT_ERROR)
#			else : self.status.setText( "Message sent" )
#
#		except Exception as error:
#			self.status.setText("Client exception was thrown: '"+str(error.__class__)+"'='"+str(error)+"'")
		
	def onClick(self, sender):
		# (data, response_class): if the latter is 'self', then
		# the response is handled by the self.onRemoteResponse() method
		try:
			self.setNewMainPanel( sender )
#			if sender == self.getStates_py :
#				if self.remote_server.getStates( None, self ) < 0:
#					self.status.setText(self.TEXT_ERROR)
#			elif sender == self.startProcesses_py :
#				if self.remote_server.startProcesses( None, self ) < 0:
#					self.status.setText(self.TEXT_ERROR)
#			elif sender == self.killProcesses_py :
#				if self.remote_server.killProcesses( None, self ) < 0:
#					self.status.setText(self.TEXT_ERROR)

		except Exception as error:
			self.status.setText("Client exception was thrown: '"+str(error.__class__)+"'='"+str(error)+"'")

	def setNewMainPanel( self, panelButton ) :
		if panelButton == self.activePanelButton : return # already the active panel so no need to do anything
		
		# Remove the "selected" style from the current button
		if self.activePanelButton!=None : self.activePanelButton.setStyleName( "areaStyle" )
		
		# Set the "selected" style on the new one
		self.activePanelButton=panelButton
		self.activePanelButton.setStyleName( "selectedAreaStyle" )
		
		# Clear the main panel
		if self.activePanel!=None :
			self.mainPanel.remove( self.activePanel.getPanel() )
		
		# Figure out what the new main panel should be
		if panelButton==self.registersButton : self.activePanel=self.I2CPanel
		elif panelButton==self.scurveButton : self.activePanel=self.SCurveRunPanel
		elif panelButton==self.occupanciesButton : self.activePanel=self.OccupancyCheckPanel
		
		# Set the new main panel
		self.activePanel.getPanel().setStyleName( "selectedAreaStyle" )
		self.mainPanel.add( self.activePanel.getPanel(), DockPanel.CENTER )

	def onRemoteResponse(self, response, request_info):
		self.status.setText(response)

	def onRemoteError(self, code, message, request_info):
		ErrorMessage( "Unable to contact server" )

# AJAX calls must come from the same server, only the path is given here
class GlibControlService(JSONProxy):
	def __init__(self):
		JSONProxy.__init__(self, "services/GlibControlProxy.py", ["getStates","connectedCBCNames","I2CRegisterValues","setI2CRegisterValues","startProcesses","killProcesses","boardIsReachable"] )

if __name__ == "__main__" :
	app = Client()
	app.onModuleLoad()

