import asyncio
import socket
import time

import numpy as np
import posix_ipc
import SharedArray

# # udpLen = SharedArray.create(SA_PATH_LEN, shape = 12, dtype = np.uint8)
# # udpRaw = SharedArray.create(SA_PATH, shape = (6, 1472), dtype = np.uint8) #12 = 2*6 where 6 is the max number of ticks per ms
# # print("Created udpRaw\n")

# udp_source_raw = SharedArray.attach(SA_PATH)

# sem = posix_ipc.Semaphore(name=SEM_NAME, flags = posix_ipc.O_CREX)
# valid_name = "shm://io.udp_valid"
# udp_packet_valid = SharedArray.attach(valid_name)
# # sem.release()

# # Set up the udp connection
UDP_ADDR = "127.0.0.1"
UDP_PORT = 51002


# #TODO: Do error checking here about connecting to the socket/if it succeeds
# s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# s.bind((UDP_ADDR, UDP_PORT))

# # PACKET_SIZE = 1472
# # k = -1

# #clear udp kerel buffer of old_data
# flush_udp()

# #set socket back to blocking
# s.setblocking(1)

# signal to parent that setup is done
os.kill(os.getppid(), signal.SIGUSR2)

# debugging file
f = open("udpDataTemp", "w+b")

# k = 0

# #Receive buffer for udp data
# buf = np.zeros(shape = (NUM_PACKETS, MESSAGE_SIZE), dtype = np.uint8)

# # while True:
# #     #Receive buffer for udp data
# #     buf = np.zeros(shape = (1,1472), dtype = np.uint8)

# #     if (k >= 5): #was originally 11
# #         k = 0
# #     else:
# #         k = k+1

# #     try:
# #         # nbytes, clientAddr = s.recvfrom_into(udpRaw[k], PACKET_SIZE)
# #         nbytes, clientAddr = s.recvfrom_into(buf, PACKET_SIZE)
# #     except InterruptedError as e:
# #         print(e)
# #         raise

# #     if(nbytes > 0):
# #         sem.acquire()
# #         # udpLen[k] = nbytes
# #         udpRaw[k] = buf
# #         f.write(udpRaw[k])
# #         sem.release()
# #         time.sleep(0.005)
# while True:
#     s.setblocking(1)

#     try:
#         nbytes, clientAddr = s.recvfrom_into(buf, MESSAGE_SIZE)
#         print(nbytes, clientAddr, buf)
#     except:
#         e = sys.exc_info()[0]
#         print(e)
#         raise

#     if(nbytes > 0):
#         sem.acquire()
#         udp_packet_valid[0] = 1

#         udp_source_raw[k][0] = nbytes
#         udp_source_raw[k][1:1+MESSAGE_SIZE] = buf[k][0:MESSAGE_SIZE]
#         buf[0:MESSAGE_SIZE] = np.zeros(shape=(1, MESSAGE_SIZE), dtype = np.uint8)
#         print(udp_source_raw)
#         sem.release()
#         time.sleep(0.005)

#     k += 1
#     if k == NUM_PACKETS:
#         k = 0

# s.close()#?DO I NEED THIS?


def getipAddr():
    return netifaces.ifaddresses("enp7s1")[netifaces.AF_INET][0]["addr"]


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


# Set up signal handlers
signal.signal(signal.SIGTERM, killHandler)

# Set up Shared Array Path and Semaphore path
MAX_NUM_PACKETS_PER_MS = (1,)
SHM_NAME = ("shm://io.udp_data",)
MAX_MESSAGE_SIZE = (10,)
NUM_PACKETS = (1,)
SEM_NAME = ("shm://udp_data.sem",)
valid_name = "shm://io.udp_valid"

# Delete shared memory arrays if they already exist
created_mem = SharedArray.list()
if any(["io.udp_data" == x[0] for x in created_mem]):
    SharedArray.delete("io.udp_data")
if any(["udp_data.sem" == x[0] for x in created_mem]):
    SharedArray.delete("udp_data.sem")
if any(["io.udp_valid" == x[0] for x in created_mem]):
    SharedArray.delete("io.udp_valid")


class EchoServerProtocol:
    def __init__(
        self,
        MAX_NUM_PACKETS_PER_MS=1,
        SHM_NAME="shm://io.udp_data",
        MAX_MESSAGE_SIZE=10,
        NUM_PACKETS=1,
        SEM_NAME="shm://udp_data.sem",
        valid_name="shm://io.udp_valid",
    ):
        # super().__init()
        self.MAX_NUM_PACKETS_PER_MS = MAX_NUM_PACKETS_PER_MS

        # Bind to SharedArray
        self.SHM_NAME = "shm://io.udp_data"
        self.MESSAGE_SIZE = self.MAX_MESSAGE_SIZE = MAX_MESSAGE_SIZE
        self.NUM_PACKETS = NUM_PACKETS
        self.shm_size_src = MAX_MESSAGE_SIZE + 1
        SHM_SIZE = (NUM_PACKETS, MESSAGE_SIZE + 1)
        self.udp_source_raw = SharedArray.attach(SHM_NAME)

        # Bind to semaphore
        self.SEM_NAME = SEM_NAME
        self.sem = posix_ipc.Semaphore(name=SEM_NAME, flags=posix_ipc.O_CREAT)
        self.sem.release()
        # Attach to valid bool
        self.valid_name = valid_name
        self.udp_packet_valid = SharedArray.attach(valid_name)

        self.k = 0

        # #Receive buffer for udp data
        # self.buf = np.zeros(shape = (NUM_PACKETS, MESSAGE_SIZE), dtype = np.uint8)

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        message = data.decode()
        nbytes = len(message)
        if nbytes > 1:
            messageInt = np.array([ord(c) for c in message])
            print("Received %r of length %d from %s" % (message, nbytes, addr))
            self.sem.acquire()
            self.udp_packet_valid[0] = 1
            self.udp_source_raw[self.k][0] = nbytes
            messageLength = min(self.MESSAGE_SIZE, nbytes)
            # print(50, messageLength, messageInt, messageInt.shape, self.udp_source_raw[self.k, 1:1+messageLength].shape)
            self.udp_source_raw[self.k][1 : 1 + messageLength] = messageInt[
                0 : min(self.MESSAGE_SIZE, nbytes)
            ]
            # print("".join([chr(int(x)) for x in self.udp_source_raw[self.k][1:min(1+self.MESSAGE_SIZE, 1 + nbytes)]]))
            # print(self.udp_source_raw)
            self.sem.release()
            self.k += 1
        else:
            print("No message received")
        if self.k == self.NUM_PACKETS:
            self.k = 0
        # print('Send %r to %s' % (message, addr))
        self.transport.sendto(data, addr)


print("Starting UDP server")

# Get a reference to the event loop as we plan to use
# low-level APIs.
loop = asyncio.get_event_loop()

# One protocol instance will be created to serve all client requests
listen = loop.create_datagram_endpoint(
    EchoServerProtocol, local_addr=("127.0.0.1", 51002)
)
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
