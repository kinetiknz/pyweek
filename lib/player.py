import pygame
import euclid
import data
import sprite
from sprite import *

class Player(Sprite):
    
    def __init__(self, level, balloon_list):
        Sprite.__init__(self)
        self.level = level
        self.balloon_list = balloon_list
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
        self.balloon_bunch.append(Sprite.load_images(self, data.filepath("four_balloons")))
        self.balloon_bunch.append(Sprite.load_images(self, data.filepath("five_balloons")))
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
        bunch_rect = self.get_bunch_rect(self.get_bunch_img())
        if (bunch_rect):
            bunch_hit = self.level.check_area(bunch_rect)
            if bunch_hit == self.level.solid:
                return True
            elif bunch_hit == self.level.spike:
                self.pop_balloon()
            
        return self.level.check_area(rect) == self.level.solid
    
    def check_balloons(self, sprite_list):
        rect = self.get_hand_rect()
        for obj in sprite_list:
            if isinstance(obj, sprite.Balloon):
                if not obj.dead and not obj.popped and obj.get_rect().colliderect(rect):
                    obj.dead = True
                    self.add_balloon()
                
    def check_darts(self, sprite_list):
        rect = self.get_bunch_rect(self.get_bunch_img())
        if not rect:
            return
        
        for obj in sprite_list:
            if isinstance(obj, sprite.Dart):
                if not obj.dead and obj.get_rect().colliderect(rect):
                    obj.dead = True
                    self.pop_balloon()
        
    def apply_balloon_force(self):
        if (self.balloon_count == 0):
            self.accel[1] = 400.0 # gravity for freefall
        else:
            self.accel[1]    = 0.0 # no gravity
            self.velocity[1] = (self.balloon_count - 2) * -60.0

    def render(self, dest_surface, view):
        self.draw_balloon_bunch(dest_surface, view)
        Sprite.render(self, dest_surface, view)

    def draw_balloon_bunch(self, dest_surface, view):
        if (self.balloon_count > 0):
            img = self.get_bunch_img()
            rect = self.get_bunch_rect(img)
            rect.move_ip(view[0], view[1])
            dest_surface.blit( img, rect )        

    def get_bunch_img(self):
        if (self.balloon_count <= 0):
            return None
        
        bunch_index = self.balloon_count-1
        if (bunch_index >= len(self.balloon_bunch)):
                 bunch_index = -1
        return self.balloon_bunch[bunch_index][0]

    def get_bunch_rect(self, bunch_img):
        if (self.balloon_count <= 0):
            return None
        
        my_img = self.anim_list[int(self.anim_frame)]
        rect   = bunch_img.get_rect()
        rect.move_ip(self.position[0], self.position[1])
        rect.move_ip(-(rect.width/2), -rect.height-my_img.get_rect().height + 10)
        return rect    
        
    def get_hand_rect(self):
        rect = Sprite.get_rect(self)
        rect.height /= 2
        return rect

    def pop_balloon(self):
        if self.balloon_count > 0:
            new = Balloon(self.level)
            new.position = self.position + euclid.Vector2(0.0, -(self.get_rect().height * 0.9))
            new.pop()
            self.balloon_list.append(new)
            self.balloon_count -= 1
            
    def drop_balloon(self):
        if self.balloon_count > 0:
            self.balloon_count -= 1
            new = Balloon(self.level)
            new.position = self.position + euclid.Vector2(0.0, -(self.get_rect().height * 0.9))
            if self.last_dir == 'r':
                new.position[0] -= self.get_rect().width
            else:
                 new.position[0] += self.get_rect().width
            self.balloon_list.append(new)

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

                              
    
            
            