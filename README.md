SHET House Event Tunneling
==========================

SHET is a simple asynchronous communication framework designed to make it easy to connect physical things together to produce useful behaviours. It was designed with home automation in mind, but has many other uses.

This readme gives an overview of the kind of things that can be done with SHET. When you're ready to get started, see the [setup guide](/18sg/SHET/blob/master/doc/setup.md), and the [client library guide](/18sg/SHET/blob/master/doc/client.md).

Architecture
------------
![Diagram of SHET Architecture](/18sg/SHET/raw/master/doc/diagram_simple.png)

The SHET Server exists to connect clients together; all application logic lives in the clients, and the server just provides a uniform way for clients to talk to each other.

Node Types
----------

SHET consists of a directory tree containing the following kinds of nodes:

### Events

If client A provides an event node, this can be 'raised' by client a, and 'watched' by all other clients.

Example:

Client A has a motion detector connected to it, then it could create an event `/motion`, which other clients can watch. When motion is detected, client A raises the event, and all the watching clients are notified.

### Actions

If client A provides an action node, then other clients can 'call' it, and client A will be notified.

Example:

Client B is connected to a media player, and provides a node `/media/play`. Other clients can call this action, causing client A to be notified, and the media player to play.

### Properties

If client A provides a property node, then other nodes can 'get' or 'set' the value of it.

Example:

Client C is connected to a light, and provides a property node `/light`. Other clients can get this property to find the state of the light, and set this property to turn it on or off.

Values
------

The SHET protocol is based on [JSON](http://json.org/), and as such all values in SHET (parameters for actions and events, and property values) can take any value permissible by JSON.

Other Projects
--------------

If you would like to connect SHET to the physical world, you might want to take a look at [SHETSource](https://github.com/18sg/SHETSource).

Implementation
--------------

If you would like to implement a client library or an alternative server, you might be interested in the [protocol documentation](/18sg/SHET/blob/master/doc/spec.md).
