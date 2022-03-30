	#Receive buffer for udp data
	buf = np.zeros(shape = (1,PACKET_SIZE), dtype = np.uint8)

	if (k >= MAX_NUM_PACKETS_PER_MS - 1): #was originally 11
		k = 0
	else:
		k = k+1

	try:
		nbytes, clientAddr = s.recvfrom_into(buf, PACKET_SIZE)
		print(nbytes, clientAddr)
	except:
		e = sys.exc_info()[0]
		print(e)
		raise

	if(nbytes > 0):
		sem.acquire()
		udp_source_raw[k] = buf #must be named "{{module_name}}_raw"
		udp_source_len[k] = nbytes
		sem.release()
		time.sleep(0.005)
