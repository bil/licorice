#include <semaphore.h>
#include <stdint.h>
#include <signal.h>
#include <stdlib.h>

#define __GNU_SOURCE

#ifndef _UTILITY_FUNCTIONS_
#define _UTILITY_FUNCTIONS_ 

/*
 * initialize utilities
 * set function to run on exit
 */ 
void init_utils(void (*pHandleExit)(int exitStatus), sigset_t *pExitMask);

/* 
 * finish necessary real-time setup before process execution begins
 */
void make_realtime();

/*
 * run the function specified by exit_handler and print the given error message
 */
void die(char *errorStr);

/* 
 * create a signal handler that handles signal signum and runs the function *psh
 * when signum is raised
 */
void set_sighandler(int signum, void *psh, sigset_t *block_mask);

/*
 * open a shared memory block with:
 * name: pName
 * size: numPages * PAGESIZE
 * shm_open flags: shm_flags
 * mmap flags: mmap_flags
 * *ppmem then points to the beginning of this block of memory once the function has run
 * 
 * If the file descriptor needs to be ftruncated (i.e., this is the first process opening)
 * this shared memory, then make sure the O_CREAT flag is set in shm_flags
 */
void open_shared_mem(uint8_t **ppmem, const char *pName, size_t numBytes, int shm_flags, int mmap_flags);

/*
 * open a semaphore with:
 * name:pName
 * value: value
 *
 * Tries creating a semaphore with O_EXCL, but falls back to just O_CREAT and issues
 * a warning if that fails.
 */
sem_t *create_semaphore(const char *pName, int value);

#endif
