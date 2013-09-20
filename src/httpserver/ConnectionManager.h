//
// connection_manager.hpp
// ~~~~~~~~~~~~~~~~~~~~~~
//
// Copyright (c) 2003-2013 Christopher M. Kohlhoff (chris at kohlhoff dot com)
//
// Distributed under the Boost Software License, Version 1.0. (See accompanying
// file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
//

#ifndef httpserver_ConnectionManager_h
#define httpserver_ConnectionManager_h

#include <set>
#include "Connection.h"

namespace httpserver
{

	/// Manages open connections so that they may be cleanly stopped when the server
	/// needs to shut down.
	class ConnectionManager
	{
	public:
		ConnectionManager( const ConnectionManager& )=delete;
		ConnectionManager& operator=( const ConnectionManager& )=delete;

		/// Construct a connection manager.
		ConnectionManager();

		/// Add the specified connection to the manager and start it.
		void start( Connection_ptr c );

		/// Stop the specified connection.
		void stop( Connection_ptr c );

		/// Stop all connections.
		void stop_all();

	private:
		/// The managed connections.
		std::set<Connection_ptr> connections_;
	};

} // namespace httpserver

#endif // httpserver_ConnectionManager_h
