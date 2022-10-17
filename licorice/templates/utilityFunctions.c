#include "utilityFunctions.h"
#include <fcntl.h>
#include <sched.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>
#include <errno.h>
#include "constants.h"

static sigset_t exitMask;
static void (*exit_handler)(int errorStr);


/* 
 * prefault stack to avoid faults during execution
 */
static void stack_prefault() {
  unsigned char dummy[MAX_SAFE_STACK];
  memset(dummy, 0, MAX_SAFE_STACK);
}

/*
 * initialize utilities
 * set function to run on exit
 */ 
void init_utils(void (*pHandleExit)(int errorStr), sigset_t *pExitMask) {
  exit_handler = pHandleExit;
  exitMask = *pExitMask;
}

/*
 * finish necessary real-time setup before process execution begins
 */
void make_realtime() {
  // lock stack mem
  if(mlockall(MCL_CURRENT|MCL_FUTURE) == -1) {
    die("NETWORK ERROR: memory lock error.\n");
  }
  stack_prefault();
}

/*
 * run the function specified by exit_handler and print the given error message
 */
void die(char *errorStr) {
// void die(const char *format, ...) {  
  sigprocmask(SIG_BLOCK, &exitMask, NULL);
/* can try to allow for printf-like argument as input
  va_list argptr;
  va_start(argptr, format);
  vfprintf(stderr, format, argptr);
  va_end(argptr);
*/  
  perror(errorStr);
  exit_handler(1);
}

/* 
 * create a signal handler that handles signal signum and runs the function *psh
 * when signum is raised
 */
void set_sighandler(int signum, void *psh, sigset_t *block_mask) {
  struct sigaction sa;
  memset(&sa, 0, sizeof(sa));
  sa.sa_handler = psh;
  if (block_mask)
    sa.sa_mask = *block_mask;
  sa.sa_flags = SA_RESTART;
  if (signum == SIGCHLD) {
    sa.sa_flags |= SA_NOCLDSTOP;
  }
  if (sigaction(signum, &sa, NULL) == -1) {
    die("sigaction failed \n");
  }
}

/*
* open a shared memory block with:
* name: pName
* size: numBytes
* flags: shm_flags
* *ppmem then points to the beginning of this block of memory once the function has run
* 
* If the file descriptor needs to be ftruncated (i.e., this is the first process opening)
* this shared memory, then make sure the O_CREAT flag is set in shm_flags
*/
void open_shared_mem(uint8_t **ppmem, const char *pName, size_t numBytes, int shm_flags, int mmap_flags) {
  int fd = shm_open(pName, shm_flags, 0666);
  if(fd == -1) {
    printf("%s\n", strerror(errno));
    fflush(stdout);
    die("shm_open failed.\n");
  }
  // check if O_CREAT (1 << 6) is set 
  if (shm_flags & O_CREAT) {
    if (ftruncate(fd, numBytes)) {
      die("ftruncate failed.\n");
    } 
  }
  *ppmem = (uint8_t*) mmap(NULL, numBytes, mmap_flags, MAP_SHARED, fd, 0);
  if (*ppmem == (void*)-1) {
    die("mmap failed\n");
  }
  close(fd);
}

sem_t *create_semaphore(const char *pName, int value) {
  sem_t *sem;
  // attempt opening semaphore with O_EXCL flag
  if ((sem = sem_open(pName, O_CREAT | O_EXCL, 0600, value)) == SEM_FAILED) {
    // issue warning if semaphore name already exists
    // TODO use proper warning (PyErr_WarnEx)
    printf(
      "Warning: semaphore name %s exists: %s \n", pName, strerror(errno)
    );

    if ((sem = sem_open(pName, O_CREAT, 0600, value)) == SEM_FAILED) {
      die("Error: could not open semaphore\n");
    }
  }
  return sem;
}

