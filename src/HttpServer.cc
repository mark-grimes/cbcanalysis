// All of this code was heavily copied from the boost asio examples so I'll include
// the licence from that.
//
//
// Copyright (c) 2003-2013 Christopher M. Kohlhoff (chris at kohlhoff dot com)
//
// Distributed under the Boost Software License, Version 1.0. (See accompanying
// file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
//


#include "XtalDAQ/OnlineCBCAnalyser/interface/HttpServer.h"

#include <fstream>
#include <thread>
#include <boost/asio.hpp>
#include "httpserver/ConnectionManager.h"
#include "httpserver/request.hpp"
#include "httpserver/reply.hpp"
#include "httpserver/mime_types.hpp"
#include "httpserver/RequestHandler.h"


namespace cbcanalyser
{
	class HttpServerPrivateMembers
	{
	public:
		HttpServerPrivateMembers();

		/// Perform an asynchronous accept operation.
		void do_accept();

		/// Wait for a request to stop the server.
		void do_await_stop();

		/// The io_service used to perform asynchronous operations.
		boost::asio::io_service io_service_;

		/// The signal_set is used to register for process termination notifications.
		boost::asio::signal_set signals_;

		/// Acceptor used to listen for incoming connections.
		boost::asio::ip::tcp::acceptor acceptor_;

		/// The connection manager which owns all live connections.
		httpserver::ConnectionManager connectionManager_;

		/// The next socket to be accepted.
		boost::asio::ip::tcp::socket socket_;

		/// The handler for all incoming requests.
		httpserver::RequestHandler request_handler_;

		/// Thread for the run loop
		std::thread runThread_;
	};
}


cbcanalyser::HttpServer::HttpServer()
	: pImple( new cbcanalyser::HttpServerPrivateMembers )
{

}

cbcanalyser::HttpServer::~HttpServer()
{

}

void cbcanalyser::HttpServer::start( const std::string& address, const std::string& port )
{
	// Make sure the server isn't already running
	if( !pImple->runThread_.joinable() )
	{
		pImple->do_await_stop();

		// Open the acceptor with the option to reuse the address (i.e. SO_REUSEADDR).
		boost::asio::ip::tcp::resolver resolver(pImple->io_service_);
		boost::asio::ip::tcp::endpoint endpoint = *resolver.resolve({address, port});
		pImple->acceptor_.open(endpoint.protocol());
		pImple->acceptor_.set_option(boost::asio::ip::tcp::acceptor::reuse_address(true));
		pImple->acceptor_.bind(endpoint);
		pImple->acceptor_.listen();

		pImple->do_accept();

		// Start the io_service running in a new thread because it blocks
		pImple->runThread_=std::thread( [&]{ pImple->io_service_.run(); } );
	}
}

void cbcanalyser::HttpServer::stop()
{
	// Check to see the server is running
	if( pImple->runThread_.joinable() )
	{
		pImple->io_service_.stop();
		pImple->acceptor_.close();
		pImple->runThread_.join();
	}
}


cbcanalyser::HttpServerPrivateMembers::HttpServerPrivateMembers()
	: io_service_(),
	  signals_(io_service_),
	  acceptor_(io_service_),
	  connectionManager_(),
	  socket_(io_service_)
{
	// Register to handle the signals that indicate when the server should exit.
	// It is safe to register for the same signal multiple times in a program,
	// provided all registration for the specified signal is made through Asio.
	signals_.add(SIGINT);
	signals_.add(SIGTERM);
#	if defined(SIGQUIT)
		signals_.add(SIGQUIT);
#	endif // defined(SIGQUIT)
}


void cbcanalyser::HttpServerPrivateMembers::do_accept()
{
	acceptor_.async_accept(socket_,
		[this](boost::system::error_code ec)
		{
			// Check whether the server was stopped by a signal before this
			// completion handler had a chance to run.
			if (!acceptor_.is_open())
			{
				return;
			}

			if (!ec)
			{
				connectionManager_.start(std::make_shared<httpserver::Connection>(std::move(socket_), connectionManager_, request_handler_));
			}

			do_accept();
		});
}

void cbcanalyser::HttpServerPrivateMembers::do_await_stop()
{
	signals_.async_wait(
		[this](boost::system::error_code /*ec*/, int /*signo*/)
		{
			// The server is stopped by cancelling all outstanding asynchronous
			// operations. Once all operations have finished the io_service::run()
			// call will exit.
			acceptor_.close();
			connectionManager_.stop_all();
		});
}
