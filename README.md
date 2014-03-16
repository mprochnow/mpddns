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
For the server, see the example config file in directory *server/etc/*. If the 
server was started without any parameters, it looks at
*/etc/mpddns/mpddns.conf* for its config file. Use the command-line option
*-c* to change this behavior. The server will start into background 
(as daemon), log messages will go to the system log.

The client has no config file, check the command-line help for the required
arguments
