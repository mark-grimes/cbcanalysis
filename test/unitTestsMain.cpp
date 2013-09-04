/** @file Copied this almost verbatim from the cppunit example cppunit/examples/simple
 *
 * Main function to run any registered test suites. Which test suites and the name
 * of the executable produced depends on whatever is setup in BuildFile.xml. At time
 * of writing the executable will be called "SimGeneral_TrackingAnalysis_unitTests"
 * and the test suites will be any in this directory that have a filename ending
 * in "_UnitTests.cpp".
 *
 * Remember that if you add any more *UnitTests.cpp files to the directory they won't
 * be noticed unless you update the modification time of BuildFile.xml, e.g. with
 * "touch BuildFile.xml".
 *
 * @author copied by Mark Grimes (mark.grimes@bristol.ac.uk)
 * @date 26/Jul/2013
 */

#include <cppunit/BriefTestProgressListener.h>
#include <cppunit/CompilerOutputter.h>
#include <cppunit/extensions/TestFactoryRegistry.h>
#include <cppunit/TestResult.h>
#include <cppunit/TestResultCollector.h>
#include <cppunit/TestRunner.h>


int main( int argc, char* argv[] )
{
	// Create the event manager and test controller
	CPPUNIT_NS::TestResult controller;

	// Add a listener that colllects test result
	CPPUNIT_NS::TestResultCollector result;
	controller.addListener( &result );

	// Add a listener that print dots as test run.
	CPPUNIT_NS::BriefTestProgressListener progress;
	controller.addListener( &progress );

	// Add the top suite to the test runner
	CPPUNIT_NS::TestRunner runner;
	runner.addTest( CPPUNIT_NS::TestFactoryRegistry::getRegistry().makeTest() );
	runner.run( controller );

	// Print test in a compiler compatible format.
	CPPUNIT_NS::CompilerOutputter outputter( &result, CPPUNIT_NS::stdCOut() );
	outputter.write();

	return result.wasSuccessful() ? 0 : 1;
}
