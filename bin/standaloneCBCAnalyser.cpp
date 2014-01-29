/** @file
 *
 * @brief An executable that opens a port given on the command line and listens for instructions.
 *
 * I can't get the full DAQ chain working at the moment (RU -> BU -> my FUEventProcessor) but I can
 * successfully dump from the GlibStreamer to disk and read it back. Instead of running analysis code
 * in an FUEventProcessor I'll run it in this executable and feed it the DAQ dumps. I'll try and put
 * as much code as possible in utility classes so that it can be transferred to a FUEventProcessor at
 * a later date if required.
 *
 * This executable opens a port and listens for instructions in the form of HTTP GET requests. I'll
 * have a python script performing the runcontrol which will instigate runs which dump a file, and
 * then instruct this program to open the file and analyse it. The python script will then query
 * the results and decide what to do next.
 *
 * I chose not to analyse in the python script because I want any analysis code to be useable from
 * XDAQ and CMSSW.
 *
 * @author Mark Grimes (mark.grimes@bristol.ac.uk)
 * @date 06/Jan/2014
 */

#include <iostream>
#include <fstream>
#include <stdexcept>
#include <sstream>
#include <iomanip>

#include "SLHCUpgradeTracker/CBCAnalysis/interface/RawDataFileReader.h"
#include "SLHCUpgradeTracker/CBCAnalysis/interface/HttpServer.h"
#include "SLHCUpgradeTracker/CBCAnalysis/interface/SCurve.h"
#include "TFile.h"

// Use the unnamed namespace for things only used in this file
namespace
{
	/** @brief Class that handles the HTTP requests.
	 *
	 * Most of the functionality is in here.
	 *
	 * @author Mark Grimes (mark.grimes@bristol.ac.uk)
	 * @date 06/Jan/2014
	 */
	class HttpRequestHandler : public httpserver::HttpServer::IRequestHandler
	{
	public:
		HttpRequestHandler() : threshold_(0) {}
		virtual ~HttpRequestHandler() {}
		virtual void handleRequest( const httpserver::HttpServer::Request& request, httpserver::HttpServer::Reply& reply );
	protected:
		void openDAQDumpFile( const std::string& filename );
		cbcanalyser::FedSCurves connectedCBCSCurves_;
		float threshold_;
	};

} // end of the unnamed namespace


int main( int argc, char* argv[] )
{
	if( argc!=2 )
	{
		std::cout << "Program to analyse DAQ dump files from GlibStreamer." << "\n"
				<< "\n"
				<< "Usage:       " << argv[0] << " <port number>" << "\n"
				<< "   Starts a server listening on the given port. This listens for instructions in the form of" << "\n"
				<< "   HTTP GET requests. To see a list of the commands point a webbrowser at the running server." << "\n"
				<< std::endl;

		return -1;
	}

	try
	{
		HttpRequestHandler handler;
		httpserver::HttpServer server( handler );
		server.start( "127.0.0.1", argv[1] );

		std::cout << "Server started at 127.0.0.1 on port " << argv[1] << std::endl;

		server.blockUntilFinished();
	}
	catch( std::exception& error )
	{
		std::cerr << "An exception occurred: " << error.what() << std::endl;
		return -1;
	}

	return 0;
}

