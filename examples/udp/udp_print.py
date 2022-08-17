# print(udp_dataBufVars[8], udp_dataBufVars[9], flush=True)
if udp_dataBufVars[9] - udp_dataBufVars[8] > 0:
    data_arr = udp_dataRaw[udp_dataBufVars[8]:udp_dataBufVars[9]]
    num_messages = data_arr.shape[0]
    for i in range(num_messages):
        message = "".join([
            chr(c) for c in data_arr[i]
        ])
        print(message, flush=True)
