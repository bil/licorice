#include "utilityFunctions.h"
#include <sys/mman.h>
#include <signal.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include "constants.h"

extern sigset_t exitMask;

void die(char *errorStr, void (*pHandleExit)()) {
  sigprocmask(SIG_BLOCK, &exitMask, NULL);
  perror(errorStr);
  pHandleExit();
  exit(1);
}

void open_shared_mem(int *pfd, uint8_t **ppmem, const char *pName, int numPages, int shm_flags, void (*pHandleExit)()) {
  *pfd = shm_open(pName, shm_flags, 0600);
  if(*pfd == -1) {
    die("shm_open failed\n", pHandleExit);
  }
  // check if O_CREAT (1 << 6) is set 
  if (shm_flags & O_CREAT) {
    if (ftruncate(*pfd, PAGESIZE * numPages)) {
      die("ftruncate failed.\n", pHandleExit);
      exit(1);
    } 
  }
  *ppmem = (uint8_t*) mmap(NULL, PAGESIZE * numPages, PROT_READ | PROT_WRITE, MAP_SHARED, *pfd, 0);
  if (*ppmem == (void*)-1) {
    die("mmap failed\n", pHandleExit);
  }
}

