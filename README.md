This repository contains software to connect to and control the SP108E
LED Wifi Controller

The SP108E hardware is available in the Shenzhen LED markets for about
55RMB and will attach to the commonly available addressable led strings.

It is normally used with the provided iOS or Android app, however this
this repository trys to document the protocol and provide some sample code.

While most of the SP108E functions are mapped out, the python library is
not quite a complete implementation and it could also be made significantly
more user friendly.

# test1.py

Command line tool to show off the various functions and modes of the SP108E.
This is mostly a wrapper around the included python library and thus serves
as an example of how to call the library.

# test.config.decode.py

As part of trying to reverse engineer the WIFI configuration process, this
script was written to decode packet captures.

Using the normal Android app, tell it to configure a SP108E with the wifi
details and capture the resulting wifi packets.

Start this script with the pcap filemame and it will output the decoded
contents of the configuration process.

This is still a work in progress and has some missing details

# x11-to-led

This is a tool to demonstrate sending video data to the LED array.
It is a quick sample program and thus has many parameters hardcoded,
so serves mainly as an example of what is possible.
