#include "XtalDAQ/OnlineCBCAnalyser/plugins/AnalyseCBCOutput.h"

#include <iostream>
#include <stdexcept>
#include <FWCore/Framework/interface/MakerMacros.h>
#include <FWCore/Framework/interface/Event.h>
#include <DataFormats/Common/interface/TriggerResults.h>
#include <DataFormats/FEDRawData/interface/FEDRawDataCollection.h>
#include <EventFilter/SiStripRawToDigi/interface/SiStripFEDBuffer.h>
#include <FWCore/ServiceRegistry/interface/Service.h>
#include <CommonTools/UtilAlgos/interface/TFileService.h>
#include <FWCore/MessageService/interface/MessageLogger.h>
#include "XtalDAQ/OnlineCBCAnalyser/interface/stringManipulationTools.h"
#include "XtalDAQ/OnlineCBCAnalyser/interface/CBCChannelUnpacker.h"


namespace cbcanalyser
{
	DEFINE_FWK_MODULE(AnalyseCBCOutput);
}


cbcanalyser::AnalyseCBCOutput::AnalyseCBCOutput( const edm::ParameterSet& config )
	: channels_(128)
{
	outputFile_.open( "/home/xtaldaq/testOutput.log", std::ios_base::out | std::ios_base::app );
	outputFile_ << "cbcanalyser::AnalyseCBCOutput::AnalyseCBCOutput()" << std::endl;

	I2CValuesFilename_=config.getParameter<std::string>("trimFilename");
	outputFilename_=config.getParameter<std::string>("outputFilename");

	edm::Service<TFileService> pFileService;
	std::stringstream stringConverter;

	for( size_t channel=0; channel<128; ++channel )
	{
		stringConverter.str("");
		stringConverter << "occupancyChannel" << channel;
		TH1* pNewHistogram=pFileService->make<TH1F>( stringConverter.str().c_str(), stringConverter.str().c_str(), 100, 0, 100 );
		pTestHistograms_.push_back( pNewHistogram );
	}
	pAllChannels_=pFileService->make<TH1F>( "allChannels", "allChannels", 128, -0.5, 127.5 );
}

cbcanalyser::AnalyseCBCOutput::~AnalyseCBCOutput()
{
	outputFile_ << "cbcanalyser::AnalyseCBCOutput::~AnalyseCBCOutput()" << std::endl;
	outputFile_.close();
}

void cbcanalyser::AnalyseCBCOutput::fillDescriptions( edm::ConfigurationDescriptions& descriptions )
{
	//outputFile_ << "cbcanalyser::AnalyseCBCOutput::fillDescriptions()" << std::endl;
}

void cbcanalyser::AnalyseCBCOutput::beginJob()
{
	outputFile_ << "cbcanalyser::AnalyseCBCOutput::beginJob()" << std::endl;
}

void cbcanalyser::AnalyseCBCOutput::analyze( const edm::Event& event, const edm::EventSetup& setup )
{
	++eventsProcessed_;
	outputFile_ << "cbcanalyser::AnalyseCBCOutput::analyze() event " << eventsProcessed_ << std::endl;

	edm::Handle<FEDRawDataCollection> hRawData;
	event.getByLabel( "rawDataCollector", hRawData );

	size_t fedIndex;
	for( fedIndex=0; fedIndex<sistrip::CMS_FED_ID_MAX; ++fedIndex )
	{
		const FEDRawData& fedData=hRawData->FEDData(fedIndex);

		if( fedData.size()!=0 )
		{
			// Check to see if this FED is one of the ones allocated to the strip tracker
			if( fedIndex < sistrip::FED_ID_MIN || fedIndex > sistrip::FED_ID_MAX )
			{
				//std::cout << "Skipping FEDRawData at fedIndex " << std::dec << fedIndex << " has size " << fedData.size() << std::endl;
				continue;
			}

			//std::cout << "FEDRawData at fedIndex " << std::dec << fedIndex << " has size " << fedData.size() << std::endl;
			try
			{
				sistrip::FEDBuffer myBuffer(fedData.data(),fedData.size());
				//myBuffer.print( std::cout );

				for ( uint16_t feIndex = 0; feIndex<sistrip::FEUNITS_PER_FED; ++feIndex )
				{
					if( !myBuffer.fePresent(feIndex) ) continue;

					for ( uint16_t channelInFe = 0; channelInFe < sistrip::FEDCH_PER_FEUNIT; ++channelInFe )
					{
						const uint16_t channelIndex=feIndex*sistrip::FEDCH_PER_FEUNIT+channelInFe;
						const sistrip::FEDChannel& channel=myBuffer.channel(channelIndex);

						cbcanalyser::CBCChannelUnpacker unpacker(channel);
						if( !unpacker.hasData() ) continue;

						const std::vector<bool>& hits=unpacker.hits();

						// For testing I'll just output the results to std::cout
						for( size_t stripNumber=0; stripNumber<hits.size(); ++stripNumber )
						{
							if( hits[stripNumber]==true )
							{
								pAllChannels_->Fill( stripNumber );
								++channels_[stripNumber].numberOn;
							}
							else ++channels_[stripNumber].numberOff;
						}
						//for( std::vector<bool>::const_iterator iHit=hits.begin(); iHit!=hits.end(); ++iHit )
						//{
						//	if( *iHit==true ) std::cout << "1";
						//	else std::cout << " ";
						//}
						//std::cout << std::endl;
					}
				}
			}
			catch( std::exception& error )
			{
				std::cout << "Exception: "<< error.what() << std::endl;
			}

		}
	}
}

