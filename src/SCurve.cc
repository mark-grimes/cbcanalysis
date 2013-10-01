#include "XtalDAQ/OnlineCBCAnalyser/interface/SCurve.h"

#include <cmath>
#include <stdexcept>
#include <sstream>
#include <iomanip>
#include <TH1F.h>
#include <TDirectory.h>

//----------------------------------------------------------------------------------------------
//------------------------- cbcanalyser::SCurveEntry definitions -------------------------------
//----------------------------------------------------------------------------------------------

cbcanalyser::SCurveEntry::SCurveEntry()
	: eventsOn_(0), eventsOff_(0)
{
	// No operation besides the initialiser list.
}

size_t& cbcanalyser::SCurveEntry::eventsOn()
{
	return eventsOn_;
}

const size_t& cbcanalyser::SCurveEntry::eventsOn() const
{
	return eventsOn_;
}

size_t& cbcanalyser::SCurveEntry::eventsOff()
{
	return eventsOff_;
}

const size_t& cbcanalyser::SCurveEntry::eventsOff() const
{
	return eventsOff_;
}

float cbcanalyser::SCurveEntry::fraction() const
{
	if( (eventsOn_+eventsOff_)==0 ) return 0;
	return static_cast<float>(eventsOn_)/static_cast<float>(eventsOn_+eventsOff_);
}

float cbcanalyser::SCurveEntry::fractionError() const
{
	if( (eventsOn_+eventsOff_)==0 ) return 0;
	return std::sqrt(eventsOn_)/static_cast<float>(eventsOn_+eventsOff_);
}

bool cbcanalyser::SCurveEntry::operator==( const SCurveEntry& otherSCurveEntry ) const
{
	return ( eventsOn_==otherSCurveEntry.eventsOn_ ) && ( eventsOff_==otherSCurveEntry.eventsOff_ );
}

bool cbcanalyser::SCurveEntry::operator!=( const SCurveEntry& otherSCurveEntry ) const
{
	return !( (*this)==otherSCurveEntry );
}

void cbcanalyser::SCurveEntry::dumpToStream( std::ostream& outputStream ) const
{
	// There will be lots of these entries so I'll just abbreviate the class identifier to "SCE"
	// instead of "SCurveEntry".
	outputStream << "SCE " << eventsOn_ << " " << eventsOff_ << " ";
}

void cbcanalyser::SCurveEntry::restoreFromStream( std::istream& inputStream )
{
	std::string identifier;
	size_t eventsOn;
	size_t eventsOff;

	inputStream >> identifier >> eventsOn >> eventsOff;

	if( identifier!="SCE" ) throw std::runtime_error( "SCurveEntry::restoreFromStream - stream does not describe a SCurveEntry object" );

	eventsOn_=eventsOn;
	eventsOff_=eventsOff;
}

//----------------------------------------------------------------------------------------------
//---------------------------- cbcanalyser::SCurve definitions ---------------------------------
//----------------------------------------------------------------------------------------------

cbcanalyser::SCurve::SCurve()
	: entries_( maxiumumEntries() )
{
}

bool cbcanalyser::SCurve::operator==( const SCurve& otherSCurve ) const
{
	if( entries_.size()!=otherSCurve.entries_.size() ) return false;

	for( size_t index=0; index<entries_.size(); ++index )
	{
		if( entries_[index]!=otherSCurve.entries_[index] ) return false;
	}

	return true;
}

bool cbcanalyser::SCurve::operator!=( const SCurve& otherSCurve ) const
{
	return !( (*this)==otherSCurve );
}

cbcanalyser::SCurveEntry& cbcanalyser::SCurve::getEntry( size_t index )
{
	return entries_.at(index);
}

const cbcanalyser::SCurveEntry& cbcanalyser::SCurve::getEntry( size_t index ) const
{
	return entries_.at(index);
}

size_t cbcanalyser::SCurve::size() const
{
	return entries_.size();
}

std::unique_ptr<TH1> cbcanalyser::SCurve::createHistogram( const std::string& name ) const
{
	std::unique_ptr<TH1> pNewHistogram( new TH1F( name.c_str(), name.c_str(), entries_.size(), -0.5, entries_.size()-0.5 ) );
	pNewHistogram->SetDirectory(nullptr);

	for( size_t index=0; index<entries_.size(); ++index )
	{
		const cbcanalyser::SCurveEntry& entry=getEntry(index);
		pNewHistogram->SetBinContent( index+1, entry.fraction() ); // +1 because root starts bin numbers from 1
		pNewHistogram->SetBinError( index+1, entry.fractionError() ); // +1 because root starts bin numbers from 1
	}

	return pNewHistogram;
}

void cbcanalyser::SCurve::dumpToStream( std::ostream& outputStream ) const
{
	outputStream << "SCurve " << entries_.size() << " ";
	for( const auto& entry : entries_ )
	{
		entry.dumpToStream(outputStream); // Then delegate to the SCurveEntry class
	}
}

