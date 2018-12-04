#!/usr/bin/env python3
#
# Look at a packet capture of the app sending the WIFI configuration and try
# to decode what is actually going on
#
# Create these captures by running tcpdump on the phone before using the
# "add device" option in the app

import sys
import pcap

pc = pcap.pcap(sys.argv[1])
pc.setfilter('udp port 7001')

sync_prev = None # track the most recent sync value

data_set = None   # track the ip_dest for the current group
data1_prev = None # track the first in each group of three
data2_prev = None # track the second in each group of three

time_first = None
for timestamp, packet in pc:
    if time_first is None:
        time_first = timestamp

    time_delta = timestamp - time_first
    ip_dest = packet[0x21]        # track the groups the app thinks it is sending
    data_len = len(packet) - 42;  # this ends up being the signal data

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
        data1_prev = data_len
        continue

    if data_set is not None:
        # we expect this to be a continuation of a previous triplet

        if data_set != ip_dest:
            print("{:.3f} {:02x} {:03x} TRIPLE bad".format(
                time_delta, ip_dest, data_len,
            ))

            data_set = None
            continue

        if data2_prev is None:
            data2_prev = data_len
            continue

        print("{:.3f} {:02x} -1 TRIPLE {:03x}  {:03x} {:03x} {:010b} {:010b}".format(
            time_delta, data_set,
            data2_prev, # looks like a data counter
            data1_prev,
            data_len,
            data1_prev,
            data_len,
        ))

        data_set = None
        data1_prev = None
        data2_prev = None
        continue

    print("{:.3f} {:02x} {:03x} UNK {:010b}".format(
        time_delta, ip_dest,
        data_len, data_len,
    ))
