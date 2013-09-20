#ifndef XtalDAQ_OnlineCBCAnalyser_interface_HttpServer_h
#define XtalDAQ_OnlineCBCAnalyser_interface_HttpServer_h

#include <memory>

namespace cbcanalyser
{
	/** @brief Very simple HTTP server copied from the boost asio examples
	 *
	 * http://www.boost.org/doc/libs/1_54_0/doc/html/boost_asio/examples/cpp11_examples.html
	 *
	 * @author Mark Grimes (mark.grimes@bristol.ac.uk) but functionality from site above.
	 * @date 22/Sep/2013
	 */
	class HttpServer
	{
	public:
		HttpServer();
		~HttpServer();
		void start( const std::string& address, const std::string& port );
		void stop();
	private:
		std::unique_ptr<class HttpServerPrivateMembers> pImple;
	};
}

#endif
