#include <stdint.h>

#ifndef _UTILITY_FUNCTIONS_
#define _UTILITY_FUNCTIONS_ 

/*
* initialize utilities
* set function to run on exit
*/ 
void init_utils(void (*pHandleExit)(int exitStatus));

/*
* run the function specified by exit_handler and print the given error message
*/
void die(char *errorStr);

/* 
* create a signal handler that handles signal signum and runs the function *psh
* when signum is raised
*/
void open_shared_mem(uint8_t **ppmem, const char *pName, int numPages, int shm_flags);

/*
* open a shared memory block with:
* name: pName
* size: numPages * PAGESIZE
* flags: shm_flags
* *ppmem then points to the beginning of this block of memory once the function has run
* 
* If the file descriptor needs to be ftruncated (i.e., this is the first process opening)
* this shared memory, then make sure the O_CREAT flag is set in shm_flags
*/
void set_sighandler(int signum, void *psh);

#endif