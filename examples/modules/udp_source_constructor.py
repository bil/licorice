import posix_ipc
import numpy as np
import SharedArray
import time

shm_name_src = 'io.udp_source'
shm_size_src = 4+1
# udp_shm_src = SharedArray.create(shm_name_src, shm_size_src)
udp_source_raw = SharedArray.attach(shm_name_src, shm_size_src)

sem_name_src = "udp_source.sem"
sem_src = posix_ipc.Semaphore(sem_name_src, posix_ipc.O_CREX)
sem_src.release() # first uptick to make the semaphore usable

udp_source = np.zeros((shm_size_src-1,1))

# UDP_ADDR = 'localhost'
# UDP_PORT = 51002

k = 1

# cdef int udp_num_packets_i = 1
