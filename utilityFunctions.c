#include "utilityFunctions.h"
#include <sys/mman.h>
#include <signal.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "constants.h"

extern sigset_t exitMask;
static void (*exit_handler)(int errorStr);

void init_utils(void (*pHandleExit)(int errorStr)) {
  exit_handler = pHandleExit;
}

void die(char *errorStr) {
  sigprocmask(SIG_BLOCK, &exitMask, NULL);
  perror(errorStr);
  exit_handler(1);
}

void set_sighandler(int signum, void *psh) {
  struct sigaction sa;
  memset(&sa, 0, sizeof(sa));
  sa.sa_handler = psh;
  sa.sa_flags = SA_RESTART;
  if (signum == SIGCHLD) {
    sa.sa_flags |= SA_NOCLDSTOP;
  }
  if (sigaction(signum, &sa, NULL) == -1) {
    die("sigaction failed \n");
  }
}

void open_shared_mem(uint8_t **ppmem, const char *pName, int numPages, int shm_flags) {
  int fd = shm_open(pName, shm_flags, 0600);
  if(fd == -1) {
    die("shm_open failed\n");
  }
  // check if O_CREAT (1 << 6) is set 
  if (shm_flags & O_CREAT) {
    if (ftruncate(fd, PAGESIZE * numPages)) {
      die("ftruncate failed.\n");
      exit(1);
    } 
  }
  *ppmem = (uint8_t*) mmap(NULL, PAGESIZE * numPages, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
  if (*ppmem == (void*)-1) {
    die("mmap failed\n");
  }
  close(fd);
}

