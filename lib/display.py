import pygame
import player
import sprite
import level

pygame.init()

width  = 640
height = 480

screen = pygame.display.set_mode([width, height])
view   = [20, 0, 600, 480]

sprite_list = []
player      = None
level       = None

def update(seconds_elapsed):
    global sprite_list
    new_sprite_list = []
        
    for s in sprite_list:
        s.move(seconds_elapsed)
        player.check_balloon(s)
        if not s.dead:
            new_sprite_list.append(s)
            
    new_sprite_list = sprite_list
    
    view[1] = -player.position[1] + 400        
                                      
    screen.fill(0)
    screen.blit(level.fg, view)
    
    for s in sprite_list:
        s.render(screen, view)
        
    pygame.display.flip()