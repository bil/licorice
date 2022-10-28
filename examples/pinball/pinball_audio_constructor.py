import os

import pygame

task_states = {
    "begin": 1,
    "active": 2,
    "hold": 3,
    "success": 4,
    "fail": 5,
    "end": 6,
}

# LICORICE_ROOT = os.environ['LICORICE_ROOT'] # this sadly doesn't work because the env isn't present when timer calls it
LICORICE_ROOT = "../../../.."  # this is fragile, need a better way to do this
AUDIO_PATH = "examples/media"
os.putenv("AUDIODRIVER", "alsa")
# os.putenv('AUDIODEV', 'plughw:0,1') # set this to the card,device to output sound to

pygame.mixer.pre_init(buffer=512)
pygame.mixer.init()

sound_success = pygame.mixer.Sound(
    os.path.join(LICORICE_ROOT, AUDIO_PATH, "CEGC_success_glockenspiel.wav")
)
sound_fail = pygame.mixer.Sound(
    os.path.join(LICORICE_ROOT, AUDIO_PATH, "C#C_failure.wav")
)

state_prev = 0
