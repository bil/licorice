try:
    new = False
    acquire_time = time.time()
    sem.acquire(timeout=0)
    if udp_packet_valid[udp_num_packets_i] == 1:
        new = True

        udp_num_bytes_i = int(udp_source_raw[udp_num_packets_i][0])
        udp_data[udp_num_packets_i, 0:udp_num_bytes_i] = udp_source_raw[
            udp_num_packets_i, 1 : 1 + udp_num_bytes_i
        ]
        udp_packet_valid[udp_num_packets_i] = 0
        udp_num_packets += 1
    release_time = time.time()
    sem.release()

    if new:
        print(
            str(udp_num_bytes_i) + "," + str(udp_data[udp_num_packets_i]),
            flush=True,
        )
        udp_data_len[udp_num_packets_i] = udp_num_bytes_i
        udp_num_packets_i += 1
        if udp_num_packets_i == NUM_PACKETS:
            udp_num_packets_i = 0
    else:
        udp_data[udp_num_packets_i] = np.zeros(MESSAGE_SIZE)
        udp_data_len[udp_num_packets_i] = 0
except posix_ipc.BusyError:
    pass
