from libc.stdint cimport int64_t, uint64_t


cdef extern from "runner_utils.h" nogil:
  cdef struct times_t:
    int64_t tick
    uint64_t monotonic_raw
    uint64_t monotonic
    uint64_t realtime
