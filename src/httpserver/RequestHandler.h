//
// Largely copied from
// http://www.boost.org/doc/libs/1_54_0/doc/html/boost_asio/example/cpp11/http/server/request_handler.hpp
// so I'll include their licence.
//
//
// Copyright (c) 2003-2013 Christopher M. Kohlhoff (chris at kohlhoff dot com)
//
// Distributed under the Boost Software License, Version 1.0. (See accompanying
// file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
//

#ifndef httpserver_RequestHandler_h
#define httpserver_RequestHandler_h

#include <string>
//
// Forward declarations
//
namespace http
{
	namespace server
	{
		class reply;
		class request;
	}
}

namespace httpserver
{

	/// The common handler for all incoming requests.
	class RequestHandler
	{
	public:
		RequestHandler( const RequestHandler& )=delete;
		RequestHandler& operator=( const RequestHandler& )=delete;

		/// Construct with a directory containing files to be served.
		explicit RequestHandler();

		/// Handle a request and produce a reply.
		void handleRequest( const http::server::request& req, http::server::reply& rep );

	private:
		/// The directory containing the files to be served.
		std::string doc_root_;

		/// Perform URL-decoding on a string. Returns false if the encoding was
		/// invalid.
		static bool url_decode( const std::string& in, std::string& out );
	};

} // namespace httpserver

#endif // HTTP_REQUEST_HANDLER_HPP

