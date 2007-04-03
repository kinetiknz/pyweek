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
        self.set_anim_list(self.right)
        self.top_speed     = euclid.Vector2(200.0, 700.0)
        self.drag_factor   = 400.0
        self.balloon_count = 0
        self.collide_speed = 0.4
        
    def check_collision(self):
       return not self.level.area_is_bg(self.get_rect())
    
    def apply_balloon_force(self):
        if (self.balloon_count == 0):
            self.accel[1] = 400.0 # gravity for freefall
        else:
            self.accel[1]    = 0.0 # no gravity
            self.velocity[1] = (self.balloon_count - 2) * -60.0

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
        
        if (self.accel[0] == 0.0):
            self.anim_frame = 0.0
        elif (self.accel[0] < 0.0):
            self.anim_list = self.left
        else:
            self.anim_list = self.right
        
        # null out any horizontal acceleration from keypress
        # now that we've moved the player.
        self.accel[0] = 0.0
            
            