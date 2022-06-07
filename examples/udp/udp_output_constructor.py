import posix_ipc
import numpy as np
import SharedArray
import time
import os
import asyncio

MESSAGE_SIZE = 4
NUM_PACKETS = 5

# Create SharedArray
SHM_NAME = "shm://io.udp_data"  # "shm://io.udp_data"
SHM_SIZE = (
    NUM_PACKETS,
    MESSAGE_SIZE + 1,
)  #'udp_data_len' #"shm://io.udp_data_len"

udp_source_raw = SharedArray.create(SHM_NAME, SHM_SIZE)

# Create semaphore
SEM_NAME = "udp_data.sem"
sem = posix_ipc.Semaphore(SEM_NAME, posix_ipc.O_CREX)  # (name = SEM_NAME)
# sem.release() # first uptick to make the semaphore usable -- IS THIS NECESSARY?

udp_data = np.zeros((NUM_PACKETS, MESSAGE_SIZE))

# Create valid bool
valid_name = "shm://io.udp_valid"
valid_size = NUM_PACKETS
udp_packet_valid = SharedArray.create(valid_name, valid_size)
for i in range(valid_size):
    udp_packet_valid[i] = 0
udp_num_packets = 0

cdef int udp_num_packets_i = 0#1
cdef int udp_num_bytes_i = 0#1

# i = 0
