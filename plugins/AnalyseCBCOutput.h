#ifndef XtalDAQ_OnlineCBCAnalyser_plugins_AnalyseCBCOutput_h
#define XtalDAQ_OnlineCBCAnalyser_plugins_AnalyseCBCOutput_h

#include <fstream>
#include <FWCore/Framework/interface/Frameworkfwd.h>
#include <FWCore/Framework/interface/EDAnalyzer.h>
#include "XtalDAQ/OnlineCBCAnalyser/interface/SCurve.h"

//
// Forward declarations
//
class TH1;


namespace cbcanalyser
{
	/** @brief Analyser to look over the CBC output written by the GlibStreamer XDAQ plugin.
	 *
	 * @author Mark Grimes (mark.grimes@bristol.ac.uk)
	 * @date 08/May2013
	 */
	class AnalyseCBCOutput : public edm::EDAnalyzer
	{
	public:
		explicit AnalyseCBCOutput( const edm::ParameterSet& config );
		~AnalyseCBCOutput();

		static void fillDescriptions( edm::ConfigurationDescriptions& descriptions );
	private:
		virtual void beginJob();
		virtual void analyze( const edm::Event& event, const edm::EventSetup& setup );
		virtual void endJob();

		virtual void beginRun( const edm::Run& run, const edm::EventSetup& setup );
		virtual void endRun( const edm::Run& run, const edm::EventSetup& setup );
		virtual void beginLuminosityBlock( const edm::LuminosityBlock& lumiBlock, const edm::EventSetup& setup );
		virtual void endLuminosityBlock( const edm::LuminosityBlock& lumiBlock, const edm::EventSetup& setup );
	protected:
		/** @brief Save the current state to disk so that another AnalyseCBCOutput can be restored to the same state.
		 *
		 * I've been having a lot of problems with the DAQ runcontrol. The only way I can take multiple runs (as of
		 * 04/Sep/2013) is to kill all the processes and start again, so I need a way of restoring the analyser's
		 * state after a run.
		 */
		void saveState( const std::string& filename );
		/** @brief Restore to the state that was saved to a call to saveState.
		 *
		 * See the note on saveState for an explanation of why this is necassary.
		 */
		void restoreState( const std::string& filename );
		/** @brief Filename to save the state to. Optional - if empty the state is not restored or saved to disk. */
		std::string savedStateFilename_;

		DetectorSCurves detectorSCurves_;

		/** @brief Dumps the s-curves to the output stream for debugging */
		void dumpSCurveToStream( std::ostream& output );

		/** @brief Reads strip threshold offsets from the filename stored in I2CValuesFilename_ and store them
		 * in stripThresholdOffsets_.
		 *
		 * @post  stripThresholdOffsets_ is overwritten with any entries in the file specified in I2CValuesFilename_.
		 */
		void readI2CValues();
		std::string I2CValuesFilename_;
		std::vector<unsigned int> stripThresholdOffsets_;

		size_t eventsProcessed_;
		size_t runsProcessed_;

		class cbcanalyser::SCurveEntry* pSCurveEntryToMonitorForDQM_;
	};

} // end of namespace cbcanalyser

#endif
