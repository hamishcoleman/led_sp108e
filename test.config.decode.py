#!/usr/bin/env python3
#
# Look at a packet capture of the app sending the WIFI configuration and try
# to decode what is actually going on
#
# Create these captures by running tcpdump on the phone before using the
# "add device" option in the app

import sys
import pcap


def hexdump(buf):
    """Takes bytes and does a standard hexdump"""

    r = ""
    addr = 0
    hexdigits = ""
    strdigits = ""

    for b in buf:
        hexdigits += "{:02x} ".format(b)
        if b >= 0x20 and b <= 0x7e:
            strdigits += chr(b)
        else:
            strdigits += '.'

        if addr % 16 == 15:
            r += "H: {:03x}: {:48}|{}|\n".format(addr-15, hexdigits, strdigits)
            hexdigits = ""
            strdigits = ""
        addr += 1

    if len(strdigits):
        r += "H: {:03x}: {:48}|{}|\n".format(
            addr-len(strdigits),
            hexdigits,
            strdigits
        )
    return r


pc = pcap.pcap(sys.argv[1])
pc.setfilter('udp port 7001')

verbose = False

sync_prev = None        # track the most recent sync value

data_set = None         # track the ip_dest for the current group
data1_curr = None       # track the first in each group of three
data2_index = None      # track the second in each group of three
data_index_prev = None  # track the counter

data = {}

time_first = None
for timestamp, packet in pc:
    if time_first is None:
        time_first = timestamp

    time_delta = timestamp - time_first
    ip_dest = packet[0x21]        # essentially the triplet identifier
    data_len = len(packet) - 42   # this ends up being the signal data

    if data_len > 0x1ff:
        # This looks like part of a sync

        if sync_prev is None:
            if data_len != 0x203:
                print("{:.3f} {:02x} {:03x} SYNC bad start".format(
                    time_delta, ip_dest, data_len,
                ))

            # Populate the data and continue
            sync_prev = data_len
            continue

        if data_len != sync_prev-1:
            print("{:.3f} {:02x} {:03x} SYNC detected missing".format(
                time_delta, ip_dest, data_len,
            ))

        if data_len == 0x200:
            # the final in a sync set

            if verbose:
                print("{:.3f} {:02x} {:03x} SYNC end".format(
                    time_delta, ip_dest, data_len,
                ))
            sync_prev = None
            continue

        sync_prev = data_len
        continue

    if sync_prev is not None:
        # The sync sequence didnt end properly

        print("{:.3f} -1 -1 SYNC bad end".format(
            time_delta,
        ))
        sync_prev = None

    if data_set is None:
        # a fresh set of three values is arriving

        data_set = ip_dest
        data1_curr = data_len
        continue

    if data_set is not None:
        # we expect this to be a continuation of a previous triplet

        if data_set != ip_dest:
            print("{:.3f} {:02x} {:03x} TRIPLE bad".format(
                time_delta, ip_dest, data_len,
            ))

            data_set = None
            continue

        if data2_index is None:
            data2_index = data_len
            continue

        if data_index_prev is not None and data2_index != data_index_prev+1:
            data_index_prev = None

            if data2_index != 0x128:
                # only show error if it is not a restart
                print("{:.3f} {:02x} {:03x} TRIPLE bad counter".format(
                    time_delta, data_set,
                    data2_index,
                ))

        if verbose:
            print("{:.3f} {:02x} -1 TRIPLE {:03x}  {:03x} {:03x} {:010b} {:010b}".format( # noqa
                time_delta, data_set,
                data2_index,
                data1_curr,
                data_len,
                data1_curr,
                data_len,
            ))

        if data2_index in data:
            # confirm that the data has not changed
            if (data1_curr != data[data2_index][0] or
               data_len != data[data2_index][1]):
                print("{:.3f} {:02x} -1 DATA mismatch".format(
                    time_delta, data_set,
                ))
        else:
            data[data2_index] = list([data1_curr, data_len])

        # save the counter
        data_index_prev = data2_index

        data_set = None
        data1_curr = None
        data2_index = None
        continue

    print("{:.3f} {:02x} {:03x} UNK {:010b}".format(
        time_delta, ip_dest,
        data_len, data_len,
    ))

print("\n")
print("DATA")
packet = bytes()
for i in sorted(data.keys()):
    d0 = data[i][0]
    d2 = data[i][1]

    # TODO
    # - This guess does not work for a PSK with spaces in it
    # - some of the packet contents appear to be changing in unexpected ways
    guess = (
        (d2 & 0x7) |
        (~d2 & 8) |
        (d0 & 7) << 4 |
        (~d0 & 8) << 4
    )

    print("{:03x} {:03x} {:03x} : {:010b} {:010b} {:010b} : {:03x}".format(
        d0, i, d2,
        d0, i, d2,
        guess
    ))

    packet += bytes([guess])

print("")
print(hexdump(packet))
