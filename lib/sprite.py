import pygame
import euclid
import data
import os

class Sprite(pygame.sprite.Sprite):

    def __init__(self):
        self.anim_list = []
        self.anim_frame = -1
        self.position      = euclid.Vector2(0.0, 0.0)
        self.velocity      = euclid.Vector2(0.0, 0.0)
        self.accel         = euclid.Vector2(0.0, 0.0)

    def set_anim_list(self, anim_list):
        self.anim_list = anim_list
        self.anim_frame = 0

    def construct_filename(self, image_basename, frame_number):
        return image_basename + ("_%02d" % frame_number) + ".png"
    
    def check_collision(self):
        return False

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
            
    def get_rect(self):
        rect = self.anim_list[int(self.anim_frame)].get_rect()
        rect.move_ip(self.position[0], self.position[1])
        return rect
    
    def render(self, dest_surface, view):
        dest_surface.blit( self.anim_list[int(self.anim_frame)],
                           pygame.Rect(self.position[0] + view[0], self.position[1] + view[1], 0, 0) )

    def animate(self, amount):
        self.anim_frame = (self.anim_frame + amount) % len(self.anim_list)
        
    def stop(self):
        self.velocity = euclid.Vector2(0.0, 0.0)
        self.accel    = euclid.Vector2(0.0, 0.0)
        
    def move(self, elapsed_time):
        old_velocity = self.velocity.copy()
        old_position = self.position.copy()
        
        # move x first
        self.velocity[0] += (self.accel[0] * elapsed_time)
        self.position[0] += (self.velocity[0] * elapsed_time)
        
        if self.check_collision():
            self.velocity[0] = old_velocity[0]
            self.position[0] = old_position[0]
        
        # move y now
        self.velocity[1] += (self.accel[1] * elapsed_time)
        self.position[1] += (self.velocity[1] * elapsed_time)
        
        if self.check_collision():
            self.velocity[1] = old_velocity[1]
            self.position[1] = old_position[1]
            
    def accelerate(self, move_vec):
        self.accel += move_vec

    def set_position(self, new_pos):
        self.position[0] = new_pos[0]
        self.position[1] = new_pos[1]
        
class Balloon(Sprite):
    pass

class Player(Sprite):
    
    def __init__(self, level):
        Sprite.__init__(self)
        self.level = level
        self.set_position(level.spawn)     
        self.left = Sprite.load_images(self, data.filepath("player_l"))
        self.right = Sprite.load_images(self, data.filepath("player_r"))
        self.set_anim_list(self.right)
        
    def check_collision(self):
       return not self.level.area_is_bg(self.get_rect())
        
    