//
// Definitions of things declared in the unnamed namespace
//
namespace
{
	void HttpRequestHandler::handleRequest( const httpserver::HttpServer::Request& request, httpserver::HttpServer::Reply& reply )
	{
		//
		// First split up the URI in the request into the resource and parameter
		// names and values.
		//
		std::string resource;
		std::vector< std::pair<std::string,std::string> > parameters;
		httpserver::HttpServer::splitURI( request.uri, resource, parameters );

		std::stringstream output;

		for( const auto& paramValuePair : parameters )
		{
			if( paramValuePair.first=="debug" )
			{
				output << "Raw string=\"" << request.uri << "\"" << "\n";
				output << "Your request was \"" << resource << "\" with " << parameters.size() << " parameters" << "\n";
				for( const auto& paramValuePair : parameters )
				{
					output << "   " << paramValuePair.first << " = " << "\"" << paramValuePair.second << "\""<< "\n";
				}
				output << "\n";
			}
		}


		if( resource=="/" )
		{
			output << "Available commands (case sensitive):" << "\n"
					<< "   analyseFile?filename=<filename>          Analyses the file with the supplied filename." << "\n"
					<< "   restoreFromRootFile?filename=<filename>  Restores the data from a file previously saved with saveHistograms." << "\n"
					<< "   setThreshold?value=<value>               Sets the current threshold (the abscissa for all plots) to the specified value." << "\n"
					<< "   saveHistograms?filename=<filename>       Save the histograms in their current state to the specified file. If it already" << "\n"
					<< "                                            exists it will be overwritten." << "\n"
					<< "   version                                  States the version of this code." << "\n"
					<< "   reset                                    Resets any data taken." << "\n"
					<< "\n"
					<< "You can add the parameter \"debug\" to any command to echo your request."
					<< "\n";
		}
		else if( resource=="/analyseFile" || resource=="/analyzeFile" )
		{
			output << "analyseFile called" << "\n";
			// Look through the parameters and try and find the filename to open
			std::string filename;
			for( const auto& paramValuePair : parameters ) if( paramValuePair.first=="filename" ) filename=paramValuePair.second;

			if( filename.empty() ) output << "Error! no filename was supplied, or it's empty." << "\n";
			else
			{
				try
				{
					openDAQDumpFile( filename );
				}
				catch( std::exception& error )
				{
					output << "Oh dear. An exception was encountered. Here it is: " << error.what() << "\n";
				}
			}
			reply.status=httpserver::HttpServer::Reply::StatusType::ok;
		}
		else if( resource=="/saveHistograms" )
		{
			output << "saveHistograms called" << "\n";
			// Look through the parameters and try and find the filename to open
			std::string filename;
			for( const auto& paramValuePair : parameters ) if( paramValuePair.first=="filename" ) filename=paramValuePair.second;

			if( filename.empty() ) output << "Error! no filename was supplied, or it's empty." << "\n";
			else
			{
				// Open a TFile and save the histograms to it
				TFile outputFile( filename.c_str(), "RECREATE" );
				connectedCBCSCurves_.createHistograms( &outputFile );
				outputFile.Write();
			}
			reply.status=httpserver::HttpServer::Reply::StatusType::ok;
		}
		else if( resource=="/setThreshold" )
		{
			output << "setThreshold called" << "\n";
			// Look through the parameters and try and find the value to set to
			std::string valueAsString;
			for( const auto& paramValuePair : parameters ) if( paramValuePair.first=="value" ) valueAsString=paramValuePair.second;

			if( valueAsString.empty() ) output << "Error! no value was supplied. Add \"?value=<threshold>\" to the URL." << "\n";
			else
			{
				std::stringstream stringConverter;
				stringConverter.str(valueAsString);
				float variable;
				stringConverter >> variable;
				output << "Setting threshold to " << variable << "; previous value was " << threshold_ << "\n";
				threshold_=variable;
			}
			reply.status=httpserver::HttpServer::Reply::StatusType::ok;
		}
		else if( resource=="/version" )
		{
			output << "Version=" << "0.0" << "\n";
			reply.status=httpserver::HttpServer::Reply::StatusType::ok;
		}
		else if( resource=="/restoreFromRootFile" )
		{
			// Look through the parameters and try and find the filename to open
			std::string filename;
			for( const auto& paramValuePair : parameters ) if( paramValuePair.first=="filename" ) filename=paramValuePair.second;

			if( filename.empty() )
			{
				output << "Error! no filename was supplied, or it's empty." << "\n";
				reply.status=httpserver::HttpServer::Reply::StatusType::bad_request;
			}
			else
			{
				try
				{
					// Open a TFile and try loading the TEfficiency objects from the different subdirectories
					TFile outputFile( filename.c_str() );
					if( outputFile.IsZombie() ) throw std::runtime_error( "Unable to open file "+filename );
					connectedCBCSCurves_.restoreFromDirectory( &outputFile );
					output << "State loaded from file " << filename << "\n";
					reply.status=httpserver::HttpServer::Reply::StatusType::ok;
				}
				catch( std::exception& error )
				{
					output << "Error! " << error.what() << "\n";
					reply.status=httpserver::HttpServer::Reply::StatusType::internal_server_error;
				}
			}
		}
		else if( resource=="/fitParameters" )
		{
			output << "{" << "\n";
			std::vector<size_t> channelIndices=connectedCBCSCurves_.getValidChannelIndices();
			for( std::vector<size_t>::const_iterator iIndexA=channelIndices.begin(); iIndexA!=channelIndices.end(); ++iIndexA )
			{
				output << "   \"CBC " << std::setfill('0') << std::setw(2)  << *iIndexA << "\": {" << "\n";
				cbcanalyser::FedChannelSCurves& fedChannel=connectedCBCSCurves_.getFedChannelSCurves(*iIndexA);
				std::vector<size_t> stripIndices=fedChannel.getValidStripIndices();
				for( std::vector<size_t>::const_iterator iIndexB=stripIndices.begin(); iIndexB!=stripIndices.end(); ++iIndexB )
				{
					cbcanalyser::SCurve& sCurve=fedChannel.getStripSCurve(*iIndexB);
					std::tuple<float,float,float,float,float> parameters=sCurve.fitParameters();
					output << "      \"Channel " << std::setfill('0') << std::setw(3)  << *iIndexB
							<< "\": { \"chi2\": " << std::get<0>(parameters)
							<< ", \"ndf\":" << std::get<1>(parameters)
							<< ", \"maxEfficiency\":" << std::get<2>(parameters)
							<< ", \"standardDeviation\":" << std::get<3>(parameters)
							<< ", \"mean\":" << std::get<4>(parameters) << " }";
					if( iIndexB+1 != stripIndices.end() ) output << ",";
					output << "\n";
				}
				output << "   }";
				if( iIndexA+1 != channelIndices.end() ) output << ",";
				output << "\n";
			}
			output << "}" << "\n";
		}
		else if( resource=="/reset" )
		{
			output << "Reset called. Removing all data." << "\n";
			connectedCBCSCurves_=cbcanalyser::FedSCurves();
			reply.status=httpserver::HttpServer::Reply::StatusType::ok;
		}
		else
		{
			output << "Unknown command. You can see a list of the available commands by requesting the root resource (i.e. \"/\")." << "\n";
			reply.status=httpserver::HttpServer::Reply::StatusType::not_found;
		}

		// Status should already have been set in the "if" statements above
		//reply.status=httpserver::HttpServer::Reply::StatusType::ok;
		reply.content=output.str();
		reply.headers.resize( 2 );
		reply.headers[0].name="Content-Length";
		reply.headers[0].value=std::to_string( reply.content.size() );
		reply.headers[1].name="Content-Type";
		reply.headers[1].value="text/plain";

		std::cout << reply.content << std::endl;
	}

