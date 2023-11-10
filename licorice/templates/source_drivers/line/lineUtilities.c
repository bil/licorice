#include "lineUtilities.h"

static int set_hwparams(
  snd_pcm_t *handle, snd_pcm_hw_params_t *params, pcm_values_t *values
) {
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
  err = snd_pcm_hw_params_set_access(handle, params, values->access);
  if (err < 0) {
    fprintf(stderr, "Access type not available: %s\n", snd_strerror(err));
    return err;
  }

  /* set the sample format */
  err = snd_pcm_hw_params_set_format(handle, params, values->format);
  if (err < 0) {
    fprintf(stderr, "Sample format not available: %s\n", snd_strerror(err));
    return err;
  }

  /* set the count of channels */
  err = snd_pcm_hw_params_set_channels(handle, params, values->channels);
  if (err < 0) {
    fprintf(stderr, "Channels count (%i) not availables: %s\n", values->channels, snd_strerror(err));
    return err;
  }

  /* set the stream rate */
  rrate = values->rate;
  err = snd_pcm_hw_params_set_rate(handle, params, values->rate, 0);
  if (err < 0) {
    fprintf(stderr, "Rate %iHz not available: %s\n", values->rate, snd_strerror(err));
    return err;
  }

  if (rrate != values->rate) {
    fprintf(stderr, "Rate doesn't match (requested %iHz, get %iHz, err %d)\n", values->rate, rrate, err);
    return -EINVAL;
  }

  /* set the buffer time */
  err = snd_pcm_hw_params_get_buffer_size_min(params, &buffer_size_min);
  err = snd_pcm_hw_params_get_buffer_size_max(params, &buffer_size_max);
  err = snd_pcm_hw_params_get_period_size_min(params, &period_size_min, NULL);
  err = snd_pcm_hw_params_get_period_size_max(params, &period_size_max, NULL);
  printf("Buffer size range from %lu to %lu\n", buffer_size_min, buffer_size_max);
  printf("Period size range from %lu to %lu\n", period_size_min, period_size_max);
  if (values->period_time > 0) {
    printf("Requested period time %u us\n", values->period_time);
    err = snd_pcm_hw_params_set_period_time_near(handle, params, &values->period_time, NULL);
    if (err < 0) {
      fprintf(stderr, "Unable to set period time %u us: %s\n",
       values->period_time, snd_strerror(err));
      return err;
    }
  }
  if (values->buffer_time > 0) {
    printf("Requested buffer time %u us\n", values->buffer_time);
    err = snd_pcm_hw_params_set_buffer_time_near(handle, params, &values->buffer_time, NULL);
    if (err < 0) {
      fprintf(stderr, "Unable to set buffer time %u us: %s\n",
       values->buffer_time, snd_strerror(err));
      return err;
    }
  }
  if (! values->buffer_time && ! values->period_time) {
    values->buffer_size = buffer_size_max;
    if (! values->period_time)
      values->buffer_size = (values->buffer_size / values->periods) * values->periods;
    printf("Using max buffer size %lu\n", values->buffer_size);
    err = snd_pcm_hw_params_set_buffer_size_near(handle, params, &values->buffer_size);
    if (err < 0) {
      fprintf(stderr, "Unable to set buffer size %lu: %s\n",
       values->buffer_size, snd_strerror(err));
      return err;
    }
  }
  if (! values->buffer_time || ! values->period_time) {
    printf("Periods = %u\n", values->periods);
    err = snd_pcm_hw_params_set_periods_near(handle, params, &values->periods, NULL);
    if (err < 0) {
      fprintf(stderr, "Unable to set nperiods %u: %s\n",
       values->periods, snd_strerror(err));
      return err;
    }
  }

  /* write the parameters to device */
  err = snd_pcm_hw_params(handle, params);
  if (err < 0) {
    fprintf(stderr, "Unable to set hw params: %s\n", snd_strerror(err));
    return err;
  }

  snd_pcm_hw_params_get_buffer_size(params, &values->buffer_size);
  snd_pcm_hw_params_get_period_size(params, &values->period_size, NULL);
  printf("period_size set to: %lu\n",values->period_size);
  printf("buffer_size set to: %lu\n",values->buffer_size);
  if (2*values->period_size > values->buffer_size) {
    fprintf(stderr, "Buffer too small, could not use\n");
    return -EINVAL;
  }
  fflush(stdout);
  return 0;
}

static int set_swparams(
  snd_pcm_t *handle, snd_pcm_sw_params_t *swparams, pcm_values_t *values
) {
  int err;

  /* get the current swparams */
  err = snd_pcm_sw_params_current(handle, swparams);
  if (err < 0) {
    fprintf(stderr, "Unable to determine current swparams: %s\n", snd_strerror(err));
    return err;
  }

  /* start the transfer when a buffer is full */
  err = snd_pcm_sw_params_set_start_threshold(handle, swparams, values->buffer_size);
  if (err < 0) {
    fprintf(stderr, "Unable to set start threshold mode: %s\n", snd_strerror(err));
    return err;
  }

  /* allow the transfer when at least period_size frames can be processed */
  err = snd_pcm_sw_params_set_avail_min(handle, swparams, values->period_size);
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

int pcm_init_capture(
  snd_pcm_t **pHandle,
  snd_pcm_hw_params_t *hwparams,
  snd_pcm_sw_params_t *swparams,
  pcm_values_t *values
) {
  snd_pcm_hw_params_alloca(&hwparams);
  snd_pcm_sw_params_alloca(&swparams);

  int err;
  if ((err = snd_pcm_open(pHandle, values->device, SND_PCM_STREAM_CAPTURE, values->mode)) < 0) {
    printf("Playback open error: %s\n", snd_strerror(err));
    exit(EXIT_FAILURE);
  }

  if ((err = set_hwparams(*pHandle, hwparams, values)) < 0) {
    printf("Setting of hwparams failed: %s\n", snd_strerror(err));
    exit(EXIT_FAILURE);
  }
  if ((err = set_swparams(*pHandle, swparams, values)) < 0) {
    printf("Setting of swparams failed: %s\n", snd_strerror(err));
    exit(EXIT_FAILURE);
  }

  return 0;
}

int pcm_init_playback(
  snd_pcm_t **pHandle,
  snd_pcm_hw_params_t *hwparams,
  snd_pcm_sw_params_t *swparams,
  pcm_values_t *values
) {
  snd_pcm_hw_params_alloca(&hwparams);
  snd_pcm_sw_params_alloca(&swparams);

  int err;
  if ((err = snd_pcm_open(pHandle, values->device, SND_PCM_STREAM_PLAYBACK, values->mode)) < 0) {
    printf("Playback open error: %s\n", snd_strerror(err));
    exit(EXIT_FAILURE);
  }

  if ((err = set_hwparams(*pHandle, hwparams, values)) < 0) {
    printf("Setting of hwparams failed: %s\n", snd_strerror(err));
    exit(EXIT_FAILURE);
  }
  if ((err = set_swparams(*pHandle, swparams, values)) < 0) {
    printf("Setting of swparams failed: %s\n", snd_strerror(err));
    exit(EXIT_FAILURE);
  }
  return 0;
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
      if (err == -EPIPE)
        fprintf(stderr, "Underrun: ");
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
  return ptr;
}

snd_pcm_sframes_t pcm_get_period_size_bytes(pcm_values_t *values) {
  return snd_pcm_format_size(values->format, values->period_size * values->channels);
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
  return ptr;
}
