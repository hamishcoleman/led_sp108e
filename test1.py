#!/usr/bin/env python3
#
# Connect to a SP108E and send the same packets as sniffed, printing any
# printing any replies

import argparse

import socket
import binascii


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
    assert data[13] == 3
    assert data[14] == 0
    assert data[15] == 0 # have also seen 0xff in this field # noqa


def test_sequence_1(s):
    """ Send the test sequence and confirm that things look OK """
    txn_sync_expect(s,
                    frame(0xd5, b'\xe5\x23\xd3'), b'\x01\x02\x03\x04\x05\xcf')
    txn_sync_expect(s,
                    frame(0xd5, b'\xc5\x1b\xa9'), b'\x01\x02\x03\x04\x05\x6d')
    txn_sync_expect(
        s, frame(0x10, b'\xd9\x0f\xbd'),
        b'\x38\x01\xfc\x01\x0a\x02\x00\x3c\x00\x01\xb3\x00\xff\x03\x00\xff\x83'
    )
    # [7] is the number of leds in each segment (perhaps [6,7])
    # suggesting that [8,9] is the number of segments


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

    assert_status_unknown(state)


def subc_test1(sock, args):
    """Run a simple sanity check on the device"""
    test_sequence_1(sock)


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
    'get_device_name': subc_get_device_name,
    'speed':   subc_speed,
    'status':  subc_status,
    'test1':   subc_test1,
    'testcmd': subc_testcmd,
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

    # txn_sync(s, frame(0xd5, b'\x00\x00\x00')) # check_device?


if __name__ == '__main__':
    args = do_options()
    main(args)
