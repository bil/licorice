matmul_out[:,:] = np.dot(m1, m2)[:,:]
# the [:,:] notation must be used otherwise Python will create a new matmul_out variable instead of copying the data into the array mapped by matmul_out
