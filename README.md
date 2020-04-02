# Network Distance Vector Routing

Team 1

Jorge Alfredo Martinez

Ezequiel Donovan

Thomas Pashoros

Jonathan Lacanlale


A simplified version of the Distance Vector Routing Protocol.
The protocol will be run on top of four servers/laptops (behaving as routers) using TCP or UDP. Each
server runs on a machine at a pre-defined port number. The servers should be able to output their
forwarding tables along with the cost and should be robust to link changes. A server should send out
routing packets only in the following two conditions: a) periodic update and b) the user uses
command asking for one. This is a little different from the original algorithm which immediately sends
out update routing information when routing table changes.