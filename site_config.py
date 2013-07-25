# Configuration file for ping.py and pinggraph.py

# Address range of the local network
first_ip = "192.168.1.1"
last_ip = "192.168.1.254"

# Any external IP addresses you want to test

extra_ips = [ '8.8.8.8' ]

# IP addresses to be identified by name in the output
# This will generally need to include the local host,
# as it won't turn up in the ARP cache.
known_ips = {
 # EXAMPLE DATA: you *will* need to change this
 "8.8.8.8" : "Google DNS",
 "192.168.1.146" : "raspberrypi",
}

# MAC addresses of devices to be identified by name
# in the output. This may be empty.
known_macs = {

 # EXAMPLE DATA: you *will* need to change this
 "f8:d1:11:54:f9:ac" : "wifi-router",
 "58:b0:11:84:2c:a1" : "ipad",
 "b8:27:eb:4b:6d:12" : "raspi2",
 "9c:02:98:3d:c3:68" : "galaxy-tab",
}

# File used to communicate between ping.py and pinggraph.py
input_file = "/tmp/pinglog-%(date)s.csv"

# Directory used to hold generated results;
# must be writable by the user running pinggraph.py
output_path = "/var/www/pages/pinger"

# Name of page to be created showing results
page_name = "netstats.html"

# Text to include in page linking to stylesheet.
stylesheet='<link rel=stylesheet type="text/css" href="/default.css">'

# Name of a valid font file to use when plotting charts
graph_font = "/usr/share/fonts/truetype/ttf-dejavu/DejaVuSansMono.ttf"

