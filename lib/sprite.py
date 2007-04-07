# PyWeek #4: Gasbag Follies - Produced by Vandelay Industries
#
# Copyright (c) 2007 Matthew Gregan <kinetik@flim.org>
#                    Joseph Miller <joff@googlehax.com>
#                    Elizabeth Moffatt <cybin@ihug.co.nz>
#                    Marcel Weber <xar@orcon.net.nz>
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF MIND, USE, DATA OR PROFITS, WHETHER
# IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING
# OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

import pygame
import euclid
import util
import os
import random
import display

class Sprite(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.anim_list     = []
        self.anim_frame    = 0
        self.position      = euclid.Vector2(0.0, 0.0)
        self.velocity      = euclid.Vector2(0.0, 0.0)
        self.accel         = euclid.Vector2(0.0, 0.0)
        self.top_speed     = euclid.Vector2(0.0, 0.0)
        self.drag_factor   = 0.0
        self.collide_speed = 1.0
        self.on_ground     = False
        self.dead          = False
        self.in_wind       = None
        self.anim_done     = None

    def alive(self):
        return not self.dead

    def kill(self):
        self.dead = True

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
            list_to_return.append(util.load_image(filename))
            frame_num += 1
            filename = self.construct_filename(image_basename, frame_num)

        if not list_to_return:
            raise Exception("empty image list")

        return list_to_return

    def get_rect(self):
        rect = self.anim_list[int(self.anim_frame)].get_rect()
        rect.move_ip(self.position[0] - (rect.width/2), self.position[1]-(rect.height))
        return rect

    def render(self, dest_surface, view):
        if self.dead:
            raise Exception("render called on dead sprite [%r]" % self)

        img  = self.anim_list[int(self.anim_frame)]
        rect = self.get_rect()
        rect.move_ip(view[0], view[1])

        if rect.right < 0 or rect.left > display.width or rect.bottom < 0 or rect.top > 480:
            return

        dest_surface.blit( img, rect )

    def animate(self, amount):
        anim_len = len(self.anim_list)
        self.anim_frame = (self.anim_frame + amount)
        if self.anim_frame >= anim_len:
            if self.anim_done: 
                self.anim_done()
            self.anim_frame = self.anim_frame % anim_len 

    def stop(self):
        self.velocity = euclid.Vector2(0.0, 0.0)
        self.accel    = euclid.Vector2(0.0, 0.0)

    def move(self, elapsed_time):
        if self.dead:
            raise Exception("move called on dead sprite [%r]" % self)

        self.apply_wind_force()

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

    def apply_wind_force(self):
        if self.in_wind:
            if self.in_wind == self.level.wind_left:
                self.velocity[0] += -7.0
            elif self.in_wind == self.level.wind_right:
                self.velocity[0] += 7.0
        self.in_wind = None

    def set_position(self, new_pos):
        self.position[0] = new_pos[0]
        self.position[1] = new_pos[1]


class Balloon(Sprite):
    frames = None
    pop_frames = None
    pop_sound = None

    def __init__(self, level, sprite_list):
        Sprite.__init__(self)

        if not Balloon.frames:
            Balloon.frames = Sprite.load_images(self, util.filepath("graphics/balloon_single"))
            Balloon.pop_frames = Sprite.load_images(self, util.filepath("graphics/balloon_pop"))

        if not Balloon.pop_sound:
            Balloon.pop_sound = pygame.mixer.Sound(util.filepath("sounds/pop.wav"))
            Balloon.pop_sound.set_volume(0.7)

        self.set_anim_list(Balloon.frames)
        self.level       = level
        self.velocity[1] = random.randrange(-75.0, -65.0)
        self.top_speed   = euclid.Vector2(100.0, 100.0)
        self.pop_timer   = 0.0
        self.popped      = False
        self.lifetime    = 60
        self.collect_delay = -1

    def can_collect(self):
        return not (self.collect_delay > 0 or self.dead or self.popped)

    def set_collect_delay(self, delay):
        self.collect_delay = delay

    def move(self, elapsed_time):
        if self.popped:
            self.pop_timer -= elapsed_time
            if (self.pop_timer <= 0.0):
                self.kill()
                self.pop_timer = 0.0
            else:
                self.animate(elapsed_time * 20.0)
        else:
            self.lifetime -= elapsed_time
            self.collect_delay -= elapsed_time
            if self.lifetime <= 0 and not self.popped:
                self.pop()
            Sprite.move(self, elapsed_time)

    def get_body_rect(self):
        rect = Sprite.get_rect(self)
        rect.height /= 2
        return rect

    def pop(self):
        if self.popped: return
        self.pop_sound.play()
        self.popped = True
        self.pop_timer = 0.05 * len(Balloon.pop_frames)
        self.set_anim_list(Balloon.pop_frames)

    def check_collision(self):
       hit = self.level.check_area(self.get_body_rect())
       if hit == self.level.spike:
           self.pop()
           return True
       elif hit == self.level.solid:
           return True

       wind_hit = self.level.check_wind(self.get_body_rect())
       if wind_hit in self.level.wind:
           self.in_wind = wind_hit

       return False


class Emitter(Sprite):
    frames = None
    balloon_frames = None
    inflate_sound = None

    def __init__(self, level, sprite_list):
        Sprite.__init__(self)

        if not Emitter.frames:
            Emitter.frames = Sprite.load_images(self, util.filepath("graphics/emitter"))

        if not Emitter.balloon_frames:
            Emitter.balloon_frames = Sprite.load_images(self, util.filepath("graphics/balloon_inflate"))

        if not Emitter.inflate_sound:
            Emitter.inflate_sound = pygame.mixer.Sound(util.filepath("sounds/inflate.wav"))
            Emitter.inflate_sound.set_volume(0.1)

        self.set_anim_list(Emitter.frames)
        self.level         = level
        self.balloon_list  = sprite_list
        self.emit_interval = 3.0
        self.emit_timer    = self.emit_interval
        self.emitting      = False
        self.sound_playing = False

    def emit(self):
       new = Balloon(self.level, self.balloon_list)
       new.position = self.position.copy()
       self.balloon_list.append(new)
       self.emit_timer = self.emit_interval
       self.emitting = False
       self.sound_playing = False
       self.anim_list = self.frames
       self.anim_frame = 0.0
       self.anim_done = None

    def move(self, elapsed_time):
        if (self.emitting):
            Sprite.animate(self, elapsed_time * 10.0)
        else:
            self.emit_timer -= elapsed_time
            if self.emit_timer < 1.0:
                if not self.sound_playing:
                    self.channel = self.inflate_sound.play()
                    self.sound_playing = True
                    
            if (self.emit_timer < 0.0):
                self.emitting   = True
                self.anim_frame = 0
                self.anim_done = self.emit
                self.anim_list = self.balloon_frames


class DartLauncher(Sprite):
    def __init__(self, level, sprite_list):
        Sprite.__init__(self)

        self.level           = level
        self.sprite_list     = sprite_list
        self.launch_interval = 5.0
        self.launch_timer    = self.launch_interval
        self.launch_vec      = euclid.Vector2(400.0, 0.0)

    def launch(self):
       new = Dart(self.level, self.sprite_list)
       new.position = self.position + (self.launch_vec * 0.1)
       new.velocity = self.launch_vec.copy()
       self.sprite_list.append(new)
       self.launch_timer = self.launch_interval

    def move(self, elapsed_time):
        self.launch_timer -= elapsed_time
        if (self.launch_timer < 0.0):
                self.launch()

    def render(self, dest_surface, view):
        pass


class Dart(Sprite):
    frames_l = None
    frames_r = None

    def __init__(self, level, sprite_list):
        Sprite.__init__(self)

        if not Dart.frames_l:
            Dart.frames_l = Sprite.load_images(self, util.filepath("graphics/dart_l"))
            Dart.frames_r = Sprite.load_images(self, util.filepath("graphics/dart_r"))

        self.set_anim_list(Dart.frames_l)
        self.level         = level
        self.top_speed     = euclid.Vector2(400.0, 400.0)

    def check_collision(self):
        if self.level.check_area(self.get_rect()) != self.level.background:
            self.dead = True

    def check_for_balloons(self, sprite_list):
        for obj in sprite_list:
            if isinstance(obj, Balloon):
                if not obj.dead and obj.get_body_rect().colliderect(self.get_rect()):
                    obj.pop()
                    self.kill()

    def move(self, elapsed_time):
        if (self.velocity < 0.0):
            self.set_anim_list(Dart.frames_l)
        else:
            self.set_anim_list(Dart.frames_r)

        Sprite.move(self, elapsed_time)
