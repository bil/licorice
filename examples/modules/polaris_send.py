if not pNumTicks[0] % 5000 :
  serial_out[0 : query_string_len] = query_string
else:
  serial_out[0 : query_string_len] = query_string_null
