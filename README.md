# mpddns

A simple service for only one purpose - running your own dynamic DNS.

## How to use
You need a (Linux) server in the Internet and a domain with access to the
nameserver settings. Create a NS record for a sub-domain of your domain
(e.g. home.example.com) which points to your server. On the server install
and run the *mpddns* server. Run periodically the *mpddns* client from within
your home network to update the sub-domain with the IP of your Internet
access.

## Configuration
For the server, see the example config file in directory server/etc/. The server
needs to be started with the command-line argument *-c* and the config file as
parameter. It will start into background (as a daemon), log messages will go
to the system log.

The client has no config file, check the command-line help for the required
arguments

## TODOs
(no special order)

 * enhance documentation
 * use Python logging module
 * make usage of the different update server configurable 
