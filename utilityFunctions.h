#include <stdint.h>

#ifndef _UTILITY_FUNCTIONS_
#define _UTILITY_FUNCTIONS_ 

void init_utils(void (*pHandleExit)(int exitStatus));

void die(char *errorStr);

void open_shared_mem(uint8_t **ppmem, const char *pName, int numPages, int shm_flags);

void set_sighandler(int signum, void *psh);

#endif