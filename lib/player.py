import pygame
import euclid
import data
import sprite
from sprite import *

class Player(Sprite):
    
    def __init__(self, level):
        Sprite.__init__(self)
        self.level = level
        self.set_position(level.spawn)
        self.left = Sprite.load_images(self, data.filepath("player_l"))
        self.right = Sprite.load_images(self, data.filepath("player_r"))
        self.hang_left = Sprite.load_images(self, data.filepath("player_hang_l"))
        self.hang_right = Sprite.load_images(self, data.filepath("player_hang_r"))
        self.fall = Sprite.load_images(self, data.filepath("player_fall"))
        self.fall_left = Sprite.load_images(self, data.filepath("player_fall_l"))
        self.fall_right = Sprite.load_images(self, data.filepath("player_fall_r"))
        self.balloon_bunch = []
        self.balloon_bunch.append(Sprite.load_images(self, data.filepath("balloon")))
        self.balloon_bunch.append(Sprite.load_images(self, data.filepath("two_balloons")))
        self.balloon_bunch.append(Sprite.load_images(self, data.filepath("three_balloons")))
        self.set_anim_list(self.right)
        self.top_speed      = euclid.Vector2(200.0, 700.0)
        self.drag_factor    = 400.0
        self.balloon_count  = 0
        self.collide_speed  = 0.4
        self.last_dir       = 'l'
        self.collision_rect = self.fall[0].get_rect()
       
    def check_collision(self):
        rect = self.collision_rect.move( self.position[0] - (self.collision_rect.width/2),
                                         self.position[1] - (self.collision_rect.height) )
        return not self.level.area_is_bg(rect)
    
    def apply_balloon_force(self):
        if (self.balloon_count == 0):
            self.accel[1] = 400.0 # gravity for freefall
        else:
            self.accel[1]    = 0.0 # no gravity
            self.velocity[1] = (self.balloon_count - 2) * -60.0

    def render(self, dest_surface, view):
        if (self.balloon_count > 0):
             bunch_index = self.balloon_count-1
             if (bunch_index >= len(self.balloon_bunch)):
                 bunch_index = -1
             img    = self.balloon_bunch[bunch_index][0]
             my_img = self.anim_list[int(self.anim_frame)]
             rect   = img.get_rect()
             rect.move_ip(self.position[0], self.position[1])
             rect.move_ip(view[0], view[1])
             rect.move_ip(-(rect.width/2), -rect.height-my_img.get_rect().height)
             dest_surface.blit( img, rect )
            
        Sprite.render(self, dest_surface, view)

    def rem_balloon(self):
        self.balloon_count -= 1
        if (self.balloon_count < 0):
            self.balloon_count = 0
        
    def add_balloon(self):
        self.balloon_count += 1
        
    def move_left(self):
        self.accel[0] = -800.0
        
    def move_right(self):
        self.accel[0] = 800.0

    def move(self, elapsed_time):
        self.apply_balloon_force()
        Sprite.move(self, elapsed_time)
        self.pick_anim_list()
        
        # null out any horizontal acceleration from keypress
        # now that we've moved the player.
        self.accel[0] = 0.0
        
        Sprite.animate(self, elapsed_time * 10.0)
        
    def pick_anim_list(self):
        if (self.balloon_count == 0 and self.on_ground and self.accel[0] == 0.0):
            self.anim_frame = 0
            
        if (self.balloon_count == 0):
            if (self.on_ground):
                l = self.left
                r = self.right
                d = None
            else:
                l = self.fall_left
                r = self.fall_right
                d = self.fall
        else:
            l = self.hang_left
            r = self.hang_right
            d = None
        
        if (self.accel[0] == 0.0):
            if d:
                self.anim_list = d
            else:
                if self.last_dir == 'l':
                    self.anim_list = l
                else:
                    self.anim_list = r
        elif (self.accel[0] < 0.0):                
            self.anim_list = l
            self.last_dir  = 'l'
        else:
            self.anim_list = r
            self.last_dir  = 'r'

                              
    
            
            