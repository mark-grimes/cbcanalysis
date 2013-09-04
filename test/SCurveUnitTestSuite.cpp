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
	CPPUNIT_TEST_SUITE_END();

protected:

public:
	void setUp();

protected:
	void testSaveAndRestore();
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
