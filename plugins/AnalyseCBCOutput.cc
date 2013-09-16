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

namespace // Use the unnamed namespace for tools only used in this file
{
	/** @brief Closes the fstream as soon as it goes out of scope.
	 *
	 * Used as an exception safe way to close files.
	 *
	 * @author Mark Grimes (mark.grimes@bristol.ac.uk)
	 * @date 04/Sep/2013
	 */
	class FileStreamSentry
	{
	public:
		FileStreamSentry( std::fstream& fileStream ) : fileStream_(fileStream) {}
		~FileStreamSentry() { fileStream_.close(); }
	private:
		std::fstream& fileStream_;
	};

}

cbcanalyser::AnalyseCBCOutput::AnalyseCBCOutput( const edm::ParameterSet& config )
	: stripThresholdOffsets_(128)
{
	std::cout << "cbcanalyser::AnalyseCBCOutput::AnalyseCBCOutput()" << std::endl;

	I2CValuesFilename_=config.getParameter<std::string>("trimFilename");
	savedStateFilename_=config.getUntrackedParameter<std::string>("savedStateFilename","");

	runsProcessed_=0;

	if( !savedStateFilename_.empty() )
	{
		try{ restoreState( savedStateFilename_ ); }
		catch( std::exception& error ){ std::cerr << "Couldn't restore state because: " << error.what() << std::endl; }
	}

}

cbcanalyser::AnalyseCBCOutput::~AnalyseCBCOutput()
{
	std::cout << "cbcanalyser::AnalyseCBCOutput::~AnalyseCBCOutput()" << std::endl;

	//
	// Now that the job has finished, create root histograms from all of the
	// data that has been collected.
	//
	edm::Service<TFileService> pFileService;
	detectorSCurves_.createHistograms( &pFileService->file() );
	pFileService->file().Write();

	//
	// If the constructor is called then job has reached it's natural conclusion.
	// Truncate the state file so that the next job starts fresh.
	//
	if( !savedStateFilename_.empty() )
	{
		std::fstream blankFile( savedStateFilename_, std::ios_base::out | std::ios_base::trunc );
		blankFile.close();
	}
}

void cbcanalyser::AnalyseCBCOutput::fillDescriptions( edm::ConfigurationDescriptions& descriptions )
{
	//std::cout << "cbcanalyser::AnalyseCBCOutput::fillDescriptions()" << std::endl;
}

void cbcanalyser::AnalyseCBCOutput::beginJob()
{
	std::cout << "cbcanalyser::AnalyseCBCOutput::beginJob()" << std::endl;
}

void cbcanalyser::AnalyseCBCOutput::analyze( const edm::Event& event, const edm::EventSetup& setup )
{
	++eventsProcessed_;
	std::cout << "cbcanalyser::AnalyseCBCOutput::analyze() event " << eventsProcessed_ << std::endl;

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

						cbcanalyser::FedChannelSCurves& fedChannelSCurves=detectorSCurves_.getFedChannelSCurves( fedIndex, channelIndex );

						const std::vector<bool>& hits=unpacker.hits();

						for( size_t stripNumber=0; stripNumber<hits.size(); ++stripNumber )
						{
							cbcanalyser::SCurve& sCurve=fedChannelSCurves.getStripSCurve(stripNumber);
							cbcanalyser::SCurveEntry& sCurveEntry=sCurve.getEntry( stripThresholdOffsets_[stripNumber] );

							if( hits[stripNumber]==true ) ++sCurveEntry.eventsOn();
							else ++sCurveEntry.eventsOff();
						}
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
	std::cout << "cbcanalyser::AnalyseCBCOutput::endJob(). Analysed " << eventsProcessed_ << " events in " << runsProcessed_ << " runs." << std::endl;
}

void cbcanalyser::AnalyseCBCOutput::beginRun( const edm::Run& run, const edm::EventSetup& setup )
{
	std::cout << "cbcanalyser::AnalyseCBCOutput::beginRun()" << std::endl;
	try { readI2CValues(); }
	catch( std::exception& error )
	{
		std::cerr << "readI2CValues() failed because: " << error.what() << std::endl;
	}
	eventsProcessed_=0;
	++runsProcessed_;
}

void cbcanalyser::AnalyseCBCOutput::endRun( const edm::Run& run, const edm::EventSetup& setup )
{
	std::cout << "cbcanalyser::AnalyseCBCOutput::endRun(). Analysed " << eventsProcessed_ << " events in " << runsProcessed_ << " runs." << std::endl;

	if( !savedStateFilename_.empty() && eventsProcessed_>0 ) saveState( savedStateFilename_ );
}

void cbcanalyser::AnalyseCBCOutput::beginLuminosityBlock( const edm::LuminosityBlock& lumiBlock, const edm::EventSetup& setup )
{
	std::cout << "cbcanalyser::AnalyseCBCOutput::beginLuminosityBlock()" << std::endl;
}

void cbcanalyser::AnalyseCBCOutput::endLuminosityBlock( const edm::LuminosityBlock& lumiBlock, const edm::EventSetup& setup )
{
	std::cout << "cbcanalyser::AnalyseCBCOutput::endLuminosityBlock()" << std::endl;
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
				stripThresholdOffsets_[channelNumber]=threshold;
			}

		} // end of try block
		catch( std::runtime_error& exception )
		{
			std::cout << "Some error occurred while processing the line \"" << buffer << "\":" << exception.what() << std::endl;
		}
	}


	trimFile.close();
}

void cbcanalyser::AnalyseCBCOutput::saveState( const std::string& filename )
{
	std::fstream outputFile( filename, std::ios_base::out | std::ios_base::trunc );
	if( !outputFile.is_open() ) throw std::runtime_error( "Unable to open the output file \""+filename+"\" to save the analyser state.");
	FileStreamSentry closeFileSentry(outputFile);

	detectorSCurves_.dumpToStream( outputFile );

	outputFile << "stripThresholdOffsets_ " << stripThresholdOffsets_.size() << " ";
	for( const auto& offset : stripThresholdOffsets_ ) outputFile << offset << " ";

	outputFile << eventsProcessed_ << " " << runsProcessed_ << " ";
}

void cbcanalyser::AnalyseCBCOutput::restoreState( const std::string& filename )
{
	std::fstream inputFile( filename, std::ios_base::in );
	if( !inputFile.is_open() ) throw std::runtime_error( "Unable to open the input file \""+filename+"\" to restore the analyser state.");
	FileStreamSentry closeFileSentry(inputFile);

	detectorSCurves_.restoreFromStream( inputFile );

	std::string identifier;
	inputFile >> identifier;
	if( identifier!="stripThresholdOffsets_" ) throw std::runtime_error( "AnalyseCBCOutput::restoreState - didn't read stripThresholdOffsets_ tag." );

	size_t entries;
	inputFile >> entries;
	stripThresholdOffsets_.resize(entries);
	for( size_t index=0; index<entries; ++index ) inputFile >> stripThresholdOffsets_[index];

	inputFile >> eventsProcessed_ >> runsProcessed_;
}
