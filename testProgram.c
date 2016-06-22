#include <stdio.h>
#include <signal.h>
#include <sys/time.h>
#include <string.h>
#include <stdlib.h>
#include <sys/io.h>
#include <unistd.h>
#include <sched.h>
#include <sys/mman.h>

#define USECREQ 1000
#define SECREQ 0
#define PARA_PORT_BASE_ADDR 0x3000
#define PRIORITY 49
#define MAX_SAFE_STACK (8*1024)

static unsigned char outVal = 0;

void event_handler(int signum) {
  //printf("interrupt\n");
  outVal = ~outVal;
  outb(outVal,PARA_PORT_BASE_ADDR); 
}

void stack_prefault() {
  unsigned char dummy[MAX_SAFE_STACK];
  memset(dummy, 0, MAX_SAFE_STACK);
}
int main(int argc, char* argv[]) {
  if(ioperm(PARA_PORT_BASE_ADDR, 1, 1)) {
    printf("io permission denied\n");
    exit(1);
  }
  struct sched_param param;
  param.sched_priority = PRIORITY;
  if (sched_setscheduler(0, SCHED_FIFO, &param) == -1) {
    printf("sched_setscheduler failed\n");
    exit(1);
  }
  if(mlockall(MCL_CURRENT|MCL_FUTURE) == -1) {
    printf("lock error\n");
    exit(1);
  }
  stack_prefault();
  struct sigaction sa;
  struct itimerval timer;
  memset (&sa, 0, sizeof(sa));
  sa.sa_handler = &event_handler;
  sigaction(SIGALRM, &sa, NULL);
  timer.it_value.tv_sec = SECREQ;
  timer.it_value.tv_usec = USECREQ;
  timer.it_interval.tv_sec = SECREQ;
  timer.it_interval.tv_usec = USECREQ;
  setitimer(ITIMER_REAL, &timer, NULL);
  while(1) {
    pause();
  }
}
