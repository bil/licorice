import math

import pygame
pygame.display.init()

class Circle(pygame.sprite.Sprite):

    def __init__(self, color, radius, pos):
        pygame.sprite.Sprite.__init__(self)
        self.radius = radius
        self.color = color

        self.image = pygame.Surface([radius * 2, radius * 2]).convert_alpha()
        self.draw()

        self.rect = self.image.get_rect()  
        self.rect.x, self.rect.y = pos

    def set_color(self, color):
        self.color = color
        self.draw()

    def get_pos(self):
        return (self.rect.x, self.rect.y)

    def set_pos(self, pos):
        self.rect.x, self.rect.y = pos

    def set_size(self, radius):
        cur_pos = self.rect.x, self.rect.y
        self.radius = radius
        self.image = pygame.Surface([self.radius * 2, self.radius * 2]).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = cur_pos
        self.draw()

    def draw(self):
        self.image.fill((0,0,0,0))
        pygame.draw.circle(self.image, self.color, (self.radius, self.radius), self.radius)

black = (0,0,0)
screen = pygame.display.set_mode((1280,1024))
screen.fill(black)

# used in both pygame_demo and cursor_track
color = [200, 200, 0]
pos = [0, 0]
size = 30

# these variables only used for pygame demo
r = 200
theta = 0
offset = [500, 500]

vel_scale = 1

cir1 = Circle(color, size, pos)

sprites = pygame.sprite.Group(cir1)

refresh_rate = 15 # ticks (1 ms)
