try:
  sem.acquire(timeout = 0)
  udp_data_len = udp_in_len
  udp_data[np.nonzero(udp_in_len)] = udp_in[np.nonzero(udp_in_len)]
  udp_in_len[:] = bytearray(len(udp_in_len))
  sem.release()
except posix_ipc.BusyError:
  pass
