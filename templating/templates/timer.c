#define _GNU_SOURCE
#include <stdio.h>
#include <signal.h>
#include <sys/time.h>
#include <string.h>
#include <stdlib.h>
#include <sys/io.h>
#include <unistd.h>
#include <sched.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <fcntl.h>
#include <errno.h>
#include <stdbool.h>
#include <sys/types.h>
#include <stdint.h>
#include <semaphore.h>
#include <sys/wait.h>
#include <stdatomic.h>
#include "constants.h"
#include "utilityFunctions.h"

// CSV file that dictates which processes run during the millisecond
// Format of csv is: one row of comma separated values for each 
// 'round' of computation processes. Each value in a row corresponds
// to the name of the process that will run in that 'round'. The same 
// process can be specified multiple times in the same row and across rows.
#define RUNORDER_FILE "runOrder.csv"
// buffer length used for reading in processes from runOrder.csv
#define BUF_LEN 1024

// process IDs for each child by round
// ch_pid[1][2] refers to the pid of the third child process in the second round
static pid_t ch_pid[MAX_NUM_ROUNDS][MAX_NUM_CHILDREN];
// network pid
static pid_t n_pid;
// logger pid
static pid_t l_pid;
//
static unsigned char outVal = 0;
// pointer to start of shared memory containing group timestamp and waveform data
static uint8_t *pmem;
static uint8_t *pFinish;
sigset_t exitMask;
static sigset_t alrmMask;
static unsigned long alrmNum = 0;
static uint32_t *pMSStart;
static uint32_t *pMSEnd;
static uint32_t *pDataStart;
static uint32_t *pDataEnd;
static sem_t *pSem;
static sem_t *pSignalSems;
static int numChildren[MAX_NUM_ROUNDS];
static int numRounds;
static bool networkCreated = false;

void handle_exit(int exitStatus) {
  sigprocmask(SIG_BLOCK, &exitMask, NULL);
  printf("Killing child processes...\n");
  // send SIGINT to all child processes and wait
  for (int i = 0; i < numRounds; i++) {
    for(int j = 0; j < numChildren[i]; j++) {
      if (ch_pid[i][j] != -1) {
        kill(ch_pid[i][j], SIGINT);
         while (waitpid(ch_pid[i][j], 0, WNOHANG) > 0);
      }
    }
  }
  // send SIGINT to logger process and wait
  if (l_pid != -1) {
    kill(l_pid, SIGINT);
    while (waitpid(l_pid, 0, WNOHANG) > 0);
  }
  // send SIGINT to network process and wait
  if (n_pid != -1) {
    kill(n_pid, SIGINT);
    while (waitpid(n_pid, 0, WNOHANG) > 0);
  }
  printf("Unmapping shared memory...\n");
  printf("%lu SIGALRMs sent\n", alrmNum);
  // close shared memory
  munmap(pmem, PAGESIZE);
  shm_unlink(SMEM0_PATHNAME);
  munlockall();
  exit(exitStatus);
}

void set_sched_prior(int priority) {
  struct sched_param param;
  param.sched_priority = priority;
  if (sched_setscheduler(0, SCHED_FIFO, &param) == -1) {
    die("sched_setscheduler failed.\n");
  }
}

