#!/usr/bin/env python3
#
# Connect to a SP108E and send the same packets as sniffed, printing any
# printing any replies

import argparse

import socket
import binascii

def do_options():
    a = argparse.ArgumentParser('Reverse Engineer Protocol for SP108E')
    a.add_argument('-H','--host', action='store', default='192.168.4.1')
    a.add_argument('-p','--port', action='store', default=8189)

    return a.parse_args()

def txn_sync(sock, sendbytes):
    """ Perform a synchronous transaction """


    # TODO - if verbose
    sendhex = binascii.hexlify(sendbytes).decode('utf-8')
    print("> {}".format(sendhex))

    sock.send(sendbytes)
    recvbytes = sock.recv(4096)

    # TODO - if verbose
    recvhex = binascii.hexlify(recvbytes).decode('utf-8')
    print("< {}".format(recvhex))

    return recvbytes

def txn_sync_expect(sock, sendbytes, expectbytes):
    """ Perform a txn_sync() and confirm the result is as expected """
    r = txn_sync(sock, sendbytes)
    assert(r == expectbytes)
    return r

def main(args):
    print("Connecting to {}:{}".format(args.host, args.port))

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((args.host, args.port))

    txn_sync_expect(s, b'8\xe5\x23\xd3\xd5\x83', b'\x01\x02\x03\x04\x05\xcf')
    txn_sync_expect(s, b'8\xc5\x1b\xa9\xd5\x83', b'\x01\x02\x03\x04\x05\x6d')
    txn_sync_expect(s, b'8\xd9\x0f\xbd\x10\x83', b'\x38\x01\xfc\x80\xff\x02\x00\x32\x00\x01\xff\x00\x00\x03\x00\xff\x83')

if __name__ == '__main__':
    args = do_options()
    main(args)

