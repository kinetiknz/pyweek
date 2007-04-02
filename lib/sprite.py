import pygame

import euclid
import data
import os

class Sprite(pygame.sprite.Sprite):

    def __init__(self):
        self.anim_list = []
        self.anim_frame = -1
        self.position = (0,0)

    def set_anim_list(self, anim_list):
        self.anim_list = anim_list
        self.anim_frame = 0

    def construct_filename(self, image_basename, frame_number):
        return image_basename + ("_%02d" % frame_number) + ".png"

    def load_images(self, image_basename):
        list_to_return = []
        frame_num = 0;
        filename = self.construct_filename(image_basename, frame_num)
        
        while (os.path.exists(filename)):
            list_to_return.append(pygame.image.load(filename))
            list_to_return[-1].convert()
            frame_num += 1
            filename = self.construct_filename(image_basename, frame_num)
            
        return list_to_return
            
    def render(self, dest_surface, view):
        dest_surface.blit( self.anim_list[int(self.anim_frame)],
                           pygame.Rect(self.position[0] + view[0], self.position[1] + view[1], 0, 0) )

    def animate(self, amount):
        self.anim_frame = (self.anim_frame + amount) % len(self.anim_list)

class Balloon(Sprite):
    pass

class Player(Sprite):
    
    def __init__(self):
        self.left = Sprite.load_images(self, data.filepath("player_l"))
        self.right = Sprite.load_images(self, data.filepath("player_r"))
        self.set_anim_list(self.right)
    

'''Some silly code for development and testing.'''
if __name__ == "__main__":
    import sys
    import pygame
    import level
    pygame.init()
    screen = pygame.display.set_mode([640, 480])

    lvl = level.load_level("t001")
    print lvl

    view = [20, -(lvl.bg_rect.h - 480), 600, 480]

    player = Player()
    player.position = lvl.spawn

    while 1:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                sys.exit(0)
        screen.fill(0)
        screen.blit(lvl.bg, view)
        player.render(screen, view)
        player.animate(0.1)
        pygame.display.flip()