// Handle SIGALRM on millisecond
void event_handler(int signum) {
  sigprocmask(SIG_BLOCK, &alrmMask, NULL);

  // flip bits and output to parallel port
  outVal = ~outVal;
  outb(outVal,PARA_PORT_BASE_ADDR);

  // increment SIGALRM counter
  alrmNum++;

  // only trigger network process on first iterations
  if (alrmNum <= LATENCY) {
    kill(n_pid, SIGALRM);
  }
  else { // normal behavior on subsequent iterations
    // check if children have finished execution in allotted time
    for (int i = 0; i < numChildren[numRounds - 1]; i++) {
      if (pFinish[i]) {
        usleep(5000);
        // printf("i:%d pFinish[%d]: %d\n", i, i, pFinish[i]);
        die("Child timing violation\n");
      } 
      pFinish[i] = 0xff;
    }
    // check if logger has finished execution in allotted time
    if (pFinish[MAX_NUM_CHILDREN]) {
      printf("Logger timing violation on ms: %lu \n", alrmNum);
      //usleep(5000);
      //die("Logger timing violation.\n");
    }
    pFinish[MAX_NUM_CHILDREN] = 0xff;

    // update ms start and end pointers for children
    //***** added recently, not tested yet ********
    //might need a lock around this with fence, since this should
    //look atomic to children. could use pthread reader writer locks
    atomic_thread_fence(memory_order_seq_cst);
    *pMSStart = *pMSEnd;
    *pMSEnd = *pDataEnd;
    atomic_thread_fence(memory_order_release);
    // trigger network process
    kill(n_pid, SIGALRM);

    // trigger first round of child processes. block if network is updating spike wave data
    sem_wait(pSem);
    kill(l_pid, SIGALRM);
    for (int i = 0; i < numChildren[0]; i++) {
      kill(ch_pid[0][i], SIGALRM);
    }
    sem_post(pSem);
  }

  sigprocmask(SIG_UNBLOCK, &alrmMask, NULL);
}

void exit_handler(int signum) {
  printf("exiting...\n");
  handle_exit(0);
}

void usr1_handler(int signum) {
  printf("Child created.\n");
}

void usr2_handler(int signum) {
  if (networkCreated) {
    printf("Network process ready.\n");
  }
  else {
    printf("Network process created.\n");
    networkCreated = true;
  }
}

void chld_handler(int sig) {
  int saved_errno = errno;
  int dead_pid;
  while ((dead_pid = waitpid((pid_t)(-1), 0, WNOHANG)) > 0);
  printf("dead pid: %d \n", dead_pid);
  if (l_pid == dead_pid) {
    l_pid = -1;
  }
  else if (n_pid == dead_pid){
    n_pid = -1;
  }
  else {
    for (int i = 0; i < numRounds; i++) {
      for (int j = 0; j < numChildren[i]; j++) {
        if (ch_pid[i][j] == dead_pid) {
          ch_pid[i][j] = -1;
        }  
      }
    }
  }
  errno = saved_errno;
  die("I have lost a child :( \n");
}

void stack_prefault() {
  unsigned char dummy[MAX_SAFE_STACK];
  memset(dummy, 0, MAX_SAFE_STACK);
}

