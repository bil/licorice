#include <stdint.h>

#ifndef _UTILITY_FUNCTIONS_
#define _UTILITY_FUNCTIONS_ 

void die(char *errorStr, void (*pHandleExit)());

void open_shared_mem(int *pfd, uint8_t **ppmem, const char *pName, int numPages, int shm_flags, void (*pHandleExit)());

void set_sighandler(int signum, void *psh);

#endif