	void HttpRequestHandler::openDAQDumpFile( const std::string& filename )
	{
		std::ifstream inputFile( filename );
		if( !inputFile.is_open() ) throw std::runtime_error( "Unable to open the file \""+filename+"\"" );

		cbcanalyser::RawDataFileReader reader( inputFile );

		while( std::unique_ptr<cbcanalyser::RawDataEvent> pEvent=reader.nextEvent() )
		{
			for( size_t cbcIndex=0; cbcIndex<4; ++cbcIndex )
			{
				cbcanalyser::FedChannelSCurves& cbcSCurves=connectedCBCSCurves_.getFedChannelSCurves( cbcIndex );
				cbcanalyser::RawCBCEvent& cbcEvent=pEvent->cbc(cbcIndex);
				for( size_t index=0; index<cbcEvent.channelData().size(); ++index )
				{
					cbcanalyser::SCurve& scurveForStrip=cbcSCurves.getStripSCurve(index);

					// If there was a hit record an "on" event, otherwise record an "off" event
					// for the current threshold.
					if( cbcEvent.channelData()[index] ) ++scurveForStrip.getEntry( threshold_ ).eventsOn();
					else ++scurveForStrip.getEntry( threshold_ ).eventsOff();
				}
			}
//			std::cout << "\n"
//					<< "bunchCounter=" << pEvent->bunchCounter() << "\n"
//					<< "orbitCounter=" << pEvent->orbitCounter() << "\n"
//					<< "lumisection=" << pEvent->lumisection() << "\n"
//					<< "l1aCounter=" << pEvent->l1aCounter() << "\n"
//					<< "cbcCounter=" << pEvent->cbcCounter() << "\n";
			std::cout << "\t" << "Channel data: ";
			for( const auto& channel : pEvent->cbc(0).channelData() )
			{
				if( channel ) std::cout << "1";
				else std::cout << ".";
			}
			std::cout << std::endl;

		}

	}

} // end of the unnamed namespace