int main(int argc, char* argv[]) {
  // initialize utilityFunctions
  init_utils(&handle_exit);

  // make sure parport is writeable
  if (ioperm(PARA_PORT_BASE_ADDR, 1, 1)) {
    printf("io permission denied\n");
    exit(1);
  }

  // set signal masks
  sigemptyset(&exitMask);
  sigaddset(&exitMask, SIGALRM);  
  sigfillset(&alrmMask);
  sigdelset(&alrmMask, SIGINT);

  // set signal handlers
  set_sighandler(SIGINT, &exit_handler);
  set_sighandler(SIGALRM, &event_handler);
  set_sighandler(SIGUSR1, &usr1_handler);
  set_sighandler(SIGUSR2, &usr2_handler);
  set_sighandler(SIGCHLD, &chld_handler);
  printf("Handlers installed.\n");

  // create shared memory and map it
  printf("Mapping memory...\n");
  open_shared_mem(&pmem, SMEM0_PATHNAME, 1, O_TRUNC | O_CREAT | O_RDWR);
  // set pmem header variables
  pSem = (sem_t*)pmem;
  pMSStart = (uint32_t*)pmem + SMEM0_MS_START_OFFSET;
  pMSEnd = (uint32_t*)pmem + SMEM0_MS_END_OFFSET;
  pDataStart = (uint32_t*)pmem + SMEM0_DATA_START_OFFSET;
  pDataEnd = (uint32_t*)pmem + SMEM0_DATA_END_OFFSET;
  pFinish = pmem + SMEM0_HEADER_LEN;
  //Might need to change name of jinja variable
  open_shared_mem(&pSignalSems, SMEMSIG_PATHNAME, 1 
    + ({{numSIGS}} * sizeof (sem_t) - 1) / getpagesize() , O_TRUNC | O_CREAT | O_RDWR);
  printf("Memory mapped.\nForking children...\n");
  // zero'd out byte in shared memory corresponding to child in child process

  //initialize semaphore
  sem_init(pSem, 1, 1);

  // fork and exec network process
  if ((n_pid = fork()) == -1) {
    die("fork failed \n");
  }
  if (n_pid == 0) { // only runs for network process
    cpu_set_t mask;
    CPU_ZERO(&mask);
    CPU_SET(NETWORK_CPU, &mask);
    sched_setaffinity(0, sizeof(cpu_set_t), &mask);
    setpriority(PRIO_PROCESS, 0, -19);
    set_sched_prior(PRIORITY);
    char* argv[2] = {NETWORK_PROCNAME, NULL};
    
    // execute network process
    // signal handlers and mmap are not preserved on exec
    execvp(argv[0],argv);
    printf("network exec error. %s \n", strerror(errno));
    exit(1);
    //in case execvp fails
  }
  pause();

  // fork and exec data logger process
  if ((l_pid = fork()) == -1) {
    die("fork failed \n");
  }
  if (l_pid == 0) { // only runs for network process
    cpu_set_t mask;
    CPU_ZERO(&mask);
    CPU_SET(LOGGER_CPU, &mask);
    sched_setaffinity(0, sizeof(cpu_set_t), &mask);
    setpriority(PRIO_PROCESS, 0, -19);
    set_sched_prior(PRIORITY);
    char* argv[2] = {LOGGER_PROCNAME, NULL};
    
    // execute network process
    // signal handlers and mmap are not preserved on exec
    execvp(argv[0],argv);
    printf("logger exec error. %s \n", strerror(errno));
    exit(1);
    //in case execvp fails
  }
  pause();

  FILE *runOrder = fopen(RUNORDER_FILE, "r");
  char line[BUF_LEN];
  char *procName;
  char *pos;
  numRounds = 0;

  while (fgets(line, 1024, runOrder) != NULL) {
    if ((pos=strchr(line, '\n')) != NULL)
    *pos = '\0';

    numChildren[numRounds] = 0;    
    procName = strtok(line, ",");
    while(procName != NULL) {
      if (numChildren[numRounds] >= MAX_NUM_CHILDREN){
        die("Too many children\n");
      }
      if ((ch_pid[numRounds][numChildren[numRounds]] = fork()) == -1) {
        die("fork failed\n");
      }
      if (ch_pid[numRounds][numChildren[numRounds]] == 0) {  // only runs for child processes
        cpu_set_t mask;
        CPU_ZERO(&mask);
        CPU_SET(numChildren[numRounds] + CPU_OFFSET, &mask);
        sched_setaffinity(0, sizeof(cpu_set_t), &mask);
        setpriority(PRIO_PROCESS, 0, -19);
        set_sched_prior(PRIORITY);
        char buf[4];
        char procBuf[64];
        sprintf(buf, "%d",numChildren[numRounds]);
        sprintf(procBuf, "./%s", procName);
        char* argv[3] = {procBuf, buf, NULL};
        
        // execute child process
        // signal handlers and mmap are not preserved on exec
        execvp(argv[0],argv);
        printf("child exec error. %s \n", strerror(errno));
        exit(1);
        //in case execvp fails
      }
      pause();
    
      numChildren[numRounds]++;
      procName = strtok(NULL, ",");
    }
    numRounds++;
  }
  if (numRounds > MAX_NUM_ROUNDS) {
    die("Too many rounds");
  }
  printf("Child(ren) created.\n");

  // set up scheduler with priority
  set_sched_prior(PRIORITY);
  printf("Scheduler set.\n");

  // lock stack mem
  if (mlockall(MCL_CURRENT|MCL_FUTURE) == -1) {
    die("Lock error \n");
  }
  stack_prefault();
  printf("Memory locked and prefaulted.\n");

  kill(n_pid, SIGUSR2);
  pause();

  // set up timer
  printf("Setting up timer...\n");
  struct itimerval timer;
  timer.it_value.tv_sec = SECREQ;
  timer.it_value.tv_usec = USECREQ;
  timer.it_interval.tv_sec = SECREQ;
  timer.it_interval.tv_usec = USECREQ;
  //tell network to start gathering data.  First ms is therefore slightly longer than the rest.
  setitimer(ITIMER_REAL, &timer, NULL);
  while(1) {
    pause();
  }
}
