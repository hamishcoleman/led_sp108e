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

def frame(cmd, data):
    """ Add the framing bytes """
    packet = b'\x38' + data + bytes([cmd]) + b'\x83'
    assert(len(packet) == 6)
    return packet

def test_sequence_1(s):
    """ Send the test sequence and confirm that things look OK """
    txn_sync_expect(s, frame(0xd5, b'\xe5\x23\xd3'), b'\x01\x02\x03\x04\x05\xcf')
    txn_sync_expect(s, frame(0xd5, b'\xc5\x1b\xa9'), b'\x01\x02\x03\x04\x05\x6d')
    txn_sync_expect(s,
        frame(0x10, b'\xd9\x0f\xbd'),
        b'\x38\x01\xfc\x01\x0a\x02\x00\x3c\x00\x01\xb3\x00\xff\x03\x00\xff\x83'
    )
    # [7] is the number of leds in each segment (perhaps [6,7])
    # suggesting that [8,9] is the number of segments

def cmd_get_device_name(sock):
    r = txn_sync(sock, frame(0x77, b'\x00\x00\x00'))
    # FIXME - first char is a null - check and remove
    return r.decode('utf-8')

def main(args):
    print("Connecting to {}:{}".format(args.host, args.port))

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((args.host, args.port))

    print("Connected to {}".format(cmd_get_device_name(s)))

    test_sequence_1(s)

if __name__ == '__main__':
    args = do_options()
    main(args)

