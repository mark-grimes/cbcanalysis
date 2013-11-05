#include "XtalDAQ/OnlineCBCAnalyser/interface/SCurve.h"

#include <cmath>
#include <stdexcept>
#include <sstream>
#include <iostream>
#include <iomanip>
#include <TH1F.h>
#include <TF1.h>
#include <TMath.h>
#include <TEfficiency.h>
#include <TDirectory.h>

//----------------------------------------------------------------------------------------------
//---------------------------- Unnamed namespace declarations ----------------------------------
//---------------------- (definitions are at the bottom of the file) ---------------------------
//----------------------------------------------------------------------------------------------
namespace
{
	/** @brief Sentry class to restore a redirected output stream if an exception is thrown.
	 *
	 * Used for when standard output is redirected to stop all the crap the minuit prints out.
	 * When this goes out of scope standard output will be reset to go to wherever it went
	 * before hand.
	 *
	 * This isn't actually used because after testing I realised it doesn't affect oldschool
	 * printf which is what I wanted. It might come in useful at some point though so I'll
	 * leave it here for now.
	 *
	 * @author Mark Grimes (mark.grimes@bristol.ac.uk)
	 * @date 04/Nov/2013
	 */
	class RedirectedStreamSentry
	{
	public:
		RedirectedStreamSentry( std::ostream& outputStreamToRedirect, std::streambuf* placeToRedirectTo )
			: redirectedStream_(outputStreamToRedirect), pOriginalOutput_( outputStreamToRedirect.rdbuf() )
		{
			redirectedStream_.rdbuf( placeToRedirectTo );
		}
		~RedirectedStreamSentry()
		{
			redirectedStream_.rdbuf( pOriginalOutput_ );
		}
	protected:
		std::ostream& redirectedStream_;
		std::streambuf* pOriginalOutput_;
	};

	/** @brief Sentry class to work with old school printf as RedirectedStreamSentry does for std::cout
	 *
	 * I wrote the RedirectedStreamSentry class and then realised it didn't work because Minuit
	 * uses stdio instead of iostream. Apparantly this code is non-portable and a little dodgy
	 * though. I've put an "#ifndef" in so that it can be disabled if DONT_USE_DODGY_PRINTF_REDIRECTION
	 * is defined.
	 *
	 * @author Mark Grimes (mark.grimes@bristol.ac.uk)
	 */
	class RedirectedPrintfSentry
	{
	public:
		RedirectedPrintfSentry()
		{
#ifndef DONT_USE_DODGY_PRINTF_REDIRECTION
			oldStdout_=dup(1);
			freopen ("/dev/null","w",stdout);
#endif
		}
		~RedirectedPrintfSentry()
		{
#ifndef DONT_USE_DODGY_PRINTF_REDIRECTION
			FILE *fp2 = fdopen(oldStdout_, "w");
			fclose(stdout);
			*stdout = *fp2;
#endif
		}
	protected:
		int oldStdout_;
	};
}
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

cbcanalyser::SCurve::SCurve( size_t numberOfEntries )
	: fit_maxEfficiency_(-1.), fit_standardDeviation_(-1), fit_mean_(-1)
{
}

bool cbcanalyser::SCurve::operator==( const SCurve& otherSCurve ) const
{
	if( entries_.size()!=otherSCurve.entries_.size() ) return false;

//	for( size_t index=0; index<entries_.size(); ++index )
//	{
//		if( entries_[index]!=otherSCurve.entries_[index] ) return false;
//	}

	return entries_==otherSCurve.entries_;
}

bool cbcanalyser::SCurve::operator!=( const SCurve& otherSCurve ) const
{
	return !( (*this)==otherSCurve );
}

cbcanalyser::SCurveEntry& cbcanalyser::SCurve::getEntry( float threshold )
{
	return entries_[threshold];
}

const cbcanalyser::SCurveEntry& cbcanalyser::SCurve::getEntry( float threshold ) const
{
	const auto& findResult=entries_.find( threshold );
	if( findResult==entries_.end() ) throw std::runtime_error( "No entry for '"+std::to_string(threshold)+"' in SCurve" );
	return findResult->second;
}

size_t cbcanalyser::SCurve::size() const
{
	return entries_.size();
}

std::unique_ptr<TEfficiency> cbcanalyser::SCurve::createHistogram( const std::string& name ) const
{
	if( entries_.empty() ) return std::unique_ptr<TEfficiency>(); // return nullptr if histogram is undefined


	// First figure out what binning I need for the entries that I have
	std::vector<double> binLowerEdges;
	cbcanalyser::calculateBinning( binLowerEdges, entries_, [](std::map<float,SCurveEntry>::const_iterator iValue)->float{return iValue->first;} );

	std::unique_ptr<TEfficiency> pNewHistogram( new TEfficiency( name.c_str(), name.c_str(), binLowerEdges.size()-1, &binLowerEdges[0] ) );
	pNewHistogram->SetDirectory(nullptr);

	for( const auto& thresholdEntryPair : entries_ )
	{
		// Need to do a const cast because for some reason FindBin is not a const method
		// and GetPassedHistogram returns a const TH1*. TEfficiency has no direct FindBin
		// method.
		int binNumber=const_cast<TH1*>(pNewHistogram->GetPassedHistogram())->FindBin( thresholdEntryPair.first );
		pNewHistogram->SetTotalEvents( binNumber, thresholdEntryPair.second.eventsOn()+thresholdEntryPair.second.eventsOff() );
		pNewHistogram->SetPassedEvents( binNumber, thresholdEntryPair.second.eventsOn() );
	}
//	// Work out what bin width I need for the given number of entries so that the range
//	// runs from 0 to 1.
//	float binWidth=1.0/static_cast<float>(entries_.size());
//
//	// Make two TH1F to store all events and passed (on) events
//	TH1F hAll(name.c_str(),name.c_str(), entries_.size(), -binWidth, 1+binWidth);
//        TH1F hPass("Pass","Pass", entries_.size(), -binWidth, 1+binWidth);
//
//	for( size_t index=0; index<entries_.size(); ++index )
//	{
//		const cbcanalyser::SCurveEntry& entry=getEntry(index);
//		hAll.SetBinContent( index+1, entry.eventsOn() + entry.eventsOff() );
//                hPass.SetBinContent( index+1, entry.eventsOn() );
//	}
//
//        std::unique_ptr<TEfficiency> pNewHistogram( new TEfficiency( hPass, hAll ) );
//        pNewHistogram->SetDirectory(nullptr);

	return pNewHistogram;
}

