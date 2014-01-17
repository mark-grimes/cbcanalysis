# Pyjamas panel to instigate a quick 100 event run and report back the occupancies.
#
# @author Mark Grimes (mark.grimes@bristol.ac.uk)
# @date 17/Jan/2014

from pyjamas.ui.VerticalPanel import VerticalPanel
from pyjamas.ui.HTML import HTML
from ErrorMessage import ErrorMessage

class OccupancyCheckPanel :
	def __init__( self, rpcService ) :
		# This is the service that will be used to communicate with the DAQ software
		self.rpcService = rpcService
		
		# The main panel that everythings will be insided
		self.mainPanel = VerticalPanel()
		self.mainPanel.add( HTML("Still need to add all of the interface elements for this.") )
		#self.mainPanel.setSpacing(10)

	def getPanel( self ) :
		return self.mainPanel
	