void cbcanalyser::AnalyseCBCOutput::endJob()
{
	outputFile_ << "cbcanalyser::AnalyseCBCOutput::endJob()" << std::endl;
}

void cbcanalyser::AnalyseCBCOutput::beginRun( const edm::Run& run, const edm::EventSetup& setup )
{
	outputFile_ << "cbcanalyser::AnalyseCBCOutput::beginRun()" << std::endl;
	readI2CValues();
	eventsProcessed_=0;
}

void cbcanalyser::AnalyseCBCOutput::endRun( const edm::Run& run, const edm::EventSetup& setup )
{
	outputFile_ << "cbcanalyser::AnalyseCBCOutput::endRun(). Analysed " << eventsProcessed_ << " events." << std::endl;
	edm::Service<TFileService>()->file().Write();
	if( eventsProcessed_>0 ) writeOutput();
}

void cbcanalyser::AnalyseCBCOutput::beginLuminosityBlock( const edm::LuminosityBlock& lumiBlock, const edm::EventSetup& setup )
{
	outputFile_ << "cbcanalyser::AnalyseCBCOutput::beginLuminosityBlock()" << std::endl;
}

void cbcanalyser::AnalyseCBCOutput::endLuminosityBlock( const edm::LuminosityBlock& lumiBlock, const edm::EventSetup& setup )
{
	outputFile_ << "cbcanalyser::AnalyseCBCOutput::endLuminosityBlock()" << std::endl;
}

void cbcanalyser::AnalyseCBCOutput::readI2CValues()
{
	std::ifstream trimFile( I2CValuesFilename_ );
	if( !trimFile.is_open() ) throw std::runtime_error( "Unable to open the trim file \""+I2CValuesFilename_+"\"");

	const size_t bufferSize=200;
	char buffer[bufferSize];
	while( trimFile.good() )
	{
		try
		{
			// Get one line at a time
			trimFile.getline( buffer, bufferSize );

			// split the line and lose everything after a comment character
			std::string lineWithoutComments=cbcanalyser::tools::splitByDelimeters( buffer, "#*" ).front();

			// split the line by whitespace into columns
			std::vector<std::string> columns=cbcanalyser::tools::splitByWhitespace( lineWithoutComments );

			if( columns.size()==1 && columns[0].empty() ) continue; // Allow blank lines without giving a warning
			if( columns.size()!=4 ) throw std::runtime_error( "The line does not have the correct number of columns" );

			std::string valueName=columns[0];
			if( valueName.substr(0,7)=="Channel" )
			{
				std::string channelNumberAsString=valueName.substr(7);
				int channelNumber=cbcanalyser::tools::convertStringToFloat(channelNumberAsString);
				if( channelNumber<0 || channelNumber>127 ) throw std::runtime_error( "Unknown channel number "+channelNumberAsString);

				int threshold=cbcanalyser::tools::convertHexToInt(columns[3]);
				channels_[channelNumber].threshold=threshold;
			}

		} // end of try block
		catch( std::runtime_error& exception )
		{
			std::cout << "Some error occured while processing the line \"" << buffer << "\":" << exception.what() << std::endl;
		}
	}


	trimFile.close();
}

void cbcanalyser::AnalyseCBCOutput::writeOutput()
{
	std::fstream outputFile( outputFilename_, std::ios_base::out | std::ios_base::app );
	if( !outputFile.is_open() ) throw std::runtime_error( "Unable to open the output file \""+outputFilename_+"\"");

	for( size_t channelNumber=0; channelNumber<128; ++channelNumber )
	{
		outputFile << "Channel " << std::setw(5) << channelNumber
				<< std::setw(10) << channels_[channelNumber].threshold << " "
				<< std::setw(10) << channels_[channelNumber].numberOn << " "
				<< std::setw(10) << channels_[channelNumber].numberOff << "\n";
	}

	outputFile.close();
}
