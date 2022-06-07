/* Use the newer ALSA API */
#define ALSA_PCM_NEW_HW_PARAMS_API
#include <alsa/asoundlib.h>
#include <stdbool.h>
#include <unistd.h>

#ifndef _LINE_UTILITIES_
#define _LINE_UTILITIES_ 

int pcm_init_capture(snd_pcm_t **pHandle, snd_pcm_hw_params_t *hwparams, snd_pcm_sw_params_t *swparams);
int pcm_init_playback(snd_pcm_t **pHandle, snd_pcm_hw_params_t *hwparams, snd_pcm_sw_params_t *swparams);
void pcm_close(snd_pcm_t *handle, int exitStatus);
int pcm_write_buffer(snd_pcm_t *handle, uint8_t *ptr, int cptr);
int pcm_read_buffer(snd_pcm_t *handle, uint8_t *ptr, int cptr);
snd_pcm_sframes_t pcm_get_period_size_bytes();

#endif
