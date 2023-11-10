#include <stdint.h>

#define __GNU_SOURCE

#ifndef _RUNNER_UTILS_
#define _RUNNER_UTILS_

typedef struct times_t {
  int64_t tick;
  uint64_t monotonic_raw;
  uint64_t monotonic;
  uint64_t realtime;
} times_t;

#endif
