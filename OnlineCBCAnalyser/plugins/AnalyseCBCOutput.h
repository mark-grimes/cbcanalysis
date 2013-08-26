#ifndef XtalDAQ_OnlineCBCAnalyser_plugins_AnalyseCBCOutput_h
#define XtalDAQ_OnlineCBCAnalyser_plugins_AnalyseCBCOutput_h

#include <fstream>
#include <FWCore/Framework/interface/Frameworkfwd.h>
#include <FWCore/Framework/interface/EDAnalyzer.h>

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
		std::string I2CValuesFilename_;
		void readI2CValues();
		std::string outputFilename_;
		void writeOutput();
		std::ostream* pOutput_;
		std::ofstream outputFile_;
		std::vector<TH1*> pTestHistograms_;
		TH1* pAllChannels_;
		struct ChannelData
		{
			size_t numberOn;
			size_t numberOff;
			float threshold;
		};
		std::vector<ChannelData> channels_;
		size_t eventsProcessed_;
	};

} // end of namespace cbcanalyser

#endif
