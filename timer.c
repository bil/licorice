#include <stdio.h>
#include <signal.h>
#include <sys/time.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <sched.h>
#include <sys/mman.h>

#define USECREQ 1000
#define SECREQ 0
#define PRIORITY 49
pid_t ppid;

void event_handler  (int signum) {
 kill(ppid, SIGALRM);
}
int main(int argc, char* argv[]) {
  ppid = (int)atoi(argv[1]);
  printf("%d\n",ppid);
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
