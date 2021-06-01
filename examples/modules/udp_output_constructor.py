import SharedArray
import posix_ipc
import numpy as np

SA_PATH = "shm://io.udp_data_pb"

SA_PATH = "shm://io.udp_data_pb"
SA_PATH_LEN = "shm://io.udp_data_len_pb"
SEM_NAME = "/udp_data.sem_pb"

udp_in = SharedArray.attach(SA_PATH)
udp_in_len = SharedArray.attach(SA_PATH_LEN)
sem = posix_ipc.Semaphore(name = SEM_NAME)