void cbcanalyser::SCurve::restoreFromStream( std::istream& inputStream )
{
	// Use a temporary object, so that if restoring fails I'm not left with a
	// half modified instance.
	cbcanalyser::SCurve temporaryInstance;

	std::string identifier;
	inputStream >> identifier;
	if( identifier!="SCurve" ) throw std::runtime_error( "SCurve::restoreFromStream - stream does not describe a SCurve object" );


	size_t numberOfEntries;
	inputStream >> numberOfEntries;

	for( size_t entry=0; entry<numberOfEntries; ++entry )
	{
		// Delegate to each entry to restore its state from disk
		temporaryInstance.entries_[entry].restoreFromStream(inputStream);
	}

	// If everything went smoothly and I get to this point, I can overwrite the contents
	// with what was read from disk.
	(*this)=temporaryInstance;
}

size_t cbcanalyser::SCurve::maxiumumEntries()
{
	return 256;
}

//----------------------------------------------------------------------------------------------
//----------------------- cbcanalyser::FedChannelSCurves definitions ---------------------------
//----------------------------------------------------------------------------------------------

cbcanalyser::SCurve& cbcanalyser::FedChannelSCurves::getStripSCurve( size_t stripNumber )
{
	return stripSCurves_[stripNumber];
}

std::vector<size_t> cbcanalyser::FedChannelSCurves::getValidStripIndices() const
{
	std::vector<size_t> returnValue;
	for( const auto& stripNumberSCurvesPair : stripSCurves_ ) returnValue.push_back( stripNumberSCurvesPair.first );
	return returnValue;
}

void cbcanalyser::FedChannelSCurves::createHistograms( TDirectory* pParentDirectory ) const
{
	std::stringstream stringConverter;

	for( const auto& stripNumberSCurvesPair : stripSCurves_ )
	{
		stringConverter.str("");
		stringConverter << "Strip " << std::setfill('0') << std::setw(2) << stripNumberSCurvesPair.first;

		std::unique_ptr<TH1> pNewHistogram=stripNumberSCurvesPair.second.createHistogram( stringConverter.str() );
		pNewHistogram->SetDirectory( pParentDirectory );
		pNewHistogram.release(); // When the directory gets set, the directory takes ownership
	}

}

void cbcanalyser::FedChannelSCurves::dumpToStream( std::ostream& outputStream ) const
{
	outputStream << "FedChannelSCurves " << stripSCurves_.size() << " ";
	for( const auto& stripNumberSCurvesPair : stripSCurves_ )
	{
		outputStream << stripNumberSCurvesPair.first << " "; // Dump the strip number
		stripNumberSCurvesPair.second.dumpToStream(outputStream); // Then delegate to the SCurve class
	}
}

void cbcanalyser::FedChannelSCurves::restoreFromStream( std::istream& inputStream )
{
	// Use a temporary object, so that if restoring fails I'm not left with a
	// half modified instance.
	cbcanalyser::FedChannelSCurves temporaryInstance;

	std::string identifier;
	inputStream >> identifier;
	if( identifier!="FedChannelSCurves" ) throw std::runtime_error( "FedChannelSCurves::restoreFromStream - stream does not describe a FedChannelSCurves object" );


	size_t numberOfEntries;
	inputStream >> numberOfEntries;

	size_t stripNumber;
	for( size_t entry=0; entry<numberOfEntries; ++entry )
	{
		inputStream >> stripNumber;
		// Create a new SCurves object
		cbcanalyser::SCurve& newSCurve=temporaryInstance.getStripSCurve(stripNumber);
		// And then delegate to that to restore its state from disk
		newSCurve.restoreFromStream(inputStream);
	}

	// If everything went smoothly and I get to this point, I can overwrite the contents
	// with what was read from disk.
	(*this)=temporaryInstance;
}

//----------------------------------------------------------------------------------------------
//-------------------------- cbcanalyser::FedSCurves definitions -------------------------------
//----------------------------------------------------------------------------------------------

cbcanalyser::FedChannelSCurves& cbcanalyser::FedSCurves::getFedChannelSCurves( size_t fedChannelNumber )
{
	return fedChannelSCurves_[fedChannelNumber];
}

cbcanalyser::SCurve& cbcanalyser::FedSCurves::getStripSCurve( size_t fedChannelNumber, size_t stripNumber )
{
	return fedChannelSCurves_[fedChannelNumber].getStripSCurve(stripNumber);
}

std::vector<size_t> cbcanalyser::FedSCurves::getValidChannelIndices() const
{
	std::vector<size_t> returnValue;
	for( const auto& fedChannelNumberSCurvesPair : fedChannelSCurves_ ) returnValue.push_back( fedChannelNumberSCurvesPair.first );
	return returnValue;
}

void cbcanalyser::FedSCurves::createHistograms( TDirectory* pParentDirectory ) const
{
	std::stringstream stringConverter;

	for( const auto& fedChannelNumberSCurvesPair : fedChannelSCurves_ )
	{
		stringConverter.str("");
		stringConverter << "Channel " << std::setfill('0') << std::setw(2) << fedChannelNumberSCurvesPair.first;

		TDirectory* pSubDirectory=pParentDirectory->mkdir( stringConverter.str().c_str() );
		fedChannelNumberSCurvesPair.second.createHistograms( pSubDirectory );
	}

}

