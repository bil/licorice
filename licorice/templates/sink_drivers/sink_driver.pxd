from runner_utils cimport times_t


cdef class SinkDriver():
    cdef void run(self, times_t *times, void *outBuf, size_t outBufLen, object in_sigs, object in_sig_lens) except *
    cdef void exit_handler(self, int exitStatus) except *
