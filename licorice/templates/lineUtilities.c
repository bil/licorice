#include "lineUtilities.h"

#define PLAYBACK_DEVICE "default"
#define CAPTURE_DEVICE "default"
#define MODE 0 // SND_PCM_NONBLOCK // SND_PCM_ASYNC

#define ACCESS SND_PCM_ACCESS_RW_INTERLEAVED
#define FORMAT SND_PCM_FORMAT_S16
#define CHANNELS 2
#define RATE 44100

static unsigned int NPERIODS = 2;
static unsigned int buffer_time = 0;       /* ring buffer length in us */
static unsigned int period_time = 100000;       /* period time in us */

static snd_pcm_sframes_t buffer_size;
static snd_pcm_sframes_t period_size;

static snd_pcm_hw_params_t *hw_params_capture;
snd_pcm_t *cap_handle;

static int set_hwparams(snd_pcm_t *handle, snd_pcm_hw_params_t *params) {
  unsigned int rrate;
  int          err;
  snd_pcm_uframes_t     period_size_min;
  snd_pcm_uframes_t     period_size_max;
  snd_pcm_uframes_t     buffer_size_min;
  snd_pcm_uframes_t     buffer_size_max;

  /* choose all parameters */
  err = snd_pcm_hw_params_any(handle, params);
  if (err < 0) {
    fprintf(stderr, "Broken configuration: no configurations available: %s\n", snd_strerror(err));
    return err;
  }

  /* set the interleaved read/write format */
  err = snd_pcm_hw_params_set_access(handle, params, ACCESS);
  if (err < 0) {
    fprintf(stderr, "Access type not available: %s\n", snd_strerror(err));
    return err;
  }

  /* set the sample format */
  err = snd_pcm_hw_params_set_format(handle, params, FORMAT);
  if (err < 0) {
    fprintf(stderr, "Sample format not available: %s\n", snd_strerror(err));
    return err;
  }

  /* set the count of channels */
  err = snd_pcm_hw_params_set_channels(handle, params, CHANNELS);
  if (err < 0) {
    fprintf(stderr, "Channels count (%i) not availables: %s\n", CHANNELS, snd_strerror(err));
    return err;
  }

  /* set the stream rate */
  rrate = RATE;
  err = snd_pcm_hw_params_set_rate(handle, params, RATE, 0);
  if (err < 0) {
    fprintf(stderr, "Rate %iHz not available: %s\n", RATE, snd_strerror(err));
    return err;
  }

  if (rrate != RATE) {
    fprintf(stderr, "Rate doesn't match (requested %iHz, get %iHz, err %d)\n", RATE, rrate, err);
    return -EINVAL;
  }

  /* set the buffer time */
  err = snd_pcm_hw_params_get_buffer_size_min(params, &buffer_size_min);
  err = snd_pcm_hw_params_get_buffer_size_max(params, &buffer_size_max);
  err = snd_pcm_hw_params_get_period_size_min(params, &period_size_min, NULL);
  err = snd_pcm_hw_params_get_period_size_max(params, &period_size_max, NULL);
  printf("Buffer size range from %lu to %lu\n",buffer_size_min, buffer_size_max);
  printf("Period size range from %lu to %lu\n",period_size_min, period_size_max);
  if (period_time > 0) {
    printf("Requested period time %u us\n", period_time);
    err = snd_pcm_hw_params_set_period_time_near(handle, params, &period_time, NULL);
    if (err < 0) {
      fprintf(stderr, "Unable to set period time %u us: %s\n",
       period_time, snd_strerror(err));
      return err;
    }
  }
  if (buffer_time > 0) {
    printf("Requested buffer time %u us\n", buffer_time);
    err = snd_pcm_hw_params_set_buffer_time_near(handle, params, &buffer_time, NULL);
    if (err < 0) {
      fprintf(stderr, "Unable to set buffer time %u us: %s\n",
       buffer_time, snd_strerror(err));
      return err;
    }
  }
  if (! buffer_time && ! period_time) {
    buffer_size = buffer_size_max;
    if (! period_time)
      buffer_size = (buffer_size / NPERIODS) * NPERIODS;
    printf("Using max buffer size %lu\n", buffer_size);
    err = snd_pcm_hw_params_set_buffer_size_near(handle, params, &buffer_size);
    if (err < 0) {
      fprintf(stderr, "Unable to set buffer size %lu: %s\n",
       buffer_size, snd_strerror(err));
      return err;
    }
  }
  if (! buffer_time || ! period_time) {
    printf("Periods = %u\n", NPERIODS);
    err = snd_pcm_hw_params_set_periods_near(handle, params, &NPERIODS, NULL);
    if (err < 0) {
      fprintf(stderr, "Unable to set nperiods %u: %s\n",
       NPERIODS, snd_strerror(err));
      return err;
    }
  }

  /* write the parameters to device */
  err = snd_pcm_hw_params(handle, params);
  if (err < 0) {
    fprintf(stderr, "Unable to set hw params: %s\n", snd_strerror(err));
    return err;
  }

  snd_pcm_hw_params_get_buffer_size(params, &buffer_size);
  snd_pcm_hw_params_get_period_size(params, &period_size, NULL);
  printf("was set period_size = %lu\n",period_size);
  printf("was set buffer_size = %lu\n",buffer_size);
  if (2*period_size > buffer_size) {
    fprintf(stderr, "buffer to small, could not use\n");
    return -EINVAL;
  }
  fflush(stdout);
  return 0;
}

