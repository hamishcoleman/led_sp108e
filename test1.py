#!/usr/bin/env python3
#
# Connect to a SP108E and send the same packets as sniffed, printing any
# printing any replies

import argparse

import socket
import codecs

encode_hex = codecs.getencoder("hex_codec")

def do_options():
    a = argparse.ArgumentParser('Reverse Engineer Protocol for SP108E')
    a.add_argument('-H','--host', action='store', default='192.168.4.1')
    a.add_argument('-p','--port', action='store', default=8189)

    return a.parse_args()

def main(args):
    print("Connecting to {}:{}".format(args.host, args.port))

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((args.host, args.port))

    s.send(bytes.fromhex('38e523d3d583'))
    buf = s.recv(512)
    print("{}".format(encode_hex(buf)))

if __name__ == '__main__':
    args = do_options()
    main(args)

