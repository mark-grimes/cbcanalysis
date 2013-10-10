#ifndef XtalDAQ_OnlineCBCAnalyser_plugins_OccupancyDQM_h
#define XtalDAQ_OnlineCBCAnalyser_plugins_OccupancyDQM_h

#include <mutex>
#include <FWCore/Framework/interface/Frameworkfwd.h>
#include <FWCore/Framework/interface/EDAnalyzer.h>
#include "XtalDAQ/OnlineCBCAnalyser/interface/HttpServer.h"


namespace cbcanalyser
{
	/** @brief Analyser that records a rolling occupancy for the last <n> events and presents the results
	 * on a webpage.
	 *
	 * The hostname and port to try and run the server on is given in the config ParameterSet, as well
	 * as the number of events to calculate the occupancy.
	 *
	 * @author Mark Grimes (mark.grimes@bristol.ac.uk)
	 * @date 09/Oct/2013
	 */
	class OccupancyDQM : public edm::EDAnalyzer, public httpserver::HttpServer::IRequestHandler
	{
	public:
		explicit OccupancyDQM( const edm::ParameterSet& config );
		~OccupancyDQM();

		//static void fillDescriptions( edm::ConfigurationDescriptions& descriptions );
	private:
		//virtual void beginJob();
		virtual void analyze( const edm::Event& event, const edm::EventSetup& setup );
		//virtual void endJob();

		//virtual void beginRun( const edm::Run& run, const edm::EventSetup& setup );
		//virtual void endRun( const edm::Run& run, const edm::EventSetup& setup );
		//virtual void beginLuminosityBlock( const edm::LuminosityBlock& lumiBlock, const edm::EventSetup& setup );
		//virtual void endLuminosityBlock( const edm::LuminosityBlock& lumiBlock, const edm::EventSetup& setup );

		/** @brief The handler that server_ will call when a HTTP request comes in. */
		virtual void handleRequest( const httpserver::HttpServer::Request& request, httpserver::HttpServer::Reply& reply );
	protected:
		httpserver::HttpServer server_;
		std::mutex serverMutex_; ///< Mutex to stop the server reading while the analyze method is writing.
	private:
		// I've got a few utility classes that are only visible in the .cc file, so
		// I need to use a pImple.
		std::unique_ptr<class OccupancyDQMPrivateMembers> pImple;
	};

} // end of namespace cbcanalyser

#endif
