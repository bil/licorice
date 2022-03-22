/* Use the newer ALSA API */
#define ALSA_PCM_NEW_HW_PARAMS_API
#include <alsa/asoundlib.h>
#include <stdbool.h>

#ifndef _LINE_UTILITIES_
#define _LINE_UTILITIES_ 

int pcm_init_cap();
int pcm_init_play();
void pcm_close_cap();
void pcm_close_play();

#endif