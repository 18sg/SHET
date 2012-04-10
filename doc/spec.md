Shet (SHET House Event Tunneling) Protocol
==========================================

URIs
----

Unix style URIs, eg:

	/unix/style/uris

Generally URIs for high-level resources should represent their location and then the object/device being referred to, eg:

	/room/device/thing/property

However, this is only a convention, and not enforced by the protocol.

Command Format
--------------

Commands are encoded in [JSON](http://json.org), and generally in the format `["unique_id", "command", ... ]`

Unique IDs need only be unique to that session and client. IDs may only ever be used once for a single request and a response pair. There must at least be the above two elements for the command to be valid.

Commands
--------

#### return (any direction)

	["unique_id", "return", "status", "values"]

A message with the same unique_id as the request and the command return and a status which is 0 for success and otherwise failure.

#### ping (any direction)

	["unique_id", "ping", *arguments]

Simply returns a list containing the arguments.

#### register (to server)

	["unique_id", "register", "connection id"]

This names a connection; any other connections with this name are disconnected.
This is designed to make reconnection a bit smoother -- if the connection has
not yet timed out, then the server may still think the client is connected,
causing all sorts of nasty naming collisions when it tries to reconnect. Client
libraries are advised to create a random connection id at start up, and use that
across reconnections.

### Properties

#### mkprop (to server)

	["unique_id", "mkprop", "/uri/to/property"]

Sets up a mk property and registers that any requests for the value of this property will be sent to this client. Returns success or failure.

#### rmprop (to server)

	["unique_id", "rmprop", "/uri/to/property"]

  Removes a property (or variable) from the server.

#### getprop (to client)

	["unique_id", "getprop", "/uri/to/property"]

A request for the value of the property which should be responded to with a return command.

#### setprop (to client)

	["unique_id", "setprop", "/uri/to/property", "new_value"]

A request for the value of the property be changed. Return success.

#### get (to server)

	["unique_id", "get", "/uri/to/property"]

Fetch the value of a property.

#### set (to server)

	["unique_id", "set", "/uri/to/property", "new_value"]

Set the value of a given property. Returns success.

### Events

#### mkevent (to server)

	["unique_id", "mkevent", "/uri/to/event"]

Creates a new event on the server. Returns success.

#### rmevent (to server)

	["unique_id", "rmevent", "/uri/to/event"]

Removes the specified event from the server

#### raise (to server)

	["unique_id", "raise", "/url/to/event", "arguments"]

Raise the specified event sending the given arguments to any watching clients.

#### event (to client)

	["unique_id", "event", "/url/to/event", "arguments here"]

Sent to clients who have requested to watch an event

#### eventdelted (to client)

	["unique_id", "eventdelted", "/url/to/event"]

Sent to clients when an event they were watching is deleted

#### watch (to server)

	["unique_id", "watch", "/uri/to/event"]

Notifies the server that you want to be informed when this event is raised.

#### ignore (to server)

	["unique_id", "ignore", "/uri/to/event"]

Removes a request for a watch.

### Actions

#### mkaction (to server)

	["unique_id", "mkaction", "/url/to/action"]

Sets up the action and returns success.

#### rmaction (to server)

	["unique_id", "rmaction", "/url/to/action"]

Deletes the action and all responsibility for it.

#### call (to server)

	["unique_id", "call", "/url/to/action", "arguments here"]

Request a particular action be called. Returns the response.

#### docall (to client)

	["unique_id", "docall", "/url/to/action", "arguments here"]

A particular action has been requested, return the response.

Authentication (not implemented)
--------------------------------
On connect the server sends a challenge string. The client must send back a
hashed version of this string and a shared key between the client and server. No
special syntax is required. On failure the client will be disconnected. On
success a single 0 will be transmitted to the client. eg:

	b62a63a32554cd3729e05199f37284baeecebc719306f7243287060eb9b0ec470
	\______________________________/\______________________________/|
	      Challenge (32 chars)             Response (32 chars)      Authentication
	        A random string.              md5 of cat of key and     Successful
                                             challenge

