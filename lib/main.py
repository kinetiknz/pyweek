'''Game main module.

Contains the entry point used by the run_game.py script.

Feel free to put all your game code here, or in other modules in this "lib"
directory.
'''

import pygame
from pygame.locals import *
import player
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

    stick_guy  = player.Player(lvl)
    
    balloon = sprite.Balloon(lvl)
    balloon.position = stick_guy.position + euclid.Vector2(400.0, 150.0)
   
    timer = pygame.time.Clock()

    while 1:
        
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                sys.exit(0)
                
            if e.type == pygame.KEYUP:
                if e.key == K_UP:
                    stick_guy.add_balloon()
                if e.key == K_DOWN:
                    stick_guy.rem_balloon()
                           
        keys = pygame.key.get_pressed()
        
        if (keys[K_LEFT]):
            stick_guy.move_left()

        if (keys[K_RIGHT]):
            stick_guy.move_right()

        elapsed = timer.tick() / 1000.0
        
        balloon.move(elapsed)
        stick_guy.move(elapsed)
        stick_guy.animate(elapsed * 10.0)
        view[1] = -stick_guy.position[1] + 300        
                                      
        screen.fill(0)
        screen.blit(lvl.bg, view)
        stick_guy.render(screen, view)
        balloon.render(screen, view)
        pygame.display.flip()




