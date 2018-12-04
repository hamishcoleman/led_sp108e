#!/usr/bin/env python3
#
# Look at a packet capture of the app sending the WIFI configuration and try
# to decode what is actually going on

import sys
import pcap

pc = pcap.pcap(sys.argv[1])
pc.setfilter('udp port 7001')

sync_prev = None

time_first = None
for timestamp, packet in pc:
    if time_first is None:
        time_first = timestamp

    time_delta = timestamp - time_first
    ip_dest = packet[0x21]
    data_len = len(packet) - 42;

    # ip_id = packet[18:20]
    # ip_checksum = packet[0x18:0x1a]
    # udp_checksum = packet[0x28:0x2a]
    # print("{:.3f} {:02x} {:04x} {:04x} {:04x} {:03x}".format(
    #     time_delta,
    #     ip_dest,
    #     ip_id[0]*0x100 + ip_id[1],
    #     ip_checksum[0]*0x100 + ip_checksum[1],
    #     udp_checksum[0]*0x100 + udp_checksum[1],
    #     data_len,
    # ))

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
 

    # clear the sync info
    sync_prev = None

    print("{:.3f} {:02x} {:03x} UNK {:010b}".format(
        time_delta, ip_dest,
        data_len, data_len,
    ))
