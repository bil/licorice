serial_out[:] = np.zeros(shape=50, dtype="uint8")

query_string = np.array(bytearray("TX 1000\r", encoding="utf-8"), dtype="uint8")
query_string_len = len(query_string)
query_string_null = np.zeros(shape=query_string_len, dtype="uint8")
