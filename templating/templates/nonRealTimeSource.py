import numpy as np
import SharedArray
import socket
import netifaces
import posix_ipc 
import time
import signal
import os
import sys

def getipAddr():
	return netifaces.ifaddresses('enp7s1')[netifaces.AF_INET][0]['addr']

def getPort():
	return socket.htons(51002)

def killHandler(signum, frame):
	print("Inside Sigterm handler for non real time sources.\n")
	sem.unlink()	
	# SharedArray.delete(SA_PATH)
	# SharedArray.delete(SA_PATH_LEN)
	f.close()
	s.close()
	exit(0)

def flush_udp():
	print("Inside udp flush")
	old_data = np.zeros(shape = (1,1472), dtype = np.uint8)
	s.setblocking(0)
	bytes_recv = 1
	while bytes_recv > 0:
		try:
			print("clearing buffer\n")
			bytes_recv, addr = s.recvfrom_into(old_data,PACKET_SIZE)
		except socket.error as err:
			return 

#Set up signal handlers 
signal.signal(signal.SIGTERM, killHandler)

#Set up Shared Array Path and Semaphore path
SA_PATH = "shm://io.udp_data"
SA_PATH_LEN = "shm://io.udp_data.len"
SEM_NAME = "/udp_data.sem"


#Delete shared memory arrays if they already exist
created_mem = SharedArray.list()
if any(['io.udp_data' == x[0] for x in created_mem]):
	SharedArray.delete("io.udp_data")
if any(['io.udp_data.len' == x[0] for x in created_mem]):
	SharedArray.delete("io.udp_data.len")


udpLen = SharedArray.create(SA_PATH_LEN, shape = 12, dtype = np.uint8)
udpRaw = SharedArray.create(SA_PATH, shape = (6, 1472), dtype = np.uint8) #12 = 2*6 where 6 is the max number of ticks per ms
print("Created udpRaw\n")

sem = posix_ipc.Semaphore(name=SEM_NAME, flags = posix_ipc.O_CREX)
sem.release()

# Set up the udp connection
UDP_ADDR = '192.168.137.255'
UDP_PORT = 51002


#TODO: Do error checking here about connecting to the socket/if it succeeds
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((UDP_ADDR, UDP_PORT))

PACKET_SIZE = 1472 
k = -1

#clear udp kerel buffer of old_data
flush_udp()

#set socket back to blocking
s.setblocking(1)

#signal to parent that setup is done
os.kill(os.getppid(), signal.SIGUSR2)

#debugging file
f = open('udpDataTemp', 'w+b')

while True:
	#Receive buffer for udp data
	buf = np.zeros(shape = (1,1472), dtype = np.uint8)

	if (k >= 5): #was originally 11
		k = 0
	else:
		k = k+1

	try:
		# nbytes, clientAddr = s.recvfrom_into(udpRaw[k], PACKET_SIZE)
		nbytes, clientAddr = s.recvfrom_into(buf, PACKET_SIZE)
	except InterruptedError as e:
		print(e)
		raise

	if(nbytes > 0):
		sem.acquire()
		# udpLen[k] = nbytes
		udpRaw[k] = buf
	  	f.write(udpRaw[k])
		sem.release()
		time.sleep(0.005)




