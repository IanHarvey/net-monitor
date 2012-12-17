net-monitor
===========

This is a couple of Python scripts which ping a block of IP addresses on a
network, and produce a simple HTML page containing charts of the results.

The code tries to detect the MAC addresses corresponding to each IP address,
so that individual devices on the network can be identified even if they're
using DHCP.

Legals
======

This code comes with no warranty, or NO WARRANTY if you need to be shouted at.

It is placed in the public domain by its author, Ian Harvey.

Instructions
============

1) Install a suitable web-server to view the results. I've been testing this
   code using lighttpd on a Raspberry Pi.
   
2) Create a directory under /var/www/ (or wherever) to hold the HTML 
   output page and its associated charts. This is static content; there
   is no cgi involved.
   
3) If you wish, edit stylesheet file default.css, and copy it to a place
   accessible by the web server. 

4) Edit site_config.py to configure the program to your environment; the 
   instructions are in the file itself.

5) Start ping.py as root, and then start pinggraph.py (recommended to not
   be run as root). 

6) If you wish to run the programs with no user logged on, I recommend
   installing and using GNU screen.

Have fun!

Cheers
IH
