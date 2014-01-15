# Client example from Amund Tveit's blog
# http://amundblog.blogspot.co.at/2008/12/ajax-with-python-combining-pyjs-and.html

# note: ui and JSONService were not prefixed with pyjamas, but that's needed
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
from I2CPanel import I2CPanel

class Client:
	def onModuleLoad(self):
		self.TEXT_WAITING = "Waiting for response..."
		self.TEXT_ERROR = "Server Error"

		self.status=Label()
		
		# This is the remote service
		self.remote_server = GlibControlService()
		self.I2CPanel=I2CPanel(self.remote_server)

		# mainPanel will have all of the working stuff in it
		self.mainPanel=DockPanel()
		self.mainPanel.setSpacing(10)
		self.mainPanel.add( HTML(r"CBC Test Stand"), DockPanel.NORTH )
		
		self.mainPanel.add( Label("I2C Registers"), DockPanel.WEST )
		
		self.mainPanel.add( self.I2CPanel.getPanel(), DockPanel.CENTER )
		
		
		self.mainPanel.add( self.status, DockPanel.SOUTH )
		RootPanel().add(self.mainPanel)

#		try:
#			if self.remote_server.I2CRegisterValues( None, self ) < 0:
#				self.status.setText(self.TEXT_ERROR)
#			else : self.status.setText( "Message sent" )
#
#		except Exception as error:
#			self.status.setText("Client exception was thrown: '"+str(error.__class__)+"'='"+str(error)+"'")
		
	def onClick(self, sender):
		self.status.setText(self.TEXT_WAITING)
		# (data, response_class): if the latter is 'self', then
		# the response is handled by the self.onRemoteResponse() method
		try:
			if sender == self.getStates_py :
				if self.remote_server.getStates( None, self ) < 0:
					self.status.setText(self.TEXT_ERROR)
			elif sender == self.startProcesses_py :
				if self.remote_server.startProcesses( None, self ) < 0:
					self.status.setText(self.TEXT_ERROR)
			elif sender == self.killProcesses_py :
				if self.remote_server.killProcesses( None, self ) < 0:
					self.status.setText(self.TEXT_ERROR)

		except Exception as error:
			self.status.setText("Client exception was thrown: '"+str(error.__class__)+"'='"+str(error)+"'")


	def onRemoteResponse(self, response, request_info):
		self.status.setText(response)

	def onRemoteError(self, code, message, request_info):
		self.status.setText("Server Error or Invalid Response: ERROR " + code )#+ " - " + message)

# AJAX calls must come from the same server, only the path is given here
class GlibControlService(JSONProxy):
	def __init__(self):
		JSONProxy.__init__(self, "services/GlibControlService.py", ["getStates","connectedCBCNames","I2CRegisterValues","startProcesses","killProcesses","boardIsReachable"] )

if __name__ == "__main__" :
	app = Client()
	app.onModuleLoad()

