# update internal/persistent variables

if scalar <= 127:
    scalar += 1
else:
    scalar = -128

if vector_i[0] < 0:
    vector_i[:] += 5
else:
    vector_i[0] = -32767
    vector_i[1] = -20000
    vector_i[2] = -10000

if vector_f[0] < 1e9:
    vector_f[:] *= 2
else:
    vector_f[:] = [1, 2, 3, 4]

if matrix[0, 0] < 1e10:
    matrix *= 3
else:
    matrix[:, :] = [[1, 2], [3, 4]]


# write to outputs
scalar_out[:] = scalar
vector_ints[:] = vector_i
vector_floats[:] = vector_f
matrix_out[:, :] = matrix
