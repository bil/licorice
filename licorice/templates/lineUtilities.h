/* Use the newer ALSA API */
#define ALSA_PCM_NEW_HW_PARAMS_API
#include <alsa/asoundlib.h>
#include <stdbool.h>
#include <unistd.h>

#ifndef _LINE_UTILITIES_
#define _LINE_UTILITIES_ 

typedef struct {
  const char *device;
  int mode;
  snd_pcm_access_t access;
  snd_pcm_format_t format;
  unsigned int channels;
  int rate;
  unsigned int buffer_time;
  unsigned int period_time;
  int periods;
  snd_pcm_sframes_t buffer_size;
  snd_pcm_sframes_t period_size;
} pcm_values_t;

int pcm_init_capture(
  snd_pcm_t **pHandle,
  snd_pcm_hw_params_t *hwparams,
  snd_pcm_sw_params_t *swparams,
  pcm_values_t *values
);
int pcm_init_playback(
  snd_pcm_t **pHandle,
  snd_pcm_hw_params_t *hwparams,
  snd_pcm_sw_params_t *swparams,
  pcm_values_t *values
);
void pcm_close(snd_pcm_t *handle, int exitStatus);
int pcm_write_buffer(snd_pcm_t *handle, uint8_t *ptr, int cptr);
int pcm_read_buffer(snd_pcm_t *handle, uint8_t *ptr, int cptr);
snd_pcm_sframes_t pcm_get_period_size_bytes(pcm_values_t *values);

#endif
