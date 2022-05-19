import socket 
import numpy as np
import posix_ipc
import SharedArray
import time

MAX_NUM_PACKETS_PER_MS = 1

SA_PATH = "shm://io.udp_data"
SEM_NAME = "udp_data.sem"

MESSAGE_SIZE = 4
shm_size_src = MESSAGE_SIZE + 1
udp_source_raw = SharedArray.attach(SA_PATH)
sem = posix_ipc.Semaphore(name=SEM_NAME, flags=posix_ipc.O_CREAT)
sem.release()

valid_name = "shm://io.udp_valid"
udp_packet_valid = SharedArray.attach(valid_name)

def flush_udp():
	print("Inside udp flush")
	old_data = np.zeros(shape = (NUM_PACKETS, MESSAGE_SIZE), dtype = np.uint8)
	s.setblocking(0)
	bytes_recv = 1
	while bytes_recv > 0:
		try:
			print("clearing buffer\n")
			bytes_recv, addr = s.recvfrom_into(old_data, MESSAGE_SIZE)
		except socket.error as err:
			return

# Set up the udp connection (identifies interface and port number to connect to)
UDP_ADDR = 'localhost'
UDP_PORT = 51002
NUM_PACKETS = 5

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((UDP_ADDR, UDP_PORT))

flush_udp()

i = 0

#Receive buffer for udp data
buf = np.zeros(shape = (NUM_PACKETS, MESSAGE_SIZE), dtype = np.uint8)

ctr = 0
while True:
    print("NEW LOOP: ", ctr)
    ctr +=1 
    #set socket back to blocking
    s.setblocking(1)

    try:
        nbytes, clientAddr = s.recvfrom_into(buf[i, :], MESSAGE_SIZE)
    except:
        e = sys.exc_info()[0]
        print("e: ", e)
        raise

    if(nbytes > 1):
        sem.acquire()
        udp_packet_valid[i] = 1

        udp_source_raw[i][0] = nbytes 
        udp_source_raw[i][1:1+MESSAGE_SIZE] = buf[i][0:MESSAGE_SIZE] #must be named "{{module_name}}_raw"
        buf[i, 0:MESSAGE_SIZE] = np.zeros(shape=(1, MESSAGE_SIZE), dtype = np.uint8)
        print("".join([chr(int(x)) for x in udp_source_raw[i][1:5]]))
        print(udp_source_raw)
        sem.release()
        i += 1
    else:
        print("WAIT")
    if i == NUM_PACKETS:
        i = 0
    print(i)
s.close()
