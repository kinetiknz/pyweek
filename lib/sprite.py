import pygame
from pygame.locals import *

import euclid
import data
import os

class Sprite(pygame.sprite.Sprite):

    def construct_filename(self, image_basename, frame_number):
        return image_basename + ("_%02d" % frame_number) + ".png"

    def load_images(self, image_basename, image_list):
        frame_num = 0;
        filename = self.construct_filename(image_basename, frame_num)
        
        while (os.path.exists(filename)):
            image_list.append(pygame.image.load(filename))
            image_list[-1].convert()
            frame_num += 1
            filename = self.construct_filename(image_basename, frame_num)

class Balloon(Sprite):
    pass

class Player(Sprite):
    
    def __init__(self):
        self.left = []
        Sprite.load_images(self, data.filepath("player_l"), self.left);
        self.right = []
        Sprite.load_images(self, data.filepath("player_r"), self.right);
        pass
    

'''Some silly code for development and testing.'''
if __name__ == "__main__":
    import sys
    import pygame
    import level
    from pygame.locals import *
    pygame.init()
    screen = pygame.display.set_mode([640, 480])

    lvl = level.load_level("t001")
    print lvl

    view = [20, -(lvl.bg_rect.h - 480), 600, 480]

    dir = -1

    player = Player()

    while 1:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                sys.exit(0)
        screen.fill(0)
        screen.blit(lvl.bg, view)
        pygame.display.flip()

