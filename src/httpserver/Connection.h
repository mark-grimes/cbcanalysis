//
// connection.hpp
// ~~~~~~~~~~~~~~
//
// Copyright (c) 2003-2013 Christopher M. Kohlhoff (chris at kohlhoff dot com)
//
// Distributed under the Boost Software License, Version 1.0. (See accompanying
// file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
//

#ifndef httpserver_Connection_h
#define httpserver_Connection_h

#include <array>
#include <memory>
#include <boost/asio.hpp>
#include "reply.hpp"
#include "request.hpp"
#include "request_parser.hpp"

namespace httpserver
{
	class RequestHandler;
	class ConnectionManager;
}

namespace httpserver
{

	/// Represents a single connection from a client.
	class Connection : public std::enable_shared_from_this<Connection>
	{
	public:
		Connection( const Connection& )=delete;
		Connection& operator=( const Connection& )=delete;

		/// Construct a connection with the given socket.
		explicit Connection( boost::asio::ip::tcp::socket socket, httpserver::ConnectionManager& manager, httpserver::RequestHandler& handler );

		/// Start the first asynchronous operation for the connection.
		void start();

		/// Stop all asynchronous operations associated with the connection.
		void stop();

	private:
		/// Perform an asynchronous read operation.
		void do_read();

		/// Perform an asynchronous write operation.
		void do_write();

		/// Socket for the connection.
		boost::asio::ip::tcp::socket socket_;

		/// The manager for this connection.
		httpserver::ConnectionManager& connectionManager_;

		/// The handler used to process the incoming request.
		RequestHandler& requestHandler_;

		/// Buffer for incoming data.
		std::array<char,8192> buffer_;

		/// The incoming request.
		http::server::request request_;

		/// The parser for the incoming request.
		http::server::request_parser request_parser_;

		/// The reply to be sent back to the client.
		http::server::reply reply_;
	};

	typedef std::shared_ptr<Connection> Connection_ptr;

} // namespace httpserver

#endif // HTTP_CONNECTION_HPP