std::unique_ptr<TF1> cbcanalyser::SCurve::fit() const
{
	std::unique_ptr<TEfficiency> pHistogram=createHistogram( "efficiencyForFit" );
	// Need to figure out the minimum and maximum for the fit by
	// examining the low and high edges of the TEfficiency.
	float lowEdge=pHistogram->GetPassedHistogram()->GetBinLowEdge(1);
	// To get the high edge need to check low edge of the overflow bin
	float highEdge=pHistogram->GetPassedHistogram()->GetBinLowEdge( pHistogram->GetPassedHistogram()->GetNbinsX()+1 );

	std::unique_ptr<TF1> pFitFunction( new TF1( "efficiencyFitFunction", "([0]*0.5)*( 1 + TMath::Erf( [1]*(x-[2])/TMath::Sqrt2() ) )", lowEdge, highEdge ) );
	pFitFunction->SetParameters( 1, 1.1, (lowEdge+highEdge)/2 ); // Set initial parameters
	pFitFunction->SetParLimits(0,0,1); // Limit range of p0 to be between 0 and 1

	// When fitting minuit prints loads of crap to the screen. To stop this I'll
	// temporarily redirect standard output. I read somewhere that it should be
	// possible to supply the "Q" option to disable output, but that doesn't seem
	// to work. Maybe because it's a TEfficiency and not a TH1.
	{
		//RedirectedPrintfSentry printfRedirector;
		pHistogram->Fit( pFitFunction.get() );
	}

	return pFitFunction;
}

std::tuple<float,float,float> cbcanalyser::SCurve::fitParameters() const
{
	std::unique_ptr<TF1> pFitFunction=fit();
	return std::tuple<float,float,float>( pFitFunction->GetParameter(0), pFitFunction->GetParameter(1), pFitFunction->GetParameter(2) );
}

void cbcanalyser::SCurve::storeFitParameters( const TF1& fittedFunction )
{
  if ( fittedFunction.GetNpar() != 3 ) {
    return;
  }
  fit_maxEfficiency_=fittedFunction.GetParameter(0);
  fit_maxEfficiency_=fittedFunction.GetParameter(1);
  fit_maxEfficiency_=fittedFunction.GetParameter(2);
  return;
}

void cbcanalyser::SCurve::dumpToStream( std::ostream& outputStream ) const
{
	outputStream << "SCurve " << entries_.size() << " ";
	for( const auto& entry : entries_ )
	{
		outputStream << entry.first << " ";
		entry.second.dumpToStream(outputStream); // Then delegate to the SCurveEntry class
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
		float threshold;
		inputStream >> threshold;
		// Delegate to each entry to restore its state from disk
		temporaryInstance.entries_[threshold].restoreFromStream(inputStream);
	}

	// If everything went smoothly and I get to this point, I can overwrite the contents
	// with what was read from disk.
	(*this)=temporaryInstance;
}

size_t cbcanalyser::SCurve::maxiumumEntries()
{
	return entries_.size();
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

		std::unique_ptr<TEfficiency> pNewHistogram=stripNumberSCurvesPair.second.createHistogram( stringConverter.str() );
		pNewHistogram->SetDirectory( pParentDirectory );

		// Fit this S-Curve
		cbcanalyser::FitSCurve fit( *pNewHistogram, stringConverter.str() );
		std::unique_ptr<TF1> pNewFittedFunction=fit.performFit();

		// Set current directory and write fitted function
		pParentDirectory->cd();
		pNewFittedFunction->Write();

		pNewHistogram.release(); // When the directory gets set, the directory takes ownership
		pNewFittedFunction.release();
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
//-------------------------- cbcanalyser::FitSCurve definitions --------------------------------
//----------------------------------------------------------------------------------------------

cbcanalyser::FitSCurve::FitSCurve( TEfficiency & sCurve, const std::string& name )
        : sCurveToFit_(sCurve)
{
  fitFunction_ = new TF1(TString(name+"_fittedFunction"), "([0]*0.5)*( 1 + TMath::Erf( [1]*(x-[2])/TMath::Sqrt2() ) )", 0, 1 );
}

std::unique_ptr<TF1> cbcanalyser::FitSCurve::performFit() const
{
//   Define fit function and set initial parameters
  std::unique_ptr<TF1> pFitFunction(fitFunction_);
  pFitFunction->SetParameters(1., 1.1, 0.5); // Set initial parameters
  pFitFunction->SetParLimits(0,0,1); // Limit range of p0 to be between 0 and 1
  // Do the fit
  sCurveToFit_.Fit(pFitFunction.get());
  return pFitFunction;
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

