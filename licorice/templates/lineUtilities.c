#include "lineUtilities.h"

#define SAMPLE_RATE 32000
#define NUM_CHANNELS 2
#define ACCESS_TYPE SND_PCM_ACCESS_RW_INTERLEAVED
//change if not using little endian system
#define FORMAT_TYPE SND_PCM_FORMAT_S16_LE
#define CAPTURE SND_PCM_STREAM_CAPTURE
#define PLAYBACK SND_PCM_STREAM_PLAYBACK
#define MODE_CAPTURE 0 //can be SND_PCM_NONBLOCK or SND_PCM_ASYNC
#define SOUND_CARD_NAME "default"
#define PERIOD_SIZE 8

static snd_pcm_hw_params_t *hw_params_capture;
snd_pcm_t *cap_handle;
snd_pcm_t *play_handle;

int pcm_init_cap() {
  int err;

  /* Open PCM device for recording (capture). */
  if((err = snd_pcm_open(&cap_handle, SOUND_CARD_NAME, CAPTURE, MODE_CAPTURE)) < 0) {
    fprintf(stderr, "cannot open audio device(%s)\n", snd_strerror(err));
    exit(1);
  }

  if((err = snd_pcm_hw_params_malloc(&hw_params_capture)) < 0) {
    fprintf(stderr, "cannot allocate hardware parameter structure(%s)\n", snd_strerror(err));
    exit(1);
  }

  if((err = snd_pcm_hw_params_any(cap_handle, hw_params_capture)) < 0) {
    fprintf(stderr, "cannot initialize hardware parameter structure(%s)\n", snd_strerror(err));
    exit(1);
  }

  if((err = snd_pcm_hw_params_set_access(cap_handle, hw_params_capture, ACCESS_TYPE)) < 0) {
    fprintf(stderr, "cannot set access type(%s)\n", snd_strerror(err));
    exit(1);
  }
  
  if((err = snd_pcm_hw_params_set_format(cap_handle, hw_params_capture, FORMAT_TYPE)) < 0) {
    fprintf(stderr, "cannot set sample format(%s)\n",
       snd_strerror(err));
    exit(1);
  }

  unsigned int rate = SAMPLE_RATE;
  int dir;
  rate = SAMPLE_RATE;
  if((err = snd_pcm_hw_params_set_rate_near(cap_handle, hw_params_capture, &rate, &dir)) < 0) {
    fprintf(stderr, "cannot set sample rate(%s)\n",
       snd_strerror(err));
    exit(1);
  }
  assert (rate == SAMPLE_RATE);
  printf("Actual ALSA sampling rate: %d dir=%d\n", rate, dir); 

  if((err = snd_pcm_hw_params_set_channels(cap_handle, hw_params_capture, NUM_CHANNELS)) < 0) {
    fprintf(stderr, "cannot set channel count(%s)\n",
       snd_strerror(err));
    exit(1);
  }

    /* Set period size to 8 frames. */
  snd_pcm_uframes_t frames = PERIOD_SIZE; 
  if((err = snd_pcm_hw_params_set_period_size_near(cap_handle, hw_params_capture, &frames, &dir)) < 0) {
    fprintf(stderr, "cannot set period size(%s)\n",
       snd_strerror(err));
    exit(1);
  }

  if((err = snd_pcm_hw_params(cap_handle, hw_params_capture)) < 0) {
    fprintf(stderr, "cannot set parameters(%s)\n",
       snd_strerror(err));
    exit(1);
  }

  snd_pcm_hw_params_free(hw_params_capture);

  return frames;
}

int pcm_init_play() {
  int err;

  /* Open PCM device for recording (capture). */
  if((err = snd_pcm_open(&play_handle, SOUND_CARD_NAME, PLAYBACK, MODE_CAPTURE)) < 0) {
    fprintf(stderr, "cannot open audio device(%s)\n", snd_strerror(err));
    exit(1);
  }

  if((err = snd_pcm_hw_params_malloc(&hw_params_capture)) < 0) {
    fprintf(stderr, "cannot allocate hardware parameter structure(%s)\n", snd_strerror(err));
    exit(1);
  }

  if((err = snd_pcm_hw_params_any(play_handle, hw_params_capture)) < 0) {
    fprintf(stderr, "cannot initialize hardware parameter structure(%s)\n", snd_strerror(err));
    exit(1);
  }

  if((err = snd_pcm_hw_params_set_access(play_handle, hw_params_capture, ACCESS_TYPE)) < 0) {
    fprintf(stderr, "cannot set access type(%s)\n", snd_strerror(err));
    exit(1);
  }
  
  if((err = snd_pcm_hw_params_set_format(play_handle, hw_params_capture, FORMAT_TYPE)) < 0) {
    fprintf(stderr, "cannot set sample format(%s)\n",
       snd_strerror(err));
    exit(1);
  }

  int dir; 
  unsigned int rate = SAMPLE_RATE;
  rate = SAMPLE_RATE;
  if((err = snd_pcm_hw_params_set_rate_near(play_handle, hw_params_capture, &rate, &dir)) < 0) {
    fprintf(stderr, "cannot set sample rate(%s)\n",
       snd_strerror(err));
    exit(1);
  }
  
  // assert (rate == SAMPLE_RATE);
  printf("Actual ALSA sampling rate: %d dir=%d\n", rate, dir);

  if((err = snd_pcm_hw_params_set_channels(play_handle, hw_params_capture, NUM_CHANNELS)) < 0) {
    fprintf(stderr, "cannot set channel count(%s)\n",
       snd_strerror(err));
    exit(1);
  }

  /* Set period size to 8 frames. */
  snd_pcm_uframes_t frames = PERIOD_SIZE; 
  if((err = snd_pcm_hw_params_set_period_size_near(play_handle, hw_params_capture, &frames, &dir)) < 0) {
    fprintf(stderr, "cannot set period size(%s)\n",
       snd_strerror(err));
    exit(1);
  }

  if((err = snd_pcm_hw_params(play_handle, hw_params_capture)) < 0) {
    fprintf(stderr, "cannot set parameters(%s)\n",
       snd_strerror(err));
    exit(1);
  }

  return frames;
}

void pcm_close_cap() {
  snd_pcm_close(cap_handle);
}

void pcm_close_play() {
  snd_pcm_close(play_handle);
}