static int set_swparams(snd_pcm_t *handle, snd_pcm_sw_params_t *swparams) {
  int err;

  /* get the current swparams */
  err = snd_pcm_sw_params_current(handle, swparams);
  if (err < 0) {
    fprintf(stderr, "Unable to determine current swparams: %s\n", snd_strerror(err));
    return err;
  }

  /* start the transfer when a buffer is full */
  err = snd_pcm_sw_params_set_start_threshold(handle, swparams, buffer_size);
  if (err < 0) {
    fprintf(stderr, "Unable to set start threshold mode: %s\n", snd_strerror(err));
    return err;
  }

  /* allow the transfer when at least period_size frames can be processed */
  err = snd_pcm_sw_params_set_avail_min(handle, swparams, period_size);
  if (err < 0) {
    fprintf(stderr, "Unable to set avail min: %s\n", snd_strerror(err));
    return err;
  }

  /* write the parameters to the playback device */
  err = snd_pcm_sw_params(handle, swparams);
  if (err < 0) {
    fprintf(stderr, "Unable to set sw params: %s\n", snd_strerror(err));
    return err;
  }

  return 0;
}

int pcm_init_capture(snd_pcm_t **pHandle, snd_pcm_hw_params_t *hwparams, snd_pcm_sw_params_t *swparams) {
  int err;
  if ((err = snd_pcm_open(pHandle, CAPTURE_DEVICE, SND_PCM_STREAM_CAPTURE, MODE)) < 0) {
    printf("Playback open error: %s\n", snd_strerror(err));
    return 0;
  }

  if ((err = set_hwparams(*pHandle, hwparams)) < 0) {
    printf("Setting of hwparams failed: %s\n", snd_strerror(err));
    exit(EXIT_FAILURE);
  }
  if ((err = set_swparams(*pHandle, swparams)) < 0) {
    printf("Setting of swparams failed: %s\n", snd_strerror(err));
    exit(EXIT_FAILURE);
  }
}

int pcm_init_playback(snd_pcm_t **pHandle, snd_pcm_hw_params_t *hwparams, snd_pcm_sw_params_t *swparams) {
  int err;
  if ((err = snd_pcm_open(pHandle, PLAYBACK_DEVICE, SND_PCM_STREAM_PLAYBACK, MODE)) < 0) {
    printf("Playback open error: %s\n", snd_strerror(err));
    return 0;
  }

  if ((err = set_hwparams(*pHandle, hwparams)) < 0) {
      printf("Setting of hwparams failed: %s\n", snd_strerror(err));
      exit(EXIT_FAILURE);
  }
  if ((err = set_swparams(*pHandle, swparams)) < 0) {
      printf("Setting of swparams failed: %s\n", snd_strerror(err));
      exit(EXIT_FAILURE);
  }
}

void pcm_close(snd_pcm_t *handle, int exitStatus) {
  int err;
  if (exitStatus) {
    err = snd_pcm_drop(handle);
  }
  else {
    err = snd_pcm_drain(handle);
  }
  if (err < 0) printf("snd_pcm_drain failed: %s\n", snd_strerror(err));    
  snd_pcm_close(handle);
}

static int xrun_recovery(snd_pcm_t *handle, int err) {
  if (err == -EPIPE) {    /* under-run */
    err = snd_pcm_prepare(handle);
    if (err < 0)
        printf("Can't recovery from underrun, prepare failed: %s\n", snd_strerror(err));
    return 0;
  } else if (err == -ESTRPIPE) {
    while ( (err = snd_pcm_resume(handle)) == -EAGAIN)
      sleep(1);   /* wait until the suspend flag is released */
    if (err < 0) {
      err = snd_pcm_prepare(handle);
      if (err < 0)
        printf("Can't recovery from suspend, prepare failed: %s\n", snd_strerror(err));
    }
    return 0;
  }
  return err;
}

int pcm_write_buffer(snd_pcm_t *handle, uint8_t *ptr, int cptr) {
  int err;

  while (cptr > 0) {
    err = snd_pcm_writei(handle, ptr, cptr);
    if (err == -EAGAIN)
      continue;

    if (err < 0) {
      fprintf(stderr, "Write error: %d,%s\n", err, snd_strerror(err));
      if (xrun_recovery(handle, err) < 0) {
        fprintf(stderr, "xrun_recovery failed: %d,%s\n", err, snd_strerror(err));
        return -1;
      }
      break;  /* skip one period */
    }

    ptr += snd_pcm_frames_to_bytes(handle, err);
    cptr -= err;
  }
  return 0;
}

snd_pcm_sframes_t pcm_get_period_size_bytes() {
  return snd_pcm_format_size(FORMAT, period_size * CHANNELS);
}


int pcm_read_buffer(snd_pcm_t *handle, uint8_t *ptr, int cptr) {
  int err;

  while (cptr > 0) {
    err = snd_pcm_readi(handle, ptr, cptr);
    if (err == -EAGAIN)
      continue;

    if (err < 0) {
      fprintf(stderr, "Read error: %d,%s\n", err, snd_strerror(err));
      if (xrun_recovery(handle, err) < 0) {
        fprintf(stderr, "xrun_recovery failed: %d,%s\n", err, snd_strerror(err));
        return -1;
      }
      break;  /* skip one period */
    }

    ptr += snd_pcm_frames_to_bytes(handle, err);
    cptr -= err;
  }
  return 0;
}
