#ifndef XtalDAQ_OnlineCBCAnalyser_interface_CBCChannelUnpacker_h
#define XtalDAQ_OnlineCBCAnalyser_interface_CBCChannelUnpacker_h

namespace cbcanalyser
{
	/** @brief Simple utility class to unpack the bits from the CBC1 and present the result has a 128 bool vector.
	 *
	 * @author Mark Grimes (mark.grimes@bristol.ac.uk)
	 * @date 28/May/2013
	 */
	class CBCChannelUnpacker
	{
	public:
		CBCChannelUnpacker( const sistrip::FEDChannel& fedChannel );
		const std::vector<bool>& hits() const;
		bool hasData() const;
	private:
		bool hasData_;
		std::vector<bool> hits_;
	};
}

#endif
