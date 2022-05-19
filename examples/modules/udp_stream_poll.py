import socket 
import numpy as np
import posix_ipc
import SharedArray
import time
import asyncio

class EchoServerProtocol:
    def __init__(self, 
            MAX_NUM_PACKETS_PER_MS = 1, 
            SA_PATH="shm://io.udp_data", 
            MAX_MESSAGE_SIZE=10, 
            NUM_PACKETS = 1,
            SEM_NAME = "udp_data.sem",
            valid_name = "shm://io.udp_valid"):
        # super().__init()
        self.MAX_NUM_PACKETS_PER_MS = MAX_NUM_PACKETS_PER_MS

        # Bind to SharedArray
        self.SA_PATH = "shm://io.udp_data"
        self.MESSAGE_SIZE = self.MAX_MESSAGE_SIZE = MAX_MESSAGE_SIZE
        self.NUM_PACKETS = NUM_PACKETS
        self.shm_size_src = MAX_MESSAGE_SIZE + 1
        self.udp_source_raw = SharedArray.attach(SA_PATH)

        # Bind to semaphore
        self.SEM_NAME = SEM_NAME
        self.sem = posix_ipc.Semaphore(name=SEM_NAME, flags=posix_ipc.O_CREAT)
        self.sem.release()
        # Attach to valid bool
        self.valid_name = valid_name
        self.udp_packet_valid = SharedArray.attach(valid_name)

        self.i = 0

        # #Receive buffer for udp data
        # self.buf = np.zeros(shape = (NUM_PACKETS, MESSAGE_SIZE), dtype = np.uint8)

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        message = data.decode()
        nbytes = len(message)
        if nbytes > 1:
            messageInt = np.array([ord(c) for c in message])
            print('Received %r of length %d from %s' % (message, nbytes, addr))
            self.sem.acquire()
            self.udp_packet_valid[0] = 1
            self.udp_source_raw[self.i][0] = nbytes 
            messageLength = min(self.MESSAGE_SIZE, nbytes)
            # print(50, messageLength, messageInt, messageInt.shape, self.udp_source_raw[self.i, 1:1+messageLength].shape)
            self.udp_source_raw[self.i][1:1+messageLength] = messageInt[0:min(self.MESSAGE_SIZE, nbytes)]
            # print("".join([chr(int(x)) for x in self.udp_source_raw[self.i][1:min(1+self.MESSAGE_SIZE, 1 + nbytes)]]))
            # print(self.udp_source_raw)
            self.sem.release()
            self.i += 1
        else:
            print("No message received")
        if self.i == self.NUM_PACKETS:
            self.i = 0
        # print('Send %r to %s' % (message, addr))
        self.transport.sendto(data, addr)

print("Starting UDP server")

def main():
    # Get a reference to the event loop as we plan to use
    # low-level APIs.
    loop = asyncio.get_event_loop()

    # One protocol instance will be created to serve all client requests
    listen = loop.create_datagram_endpoint(
        EchoServerProtocol, local_addr=('127.0.0.1', 51002))
    transport, protocol = loop.run_until_complete(listen)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    transport.close()
    loop.close()

    # # One protocol instance will be created to serve all
    # # client requests.
    # # Set up the udp connection (identifies interface and port number to connect to)
    # transport, protocol = await loop.create_datagram_endpoint(
    #     lambda: EchoServerProtocol(),
    #     local_addr=('127.0.0.1', 51002))
        

    # try:
    #     await asyncio.sleep(3600)  # Serve for 1 hour.
    # finally:
    #     transport.close()

main()
