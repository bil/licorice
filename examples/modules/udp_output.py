try:
  sem.acquire(timeout = 0)
  udp_data = udp_in
  print(udp_data)
  sem.release()
except posix_ipc.BusyError:
  pass
