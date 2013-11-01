#include <cppunit/extensions/HelperMacros.h>


/** @brief A cppunit TestFixture to test the classes in SCurves.h
 *
 * @author Mark Grimes (mark.grimes@bristol.ac.uk)
 * @date 03/Aug/2013
 */
class SCurveUnitTestSuite : public CPPUNIT_NS::TestFixture
{
	CPPUNIT_TEST_SUITE(SCurveUnitTestSuite);
	CPPUNIT_TEST(testSaveAndRestore);
	CPPUNIT_TEST(testCalculateBinning);
	CPPUNIT_TEST_SUITE_END();

protected:

public:
	void setUp();

protected:
	void testSaveAndRestore();
	void testCalculateBinning();
};





#include <cppunit/config/SourcePrefix.h>
#include <iostream>
#include <stdexcept>
#include "XtalDAQ/OnlineCBCAnalyser/interface/SCurve.h"

CPPUNIT_TEST_SUITE_REGISTRATION(SCurveUnitTestSuite);

void SCurveUnitTestSuite::setUp()
{

}

void SCurveUnitTestSuite::testSaveAndRestore()
{
	const std::string testOutputFilename="testOutput.blah";

	cbcanalyser::DetectorSCurves detectorSCurves;
	cbcanalyser::DetectorSCurves restoredDetectorSCurves;

	// First fill with random data
	detectorSCurves.getStripSCurve( 0, 0, 0 ).getEntry(0).eventsOn()+=30;
	detectorSCurves.getStripSCurve( 0, 0, 0 ).getEntry(0).eventsOff()+=2342;
	detectorSCurves.getStripSCurve( 0, 0, 1 ).getEntry(0).eventsOn()+=23;
	detectorSCurves.getStripSCurve( 0, 0, 1 ).getEntry(0).eventsOff()+=34567;
	detectorSCurves.getStripSCurve( 0, 1, 0 ).getEntry(0).eventsOn()+=43152;
	detectorSCurves.getStripSCurve( 1, 0, 0 ).getEntry(0).eventsOn()+=3223;
	detectorSCurves.getStripSCurve( 1, 0, 0 ).getEntry(0).eventsOn()+=9;

	// Write out the data to a file
	{ // block to keep temporary variables' scope limited
		std::ofstream outputFile( testOutputFilename, std::ios::trunc );
		CPPUNIT_ASSERT( outputFile.is_open() );

		CPPUNIT_ASSERT_NO_THROW( detectorSCurves.dumpToStream(outputFile) );
		outputFile.close();
	}

	// Read back the saved data into a different object
	{ // block to keep temporary variables' scope limited
		std::ifstream inputFile( testOutputFilename );
		CPPUNIT_ASSERT( inputFile.is_open() );

		CPPUNIT_ASSERT_NO_THROW( restoredDetectorSCurves.restoreFromStream(inputFile) );
		inputFile.close();
	}


	//
	// Compare what was restored to the original object
	// and make sure they're the same.
	//
	const auto fedIndices=detectorSCurves.getValidFedIndices();
	const auto restoredFedIndices=restoredDetectorSCurves.getValidFedIndices();
	CPPUNIT_ASSERT_EQUAL( fedIndices.size(), restoredFedIndices.size() );

	for( size_t fedIndex=0; fedIndex<fedIndices.size() && fedIndex<restoredFedIndices.size(); ++fedIndex )
	{
		CPPUNIT_ASSERT_EQUAL( fedIndices[fedIndex], restoredFedIndices[fedIndex] );

		auto& fedSCurve=detectorSCurves.getFedSCurves(fedIndex);
		auto& restoredFedSCurve=restoredDetectorSCurves.getFedSCurves(fedIndex);

		const auto channelIndices=fedSCurve.getValidChannelIndices();
		const auto restoredChannelIndices=restoredFedSCurve.getValidChannelIndices();
		CPPUNIT_ASSERT_EQUAL( channelIndices.size(), restoredChannelIndices.size() );

		for( size_t channelIndex=0; channelIndex<channelIndices.size() && channelIndex<restoredChannelIndices.size(); ++channelIndex )
		{
			CPPUNIT_ASSERT_EQUAL( channelIndices[channelIndex], restoredChannelIndices[channelIndex] );

			auto& channelSCurve=fedSCurve.getFedChannelSCurves(channelIndex);
			auto& restoredChannelSCurve=restoredFedSCurve.getFedChannelSCurves(channelIndex);

			const auto stripIndices=channelSCurve.getValidStripIndices();
			const auto restoredStripIndices=restoredChannelSCurve.getValidStripIndices();
			CPPUNIT_ASSERT_EQUAL( stripIndices.size(), restoredStripIndices.size() );

			for( size_t stripIndex=0; stripIndex<stripIndices.size() && stripIndex<restoredStripIndices.size(); ++stripIndex )
			{
				CPPUNIT_ASSERT_EQUAL( stripIndices[stripIndex], restoredStripIndices[stripIndex] );

				const auto& sCurve=channelSCurve.getStripSCurve(stripIndex);
				const auto& restoredSCurve=restoredChannelSCurve.getStripSCurve(stripIndex);

				// I actually bothered to write an equality operator for this class
				CPPUNIT_ASSERT( sCurve==restoredSCurve );
			}
		}
	}
}

