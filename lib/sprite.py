import pygame
import euclid
import data
import os
import random
import display

class Sprite(pygame.sprite.Sprite):

    def __init__(self):
        self.anim_list     = []
        self.anim_frame    = -1
        self.position      = euclid.Vector2(0.0, 0.0)
        self.velocity      = euclid.Vector2(0.0, 0.0)
        self.accel         = euclid.Vector2(0.0, 0.0)
        self.top_speed     = euclid.Vector2(0.0, 0.0)
        self.drag_factor   = 0.0
        self.collide_speed = 1.0
        self.on_ground     = False

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
        rect.move_ip(self.position[0] - (rect.width/2), self.position[1]-(rect.height))
        return rect
    
    def render(self, dest_surface, view):
        img  = self.anim_list[int(self.anim_frame)]
        rect = self.get_rect()
        rect.move_ip(view[0], view[1])
        
        if rect.right < 0 or rect.left > display.width or rect.bottom < 0 or rect.top > 480:
            return
        
        dest_surface.blit( img, rect )

    def animate(self, amount):
        self.anim_frame = (self.anim_frame + amount) % len(self.anim_list)
        
    def stop(self):
        self.velocity = euclid.Vector2(0.0, 0.0)
        self.accel    = euclid.Vector2(0.0, 0.0)
        
    def move(self, elapsed_time):
        old_velocity = self.velocity.copy()
        old_position = self.position.copy()
        
        # move x first
        if self.velocity[0] > self.top_speed[0]:
            self.velocity[0] = self.top_speed[0]
        elif self.velocity[0] < -self.top_speed[0]:
            self.velocity[0] = -self.top_speed[0]
        
        self.position[0] += (self.velocity[0] * elapsed_time)
        
        if self.check_collision():
            self.velocity[0] = old_velocity[0] * self.collide_speed
            self.position[0] = old_position[0]
        else:
            self.velocity[0] += (self.accel[0] * elapsed_time)
        
        # move y now
        if self.velocity[1] > self.top_speed[1]:
            self.velocity[1] = self.top_speed[1]
        elif self.velocity[1] < -self.top_speed[1]:
            self.velocity[1] = -self.top_speed[1]
                
        self.position[1] += (self.velocity[1] * elapsed_time)
        
        if self.check_collision():
            self.velocity[1] = old_velocity[1] * self.collide_speed
            self.position[1] = old_position[1]
        else:
            self.velocity[1] += (self.accel[1] * elapsed_time)
                    
        self.apply_drag(self.velocity, elapsed_time)
        ychange = self.position[1] - old_position[1]
        if (ychange < 1.0 and ychange > -1.0):
            self.on_ground = True
        else:
            self.on_ground = False
        
    
    def apply_drag(self, reference, elapsed_time):
        drag = self.drag_factor * elapsed_time
        
        if reference[0] < drag and reference[0] > -drag:
            reference[0] = 0.0
        elif reference[0] < 0.0:
            reference[0] += drag
        else:
            reference[0] -= drag 

    def set_position(self, new_pos):
        self.position[0] = new_pos[0]
        self.position[1] = new_pos[1]



class Balloon(Sprite):
    frames = None
    
    def __init__(self, level):
        Sprite.__init__(self)

        if not Balloon.frames:
            Balloon.frames = Sprite.load_images(self, data.filepath("balloon"))
            
        self.set_anim_list(Balloon.frames)
        self.anim_frame  = 0
        self.level       = level
        self.velocity[1] = random.randrange(-75.0, -65.0)
        self.top_speed   = euclid.Vector2(100.0, 100.0)

    def check_collision(self):
       return not self.level.area_is_bg(self.get_rect())
          