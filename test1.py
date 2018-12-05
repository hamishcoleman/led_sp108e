#!/usr/bin/env python3
#
# Connect to a SP108E and send the same packets as sniffed, printing any
# printing any replies

import argparse

import socket
import random

import commands as cmd


def txn(sock, sendbytes):
    """ Perform a tx transaction """

    # TODO - if verbose
    print("> {}".format(sendbytes.hex()))

    sock.send(sendbytes)


def rxn(sock):
    """ Listen for a reply packet """
    recvbytes = sock.recv(4096)

    # TODO - if verbose
    print("< {}".format(recvbytes.hex()))

    return recvbytes


def txn_sync(sock, sendbytes):
    """ Perform a synchronous tx/rx transaction """

    txn(sock, sendbytes)
    return rxn(sock)


def txn_sync_expect(sock, sendbytes, expectbytes):
    """ Perform a txn_sync() and confirm the result is as expected """
    r = txn_sync(sock, sendbytes)
    assert(r == expectbytes)
    return r


def cmd_check_device(sock, challenge):
    """Send a check packet, and confirm the result is sane"""
    if challenge is None:
        challenge = 0x73a52b  # chosen by a fair dice roll

    r = txn_sync(sock, cmd.check_device(challenge))

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


def test_frame(dotcount, firstrandom, firstfill):
    """Generate a single frame to send to the array"""
    maxlen = 900        # Number of bytes in a frame
    stride = (maxlen // 3) // dotcount * 3

    offset = firstrandom*stride   # address of first non blank pixel
    minlen1 = firstfill*stride    # address of last pixel with random color
    maxdots = dotcount*stride     # address of first non displayed pixel

    # R G B followed by 12 unknown bytes
    fill = bytearray([0x11, 0x00, 0x00])

    a = bytearray(maxlen)

    while offset < minlen1:
        a[offset:offset+3] = bytearray([
            random.randrange(256),
            random.randrange(256),
            random.randrange(256),
        ])
        offset += stride

    while offset < maxdots:
        a[offset:offset+3] = fill
        offset += stride

    return a


def subc_testpreview(sock, args):
    """Try to send video"""
    dotcount = int(args.subc_args[0], 0)
    firstrandom = int(args.subc_args[1], 0)
    firstfill = int(args.subc_args[2], 0)

    txn_sync_expect(sock, cmd.frame(cmd.CMD_CUSTOM_PREVIEW, None), b'\x31')

    for i in range(100):
        a = test_frame(dotcount, firstrandom, firstfill)
        # TODO - split array up into bits that are MSS rounded down to nearest
        # 15 byte boundary and hope to solve the MTU issue
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
    name = txn_sync(sock, cmd.get_device_name()).decode('utf8')
    # FIXME - first char is a null - check and remove
    print("Connected to {}".format(name))


def subc_mode_change(sock, args):
    assert (len(args.subc_args) == 1), "command takes 1 arg"
    mode = int(args.subc_args[0], 0)
    txn(sock, cmd.mode_change(mode))


def subc_set_ic_model(sock, args):
    assert (len(args.subc_args) == 1), "command takes 1 arg"
    model = int(args.subc_args[0], 0)
    txn(sock, cmd.set_ic_model(model))


def subc_speed(sock, args):
    """Set automatic sequence display speed"""
    assert (len(args.subc_args) == 1), "speed command takes 1 arg"

    speed = int(args.subc_args[0])
    txn(sock, cmd.speed(speed))


def subc_status(sock, args):
    """Request device status"""

    state = txn_sync(sock, cmd.sync())
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

    cmdnr = int(args.subc_args[0], 0)

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

    txn(sock, cmd.frame(cmdnr, bytes([data1, data2, data3])))

    if cmdnr not in cmd.response or cmd.response[cmdnr]:
        # either we dont know if it responds, so we always listen
        # or we know for sure it has a response, so we listen
        rxn(sock)
    else:
        # Ensure we keep in sync by sending a quick check
        cmd_check_device(sock, None)


# A list of all the sub-commands
subc_cmds = {
    'check_device':     subc_check_device,
    'get_device_name':  subc_get_device_name,
    'mode_change':      subc_mode_change,
    'set_ic_model':     subc_set_ic_model,
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
