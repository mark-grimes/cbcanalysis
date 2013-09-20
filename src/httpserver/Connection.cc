//
// connection.cpp
// ~~~~~~~~~~~~~~
//
// Copyright (c) 2003-2013 Christopher M. Kohlhoff (chris at kohlhoff dot com)
//
// Distributed under the Boost Software License, Version 1.0. (See accompanying
// file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
//

#include "Connection.h"
#include <utility>
#include <vector>
#include "ConnectionManager.h"
#include "RequestHandler.h"

httpserver::Connection::Connection( boost::asio::ip::tcp::socket socket, httpserver::ConnectionManager& manager, RequestHandler& handler ) :
		socket_( std::move( socket ) ), connectionManager_( manager ), requestHandler_( handler )
{
}

void httpserver::Connection::start()
{
	do_read();
}

void httpserver::Connection::stop()
{
	socket_.close();
}

void httpserver::Connection::do_read()
{
	auto self( shared_from_this() );
	socket_.async_read_some( boost::asio::buffer( buffer_ ), [this, self](boost::system::error_code ec, std::size_t bytes_transferred)
	{
		if (!ec)
		{
			http::server::request_parser::result_type result;
			std::tie(result, std::ignore) = request_parser_.parse(
					request_, buffer_.data(), buffer_.data() + bytes_transferred);

			if (result == http::server::request_parser::good)
			{
				requestHandler_.handleRequest(request_, reply_);
				do_write();
			}
			else if (result == http::server::request_parser::bad)
			{
				reply_ = http::server::reply::stock_reply(http::server::reply::bad_request);
				do_write();
			}
			else
			{
				do_read();
			}
		}
		else if (ec != boost::asio::error::operation_aborted)
		{
			connectionManager_.stop(shared_from_this());
		}
	} );
}

void httpserver::Connection::do_write()
{
	auto self( shared_from_this() );
	boost::asio::async_write( socket_, reply_.to_buffers(), [this, self](boost::system::error_code ec, std::size_t)
	{
		if (!ec)
		{
			// Initiate graceful connection closure.
			boost::system::error_code ignored_ec;
			socket_.shutdown(boost::asio::ip::tcp::socket::shutdown_both,
					ignored_ec);
		}

		if (ec != boost::asio::error::operation_aborted)
		{
			connectionManager_.stop(shared_from_this());
		}
	} );
}