void cbcanalyser::FedSCurves::dumpToStream( std::ostream& outputStream ) const
{
	outputStream << "FedSCurves " << fedChannelSCurves_.size() << " ";
	for( const auto& fedChannelNumberSCurvesPair : fedChannelSCurves_ )
	{
		outputStream << fedChannelNumberSCurvesPair.first << " "; // Dump the FED channel number
		fedChannelNumberSCurvesPair.second.dumpToStream(outputStream); // Then delegate to the FedSCurves class
	}
}

void cbcanalyser::FedSCurves::restoreFromStream( std::istream& inputStream )
{
	// Use a temporary object, so that if restoring fails I'm not left with a
	// half modified instance.
	cbcanalyser::FedSCurves temporaryInstance;

	std::string identifier;
	inputStream >> identifier;
	if( identifier!="FedSCurves" ) throw std::runtime_error( "FedSCurves::restoreFromStream - stream does not describe a FedSCurves object" );


	size_t numberOfEntries;
	inputStream >> numberOfEntries;

	size_t fedChannelNumber;
	for( size_t entry=0; entry<numberOfEntries; ++entry )
	{
		inputStream >> fedChannelNumber;
		// Create a new FedChannelSCurves object
		cbcanalyser::FedChannelSCurves& newFedChannelSCurves=temporaryInstance.getFedChannelSCurves(fedChannelNumber);
		// And then delegate to that to restore its state from disk
		newFedChannelSCurves.restoreFromStream(inputStream);
	}

	// If everything went smoothly and I get to this point, I can overwrite the contents
	// with what was read from disk.
	(*this)=temporaryInstance;
}

//----------------------------------------------------------------------------------------------
//------------------------ cbcanalyser::DetectorSCurves definitions ----------------------------
//----------------------------------------------------------------------------------------------

cbcanalyser::FedSCurves& cbcanalyser::DetectorSCurves::getFedSCurves( size_t fedNumber )
{
	return fedSCurves_[fedNumber];
}

cbcanalyser::FedChannelSCurves& cbcanalyser::DetectorSCurves::getFedChannelSCurves( size_t fedNumber, size_t fedChannelNumber )
{
	return fedSCurves_[fedNumber].getFedChannelSCurves(fedChannelNumber);
}

cbcanalyser::SCurve& cbcanalyser::DetectorSCurves::getStripSCurve( size_t fedNumber, size_t fedChannelNumber, size_t stripNumber )
{
	return fedSCurves_[fedNumber].getStripSCurve(fedChannelNumber,stripNumber);
}

std::vector<size_t> cbcanalyser::DetectorSCurves::getValidFedIndices() const
{
	std::vector<size_t> returnValue;
	for( const auto& fedNumberSCurvesPair : fedSCurves_ ) returnValue.push_back( fedNumberSCurvesPair.first );
	return returnValue;
}

void cbcanalyser::DetectorSCurves::createHistograms( TDirectory* pParentDirectory ) const
{
	std::stringstream stringConverter;

	for( const auto& fedNumberSCurvesPair : fedSCurves_ )
	{
		stringConverter.str("");
		stringConverter << "FED " << std::setfill('0') << std::setw(2) << fedNumberSCurvesPair.first;

		TDirectory* pSubDirectory=pParentDirectory->mkdir( stringConverter.str().c_str() );
		fedNumberSCurvesPair.second.createHistograms( pSubDirectory );
	}

}

void cbcanalyser::DetectorSCurves::dumpToStream( std::ostream& outputStream ) const
{
	outputStream << "DetectorSCurves " << fedSCurves_.size() << " ";
	for( const auto& fedNumberSCurvesPair : fedSCurves_ )
	{
		outputStream << fedNumberSCurvesPair.first << " "; // Dump the FED number
		fedNumberSCurvesPair.second.dumpToStream(outputStream); // Then delegate to the FedSCurves class
	}
}

void cbcanalyser::DetectorSCurves::restoreFromStream( std::istream& inputStream )
{
	// Use a temporary object, so that if restoring fails I'm not left with a
	// half modified instance.
	cbcanalyser::DetectorSCurves temporaryInstance;

	std::string identifier;
	inputStream >> identifier;
	if( identifier!="DetectorSCurves" ) throw std::runtime_error( "DetectorSCurves::restoreFromStream - stream does not describe a DetectorSCurves object" );


	size_t numberOfEntries;
	inputStream >> numberOfEntries;

	size_t fedNumber;
	for( size_t entry=0; entry<numberOfEntries; ++entry )
	{
		inputStream >> fedNumber;
		// Create a new FedSCurves object
		cbcanalyser::FedSCurves& newFedSCurves=temporaryInstance.getFedSCurves(fedNumber);
		// And then delegate to that to restore its state from disk
		newFedSCurves.restoreFromStream(inputStream);
	}

	// If everything went smoothly and I get to this point, I can overwrite the contents
	// with what was read from disk.
	(*this)=temporaryInstance;
}
