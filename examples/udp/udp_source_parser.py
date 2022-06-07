# import time

# # udp_source_raw = SharedArray.attach(SA_PATH_SOURCE)
# MAX_NUM_PACKETS_PER_MS = 1
# PACKET_SIZE = 4
# # Receive buffer for udp data
# buf = np.zeros(shape = (PACKET_SIZE, MAX_NUM_PACKETS_PER_MS), dtype = np.uint8)

# k_num_packets_i = int(udp_source_raw[0])

# if (k >= MAX_NUM_PACKETS_PER_MS - 1): #was originally 11
#     k = 1
# else:
#     k = k+1

# try:
#     nbytes, clientAddr = s.recvfrom_into(buf, PACKET_SIZE)
# except:
#     e = sys.exc_info()[0]
#     print(e)
#     raise

# if(nbytes > 0):
#     sem_source.acquire() # locks
#     udp_shm_src[k] = buf #must be named "{{module_name}}_raw"
#     # udp_source_len[k] = nbytes
#     sem_source.release() # unlock
#     time.sleep(0.005)
