cdef class SourceDriver():
    cdef size_t run(self, times_t *times, void *inBuf, size_t packetSize, object out_sigs) except *:
        raise NotImplementedError()

    cdef void exit_handler(self, int exitStatus) except *:
        raise NotImplementedError()
