import os
import pygame

task_states = {
        'begin'     : 1,
        'active'    : 2,
        'hold'      : 3,
        'success'   : 4,
        'fail'      : 5,
        'end'       : 6 }

os.putenv('AUDIODRIVER', 'alsa')
#os.putenv('AUDIODEV', 

pygame.mixer.pre_init(buffer=512)
pygame.mixer.init()

sound_success = pygame.mixer.Sound('/tmp/audio/CEGC_success_glockenspiel.wav')
sound_fail = pygame.mixer.Sound('/tmp/audio/C#C_failure.wav')

state_prev = 0
