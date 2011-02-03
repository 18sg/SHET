Setup Guide
===========

Requirements
------------

SHET Requires:

- [Python](http://www.python.org/) 2.x &mdash; it is known to work on at least 2.6 and 2.7.
- [Twisted](http://twistedmatrix.com/)


Get It
------

Download the code (you'll need [Git](http://git-scm.com/)):

	$ git clone git://github.com/18sg/SHET.git

Install it:

	$ cd SHET
	$ sudo python2 setup.py install

Server
------

To start the server:

	$ shetserv

This will start the server on port 11235; you'll probably want to poke a hole in your firewall for it. You should probably run this in screen.


Clients
-------

Included clients default to connecting to `localhost`. If you want to use a different server, you should set the environment variable `SHET_HOST` to it's address. Put something like this in your `~/.bashrc`:

	export SHET_HOST="104.97.120.33"

### MPD Client

To expose [MPD](http://mpd.wikia.com/) to SHET:

	$ python2 src/clients/mpd.py /mpd/

This will put a bunch of MPD controls in the `/mpd/` directory.

### Persistent Event Client

This client provides persistent events that are not connected to any one client, which can occasionally be useful. Have a look at the code to figure out what it does and how it does it &mdash; it's a fairly good example of how to write a SHET client. To start it:

	$ python2 src/clients/persist.py
