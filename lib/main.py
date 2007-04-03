'''Game main module.

Contains the entry point used by the run_game.py script.

Feel free to put all your game code here, or in other modules in this "lib"
directory.
'''

import random
import pygame
import display
import player
import sprite
import level
import euclid
import sys

def add_a_balloon(guy, lvl):
    new = sprite.Balloon(lvl)
    new.position = guy.position + euclid.Vector2(random.randrange(250.0, 450.0), random.randrange(0.0, 150.0))
    display.sprite_list.append(new)

def main():
    lvl = level.load_level("t001")
    print lvl

    stick_guy      = player.Player(lvl)
    display.player = stick_guy
    display.level  = lvl
    
    display.sprite_list.append(stick_guy)
   
    for i in xrange(0,20):
        add_a_balloon(stick_guy, lvl)

    
    timer = pygame.time.Clock()

    while 1:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                sys.exit(0)
                
            if e.type == pygame.KEYUP:
                if e.key == pygame.K_UP:
                    stick_guy.add_balloon()
                if e.key == pygame.K_DOWN:
                    stick_guy.rem_balloon()
                           
        keys = pygame.key.get_pressed()
        
        if (keys[pygame.K_LEFT]):
            stick_guy.move_left()

        if (keys[pygame.K_RIGHT]):
            stick_guy.move_right()

        elapsed = timer.tick() / 1000.0
        
        display.update(elapsed)

