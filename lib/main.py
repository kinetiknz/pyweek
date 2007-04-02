'''Game main module.

Contains the entry point used by the run_game.py script.

Feel free to put all your game code here, or in other modules in this "lib"
directory.
'''

import pygame
from pygame.locals import *
import sprite
import level
import euclid
import sys

def main():
    pygame.init()
    screen = pygame.display.set_mode([640, 480])

    lvl = level.load_level("t001")
    print lvl

    view = [20, -(lvl.bg_rect.h - 480), 600, 480]

    player = sprite.Player(lvl)
   
    timer = pygame.time.Clock()

    while 1:
        
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                sys.exit(0)
                
            if e.type == pygame.KEYUP:
                if e.key == K_SPACE:
                    player.add_balloon()
        
        keys = pygame.key.get_pressed()
        
        if (keys[K_LEFT]):
            player.move_left()

        if (keys[K_RIGHT]):
            player.move_right()
                      
        screen.fill(0)
        screen.blit(lvl.bg, view)

        elapsed = timer.tick()
        
        player.move(elapsed / 1000.0)
        player.animate(elapsed / 100.0)
        player.render(screen, view)
        pygame.display.flip()
        view[1] = -player.position[1] + 300



