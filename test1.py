#!/usr/bin/env python3
#
# Connect to a SP108E and send the same packets as sniffed, printing any
# printing any replies

import argparse

import socket
import binascii
import random


def txn(sock, sendbytes):
    """ Perform a tx transaction """

    # TODO - if verbose
    sendhex = binascii.hexlify(sendbytes).decode('utf-8')
    print("> {}".format(sendhex))

    sock.send(sendbytes)


def txn_sync(sock, sendbytes):
    """ Perform a synchronous tx/rx transaction """

    txn(sock, sendbytes)

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
    if data is None:
        data = b'\x00\x00\x00'

    packet = b'\x38' + data + bytes([cmd]) + b'\x83'
    assert(len(packet) == 6)
    return packet


def cmd_speed(sock, speed):
    return txn(sock, frame(0x03, bytes([speed]) + b'\x00\x00'))


def cmd_sync(sock):
    return txn_sync(sock, frame(0x10, None))


def cmd_get_device_name(sock):
    r = txn_sync(sock, frame(0x77, None))
    # FIXME - first char is a null - check and remove
    return r.decode('utf-8')


def cmd_check_device(sock, challenge):
    """Send a check packet, and confirm the result is sane"""
    if challenge is None:
        challenge = 0x73a52b # chosen by a fair dice roll # noqa

    data = bytes([
        challenge % 256,
        challenge // 256 % 256,
        challenge // 256 // 256 % 256,
    ])

    r = txn_sync(sock, frame(0xd5, data))

    assert r[0] == 1
    assert r[1] == 2
    assert r[2] == 3
    assert r[3] == 4
    assert r[4] == 5
    assert r[5] == (
        challenge & 0x53 |
        (challenge & 0x3f00) >> 6 |
        (challenge & 0xe00000) >> 21
    )

    return r[5]


#############################################################################
#
# Above this line, code should be generic enough to be turned into a library
#


def assert_frame(data):
    """Confirm that the correct framing bytes are present"""
    assert data[0] == 0x38
    assert data[-1] == 0x83


def assert_status_unknown(data):
    """Assert if any of the unknown state fields changes"""
    assert (
        (data[2] <= 179) or
        (data[2] >= 205 and data[2] <= 212) or
        (data[2] == 219) or
        (data[2] == 0xfc)
    )
    assert data[5] <= 5
    assert data[13] <= 0x1c
    assert data[14] == 0
    assert data[15] == 0 # have also seen 0xff in this field # noqa


def test_frame():
    """Generate a single frame to send to the array"""
    maxlen = 292
    minlen = 6
    offset = 0
    fill = b'\x11\x00\x00'

    a = bytes(offset*3)
    while len(a) < minlen*3:
        a += bytes([
            random.randrange(256),
            random.randrange(256),
            random.randrange(256),
            0, 0, 0,
            0, 0, 0,
            0, 0, 0,
            0, 0, 0,
        ])
    while len(a) < maxlen*3:
        a += fill

    return a


def subc_testpreview(sock, args):
    """Try to send video"""
    txn_sync_expect(sock, frame(0x24, None), b'\x31')

    for i in range(100):
        a = test_frame()
        txn_sync_expect(sock, a, b'\x31')


def subc_check_device(sock, args):
    """Send a bunch of check device packets"""
    assert (len(args.subc_args) == 1), "check_device command takes 1 arg"

    challenge = int(args.subc_args[0], 0)

    while challenge < 0x1000000:
        r = cmd_check_device(sock, challenge)
        print(
            "T: 0x{0:06x} == 0x{1:02x}, {0:24b} == {1:8b}".format(
                challenge, r
            )
        )
        challenge *= 2


def subc_get_device_name(sock, args):
    """Request device name"""
    print("Connected to {}".format(cmd_get_device_name(sock)))


def subc_speed(sock, args):
    """Set automatic sequence display speed"""
    assert (len(args.subc_args) == 1), "speed command takes 1 arg"

    speed = int(args.subc_args[0])
    cmd_speed(sock, speed)


def subc_status(sock, args):
    """Request device status"""
    state = cmd_sync(sock)
    assert_frame(state)

    modenames = {
        205: 'meteor',
        206: 'breathing',
        207: 'stack',
        208: 'flow',
        209: 'wave',
        210: 'flash',
        211: 'static',
        212: 'catch-up',
        219: 'custom_effect',
        0xfc: 'auto',
    }
    if state[2] in modenames:
        modename = modenames[state[2]]
    else:
        modename = ''

    # TODO - move this into the library and object model
    print("lamp =", state[1])
    print("mode = {} {}".format(state[2], modename))
    print("speed =", state[3])
    print("brightness =", state[4])
    print("rgb_order =", state[5])
    print("dotperseg =", state[6]*256 + state[7])
    print("segs =", state[8]*256 + state[9])
    print("staticcolor = {} {} {}".format(state[10], state[11], state[12]))
    print("ic_model =", state[13])

    assert_status_unknown(state)


def subc_testcmd(sock, args):
    """Send specified command and wait for response"""
    assert (len(args.subc_args) > 0), "testcmd takes at least 1 arg"
    assert (len(args.subc_args) < 5), "testcmd takes at most 4 args"

    cmd = int(args.subc_args[0], 0)

    if len(args.subc_args) > 1:
        data1 = int(args.subc_args[1], 0)
    else:
        data1 = 0

    if len(args.subc_args) > 2:
        data2 = int(args.subc_args[2], 0)
    else:
        data2 = 0

    if len(args.subc_args) > 3:
        data3 = int(args.subc_args[3], 0)
    else:
        data3 = 0

    txn_sync(sock, frame(cmd, bytes([data1, data2, data3])))


# A list of all the sub-commands
subc_cmds = {
    'check_device':     subc_check_device,
    'get_device_name':  subc_get_device_name,
    'speed':   subc_speed,
    'status':  subc_status,
    'testcmd': subc_testcmd,
    'testpreview': subc_testpreview,
}


def do_options():
    a = argparse.ArgumentParser('Reverse Engineer Protocol for SP108E')
    a.add_argument('-H', '--host', action='store', default='192.168.4.1')
    a.add_argument('-p', '--port', action='store', default='8189')

    subc = a.add_subparsers(help='Subcommand', dest='cmd')
    subc.required = True
    for key, value in subc_cmds.items():
        parser = subc.add_parser(key, help=value.__doc__)
        parser.set_defaults(func=value)
        parser.add_argument('subc_args', nargs='*')

    return a.parse_args()


def main(args):
    print("Connecting to {}:{}".format(args.host, int(args.port, 0)))

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((args.host, int(args.port, 0)))

    args.func(s, args)


if __name__ == '__main__':
    args = do_options()
    main(args)
