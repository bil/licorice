#ifndef CLOCK_NANOSLEEP_H
#define CLOCK_NANOSLEEP_H

#define TIMER_ABSTIME 0x01

int clock_nanosleep(clockid_t clock_id, int flags,
        const struct timespec *rqtp, struct timespec *rmtp);

#endif
