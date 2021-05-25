import SharedArray
import posix_ipc
import numpy as np

SA_PATH = "shm://io.udp_data"

SA_PATH = "shm://io.udp_data"
SA_PATH_LEN = "shm://io.udp_data.len"
SEM_NAME = "/udp_data.sem"

udp_in = SharedArray.attach(SA_PATH)
udp_in_len = SharedArray.attach(SA_PATH_LEN)
sem = posix_ipc.Semaphore(name = SEM_NAME)
