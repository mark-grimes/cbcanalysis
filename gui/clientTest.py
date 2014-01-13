# Client example from Amund Tveit's blog
# http://amundblog.blogspot.co.at/2008/12/ajax-with-python-combining-pyjs-and.html

# note: ui and JSONService were not prefixed with pyjamas, but that's needed
from pyjamas.ui.RootPanel import RootPanel
from pyjamas.ui.TextArea import TextArea
from pyjamas.ui.Label import Label
from pyjamas.ui.Button import Button
from pyjamas.ui.HTML import HTML
from pyjamas.ui.VerticalPanel import VerticalPanel
from pyjamas.ui.HorizontalPanel import HorizontalPanel
from pyjamas.ui.ListBox import ListBox
from pyjamas.JSONService import JSONProxy

class Client:
	def onModuleLoad(self):
		self.TEXT_WAITING = "Waiting for response..."
		self.TEXT_ERROR = "Server Error"

		# This is the remote service
		self.remote_server = UpperService()

		self.status=Label()
		self.getStates_py = Button("Query application states", self)
		self.startProcesses_py = Button("Start processes", self)
		self.killProcesses_py = Button("Kill processes", self)
		buttons = HorizontalPanel()
		buttons.add(self.getStates_py)
		buttons.add(self.startProcesses_py)
		buttons.add(self.killProcesses_py)
		buttons.setSpacing(8)
		info = r'First test of runcontrol GUI'
		panel = VerticalPanel()
		panel.add(HTML(info))
		panel.add(buttons)
		panel.add(self.status)
		RootPanel().add(panel)

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
			self.status.setText("Client exception was thrown: \""+str(error.__class__)+"\"=\""+str(error)+"\"")


	def onRemoteResponse(self, response, request_info):
		self.status.setText(response)

	def onRemoteError(self, code, message, request_info):
		self.status.setText("Server Error or Invalid Response: ERROR " + code )#+ " - " + message)

# AJAX calls must come from the same server, only the path is given here
class UpperService(JSONProxy):
	def __init__(self):
		JSONProxy.__init__(self, "services/GlibControlService.py", ["getStates","startProcesses","killProcesses"] )

if __name__ == "__main__" :
	app = Client()
	app.onModuleLoad()

