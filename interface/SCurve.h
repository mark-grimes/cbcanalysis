#ifndef XtalDAQ_OnlineCBCAnalyser_interface_SCurve_h
#define XtalDAQ_OnlineCBCAnalyser_interface_SCurve_h

#include <vector>
#include <map>
#include <cstddef>
#include <iosfwd>
#include <memory>

//
// Forward declarations
//
class TH1;
class TDirectory;

namespace cbcanalyser
{

	/** @brief Class to record data for a single bin in an s-curve.
	 *
	 * @author Mark Grimes (mark.grimes@bristol.ac.uk)
	 * @date 04/Sep/2013
	 */
	class SCurveEntry
	{
	public:
		SCurveEntry();
		bool operator==( const SCurveEntry& otherSCurveEntry ) const;
		bool operator!=( const SCurveEntry& otherSCurveEntry ) const;

		size_t& eventsOn();
		const size_t& eventsOn() const;
		size_t& eventsOff();
		const size_t& eventsOff() const;
		/** @brief Returns the fraction of events where the channel was on. */
		float fraction() const;
		/** @brief Returns simple error assuming poisson error on the number of events on, and no error on the total. */
		float fractionError() const;

		void dumpToStream( std::ostream& outputStream ) const;
		void restoreFromStream( std::istream& inputStream );
	protected:
		size_t eventsOn_;
		size_t eventsOff_;
	};

	/** @brief Class to record data to calculate an s-curve.
	 *
	 * @author Mark Grimes (mark.grimes@bristol.ac.uk)
	 * @date 04/Sep/2013
	 */
	class SCurve
	{
	public:
		/** @brief Constructor that specifies how many bins the SCurve will have. */
		SCurve( size_t numberOfEntries=256 );
		bool operator==( const SCurve& otherSCurve ) const;
		bool operator!=( const SCurve& otherSCurve ) const;

		SCurveEntry& getEntry( size_t index );
		const SCurveEntry& getEntry( size_t index ) const;
		/** @brief Returns the number of bins in the s-curve. */
		size_t size() const;

		/** @brief Creates a new root histogram and fills it with the s-curve data.
		 *
		 * The parent directory will be set to nullptr, so unless you call SetDirectory
		 * on the result the histogram will be held in memory only.
		 */
		std::unique_ptr<TH1> createHistogram( const std::string& name ) const;

		void dumpToStream( std::ostream& outputStream ) const;
		void restoreFromStream( std::istream& inputStream );

		/// @brief Returns the number of entries possible. I.e. any call to getEntry should be in the range 0 to this value-1
		size_t maxiumumEntries();
	protected:
		std::vector<SCurveEntry> entries_;
	};

	/** @brief Convenience class to store all the s-curves for a FED channel.
	 *
	 * Could have just used a raw std::map but this way makes the intention in the code a bit
	 * clearer.
	 *
	 * @author Mark Grimes (mark.grimes@bristol.ac.uk)
	 * @date 04/Sep/2013
	 */
	class FedChannelSCurves
	{
	public:
		SCurve& getStripSCurve( size_t stripNumber );
		/** @brief Returns a vector of the strip indices that have data recorded for them. */
		std::vector<size_t> getValidStripIndices() const;

		/** @brief Creates a series of sub-directories for histograms for all of the s-curves. */
		void createHistograms( TDirectory* pParentDirectory ) const;

		void dumpToStream( std::ostream& outputStream ) const;
		void restoreFromStream( std::istream& inputStream );
	protected:
		std::map<size_t,SCurve> stripSCurves_;
	};

	/** @brief Convenience class to store all the s-curves for a single FED.
	 *
	 * Could have just used a series of raw std::map but this way makes the intention in the
	 * code a bit clearer.
	 *
	 * @author Mark Grimes (mark.grimes@bristol.ac.uk)
	 * @date 04/Sep/2013
	 */
	class FedSCurves
	{
	public:
		FedChannelSCurves& getFedChannelSCurves( size_t fedChannelNumber );
		SCurve& getStripSCurve( size_t fedChannelNumber, size_t stripNumber );
		/** @brief Returns a vector of the channel indices that have data recorded for them. */
		std::vector<size_t> getValidChannelIndices() const;

		/** @brief Creates a series of sub-directories for histograms for all of the s-curves. */
		void createHistograms( TDirectory* pParentDirectory ) const;

		void dumpToStream( std::ostream& outputStream ) const;
		void restoreFromStream( std::istream& inputStream );
	protected:
		std::map<size_t,FedChannelSCurves> fedChannelSCurves_;
	};

	/** @brief Convenience class to store all the s-curves for all of the FEDs.
	 *
	 * Could have just used a series of raw std::map but this way makes the intention in the
	 * code a bit clearer.
	 *
	 * @author Mark Grimes (mark.grimes@bristol.ac.uk)
	 * @date 04/Sep/2013
	 */
	class DetectorSCurves
	{
	public:
		FedSCurves& getFedSCurves( size_t fedNumber );
		FedChannelSCurves& getFedChannelSCurves( size_t fedNumber, size_t fedChannelNumber );
		SCurve& getStripSCurve( size_t fedNumber, size_t fedChannelNumber, size_t stripNumber );
		/** @brief Returns a vector of the FED indices that have data recorded for them. */
		std::vector<size_t> getValidFedIndices() const;

		/** @brief Creates a series of sub-directories for histograms for all of the s-curves. */
		void createHistograms( TDirectory* pParentDirectory ) const;

		void dumpToStream( std::ostream& outputStream ) const;
		void restoreFromStream( std::istream& inputStream );
	protected:
		std::map<size_t,FedSCurves> fedSCurves_;
	};

} // end of namespace cbcanalyser

#endif
