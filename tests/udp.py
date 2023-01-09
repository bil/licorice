import re
import socket


def udp_server_recv(port, timeout=60.0):
    family_addr = socket.AF_INET
    sock = socket.socket(family_addr, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(timeout)
    data = None

    try:
        sock.bind(("", port))
    except socket.error as e:
        print("Bind failed:{}".format(e))
        sock.close()
        raise

    try:
        data, addr = sock.recvfrom(1024)
        print(addr)
        if not data:
            sock.close()
            return
        data = data.decode()
        print("Reply[" + addr[0] + ":" + str(addr[1]) + "] - " + data)
        reply = "OK"
        sock.sendto(reply.encode(), addr)
    except socket.error as e:
        print("Running server failed:{}".format(e))
        sock.close()
        raise

    sock.close()

    regex = re.compile(
        r"Mean: (\d*[.]\d*), StdDev: (\d*[.]\d*), "
        r"Min: (\d*[.]\d*), Max: (\d*[.]\d*)"
    )
    m = regex.search(data)
    return [float(x) for x in m.groups()]
