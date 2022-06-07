# this constructor sets up pygame and initializes and defines the joystick

import pygame

pygame.display.init()
pygame.joystick.init()

if pygame.joystick.get_count() < 1:
    die("No joystick found!\n")

usb_joystick = pygame.joystick.Joystick(0)
usb_joystick.init()
num_buttons = usb_joystick.get_numbuttons()
