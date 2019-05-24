#Flush udp buffer before we begin reading the data
def flush_udp():
	print("Inside udp flush")
	old_data = np.zeros(shape = (1,PACKET_SIZE), dtype = np.uint8)
	s.setblocking(0)
	bytes_recv = 1
	while bytes_recv > 0:
		try:
			print("clearing buffer\n")
			bytes_recv, addr = s.recvfrom_into(old_data,PACKET_SIZE)
		except socket.error as err:
			return 

# Set up the udp connection (identifies interface and port number to connect to)
UDP_ADDR = '192.168.137.255'
UDP_PORT = 51002

#TODO: Do error checking here about connecting to the socket/if it succeeds
#TODO: check for dropped packets
#soccket must be names as s
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((UDP_ADDR, UDP_PORT))

#clear udp kerel buffer of old_data
flush_udp()

#set socket back to blocking
s.setblocking(1)