void SCurveUnitTestSuite::testCalculateBinning()
{
	std::vector<float> binCentres;
	binCentres.push_back(3);
	binCentres.push_back(5);
	binCentres.push_back(8);
	binCentres.push_back(9);

	// The bin centres above should produce the following binning:
	// 2-4      : bin with centre 3
	// 4-6      : bin with centre 5
	// 6-7.5    : dummy bin as a spacer
	// 7.5-8.5  : bin with centre 8
	// 8.5-9.5  : bin with centre 9
	//
	// So the output vector should contain [2,4,6,7.5,8.5,9.5] (lower edges plus global upper edge)


	std::vector<float> binLowerEdges;
	cbcanalyser::calculateBinning( binLowerEdges, binCentres );

	CPPUNIT_ASSERT( binLowerEdges.size()==6 );
	CPPUNIT_ASSERT( binLowerEdges[0]==2 );
	CPPUNIT_ASSERT( binLowerEdges[1]==4 );
	CPPUNIT_ASSERT( binLowerEdges[2]==6 );
	CPPUNIT_ASSERT( binLowerEdges[3]==7.5 );
	CPPUNIT_ASSERT( binLowerEdges[4]==8.5 );
	CPPUNIT_ASSERT( binLowerEdges[5]==9.5 );

	//
	// Now try the same thing with a map and custom value retriever
	//
	std::map<float,std::string> centresAndValues;
	centresAndValues[3]="Some random";
	centresAndValues[5]="data that";
	centresAndValues[8]="I don't";
	centresAndValues[9]="care about";
	// Adding an extra bin at the end changes the widths of both the bin centred on 9
	// and the bin centred on 8. The bin centred on 9 has to be smaller, which allows
	// the bin centred on 8 to be bigger.
	centresAndValues[9.5]="blah blah blah";
	// The bin centres above should now produce the following binning:
	// 2-4        : bin with centre 3
	// 4-6        : bin with centre 5
	// 6-7.25     : dummy bin as a spacer
	// 7.25-8.75  : bin with centre 8
	// 8.75-9.25  : bin with centre 9
	// 9.25-9.75  : bin with centre 9.5
	//
	// So the output vector should contain [2,4,6,7.25,8.75,9.25,9.75] (lower edges plus global upper edge)


	binLowerEdges.clear();
	cbcanalyser::calculateBinning( binLowerEdges, centresAndValues, [](std::map<float,std::string>::const_iterator iValue)->float{return iValue->first;} );


	CPPUNIT_ASSERT( binLowerEdges.size()==7 );
	CPPUNIT_ASSERT( binLowerEdges[0]==2 );
	CPPUNIT_ASSERT( binLowerEdges[1]==4 );
	CPPUNIT_ASSERT( binLowerEdges[2]==6 );
	CPPUNIT_ASSERT( binLowerEdges[3]==7.25 );
	CPPUNIT_ASSERT( binLowerEdges[4]==8.75 );
	CPPUNIT_ASSERT( binLowerEdges[5]==9.25 );
	CPPUNIT_ASSERT( binLowerEdges[6]==9.75 );

}
