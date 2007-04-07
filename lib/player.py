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
import sprite
from sprite import *

class Player(Sprite):
    def __init__(self, level, balloon_list):
        Sprite.__init__(self)
        self.level = level
        self.balloon_list = balloon_list
        self.set_position(level.spawn)
        self.left = Sprite.load_images(self, util.filepath("player_l"))
        self.right = Sprite.load_images(self, util.filepath("player_r"))
        self.hang_left = Sprite.load_images(self, util.filepath("player_hang_l"))
        self.hang_right = Sprite.load_images(self, util.filepath("player_hang_r"))
        self.fall = Sprite.load_images(self, util.filepath("player_fall"))
        self.fall_left = Sprite.load_images(self, util.filepath("player_fall_l"))
        self.fall_right = Sprite.load_images(self, util.filepath("player_fall_r"))
        self.balloon_bunch = []
        self.balloon_bunch.append(Sprite.load_images(self, util.filepath("balloon")))
        self.balloon_bunch.append(Sprite.load_images(self, util.filepath("two_balloons")))
        self.balloon_bunch.append(Sprite.load_images(self, util.filepath("three_balloons")))
        self.balloon_bunch.append(Sprite.load_images(self, util.filepath("four_balloons")))
        self.balloon_bunch.append(Sprite.load_images(self, util.filepath("five_balloons")))
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
                self.pop_balloons()

            wind_hit = self.level.check_wind(bunch_rect)
            if wind_hit in self.level.wind:
                self.in_wind = wind_hit

        return self.level.check_area(rect) == self.level.solid

    def check_balloons(self, sprite_list):
        rect = self.get_hand_rect()
        for obj in sprite_list:
            if isinstance(obj, sprite.Balloon):
                if obj.can_collect() \
                        and obj.get_rect().colliderect(rect) \
                        and self.balloon_count < len(self.balloon_bunch):
                    obj.kill()
                    self.add_balloon()

    def check_darts(self, sprite_list):
        rect = self.get_bunch_rect(self.get_bunch_img())
        if not rect:
            return

        for obj in sprite_list:
            if isinstance(obj, sprite.Dart):
                if obj.alive() and obj.get_rect().colliderect(rect):
                    obj.kill()
                    self.pop_balloons()

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

    def pop_balloons(self):
        if self.balloon_count > 0:
            limit = 1
            if self.balloon_count == 1:
                limit = 0
            while self.balloon_count > limit:
                new = self._release_balloon()
                new.pop()

    def _release_balloon(self):
        new = Balloon(self.level)
        new.position = self.position + euclid.Vector2(0.0, -(self.get_rect().height * 0.9))
        self.balloon_list.append(new)
        self.balloon_count -= 1
        return new

    def drop_balloon(self):
        if self.balloon_count > 0:
            new = self._release_balloon()
            new.set_collect_delay(3)

    def add_balloon(self):
        if self.balloon_count >= len(self.balloon_bunch):
            print "Debug! Don't do this in release!"
            return
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
