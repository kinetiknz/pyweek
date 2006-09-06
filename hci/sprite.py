# Copyright (c) 2006 Matthew Gregan <kinetik@flim.org>
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

import random
import time
import math

from pygame.locals import *
import pygame
from pgu import tilevid
import euclid

import movement
import sprite_eater
import visibility

class AbstractClassException(Exception): pass

class Sprite(object):
    def __init__(self, name, group, game, tile, values=None):
        self.name = name
        self.group = group
        rect = tile
        if hasattr(tile, 'rect'):
            rect = tile.rect
        self.sprite = tilevid.Sprite(game.images[self.name], rect)
        self.sprite.loop = lambda game, sprite: self.step(game, sprite)
        self.sprite.groups = game.string2groups(self.group)
        self.hitmask = pygame.surfarray.array_alpha(self.sprite.image)
        self.rect = self.sprite.rect
        self.sprite.backref = self
        self.bounds = pygame.Rect(game.bounds)
        self.bounds.inflate_ip(-self.sprite.rect.w * 2, -self.sprite.rect.h * 2)

        # size / rotation
        self.orig_image   = self.sprite.image
        self.orig_shape   = self.sprite.shape
        self.scale_factor = 1.0
        self.rotation     = 0.0

        # animation
        self.frame = 0.0
        self.frames = []
        self.frames.append(game.images[self.name])

        # movement
        self.last_pos  = euclid.Vector2(0,0)
        self.position  = euclid.Vector2(0,0)
        self.get_sprite_pos()
        self.stop()
        self.accel     = 0.0
        self.drag      = 0.85
        self.top_speed = 0.0
        self.target    = None

        # something to do with PGU?
        if hasattr(tile, 'rect'):
            game.clayer[tile.ty][tile.tx] = 0
        game.sprites.append(self.sprite)

    def scale(self, new_scale_factor):
        self.scale_factor = new_scale_factor
        self.reimage()

    def rotate(self, new_rotation):
        self.rotation = new_rotation
        self.reimage()

    def reimage(self):
        if (self.scale_factor == 1.0 and self.rotation == 0.0):
            self.sprite.setimage((self.orig_image, self.orig_shape))
            return

        if self.scale_factor != 1.0:
            newrect = self.orig_shape.inflate(self.orig_shape.w * (self.scale_factor-1.0) , \
                                              self.orig_shape.h * (self.scale_factor-1.0) )

        newsurf = pygame.transform.rotozoom(self.sprite.image, self.rotation, self.scale_factor)
        self.sprite.setimage(newsurf)

    def set_image(self, new_image):
        self.sprite.setimage(new_image)
        self.orig_image = self.sprite.image
        self.orig_shape = self.sprite.shape
        self.reimage()

    def get_sprite_pos(self):
        self.position[0] = self.sprite.rect.x
        self.position[1] = self.sprite.rect.y

    def set_sprite_pos(self):
        self.sprite.rect.x = self.position[0]
        self.sprite.rect.y = self.position[1]

    def stop(self):
        self.last_pos[0] = self.position[0]
        self.last_pos[1] = self.position[1]

    def accelerate(self, vector):
        move_vec = self.velocity() + vector

        if move_vec.magnitude() > self.top_speed:
            move_vec.normalize()
            move_vec *= self.top_speed

        self.position = self.last_pos + move_vec

    def move_toward(self, target, speed, min_distance):
            to_target = target - self.position
            length = to_target.magnitude()

            if (length <= min_distance):
                return True

            to_target /= length
            to_target *= speed
            self.accelerate(to_target)

            return False

    def velocity(self):
        return self.position - self.last_pos

    def verlet_move(self):
        # use verlet integration to move our sprite
        move_vec = self.velocity()

        if move_vec.magnitude_squared() < 0.1:
            return False

        move_vec *= self.drag

        if self.position[0] < self.bounds.left:    self.position[0] = self.bounds.left
        if self.position[0] > self.bounds.right:   self.position[0] = self.bounds.right
        if self.position[1] < self.bounds.top:     self.position[1] = self.bounds.top
        if self.position[1] > self.bounds.bottom:  self.position[1] = self.bounds.bottom

        self.last_pos = self.position
        self.position = self.last_pos + move_vec
        self.sprite.rect.x = self.position[0]
        self.sprite.rect.y = self.position[1]

        return True

    def view_me(self, game):
        gx = self.sprite.rect.x - (game.view.w/2) + game.tile_w
        gy = self.sprite.rect.y - (game.view.h/2) + game.tile_h

        game.view.x = gx
        game.view.y = gy

    def step(self, game, sprite):
        raise AbstractClassException, "abstract method called"

class Player(Sprite):
    def __init__(self, game, tile, values=None):
        super(Player, self).__init__('player', 'player', game, tile, values)
        self.frames.append(game.images['player1'])
        self.frames.append(game.images['player2'])
        self.frames.append(game.images['player3'])
	self.frames.append(game.images['player4'])
	self.frames.append(game.images['player5'])
        self.sprite.agroups = game.string2groups('Background')
        self.sprite.hit  = lambda game, sprite, other: self.hit(game, sprite, other)
        self.sprite.shoot = lambda game, sprite: self.fire(game, sprite)
        self.sprite.score = 0
        self.seen = False
        self.mouse_move = False
        self.speed = 1.0
        self.top_speed = 5.0
        self.player_target = None

        game.player = self

        self.known_items = []

        self.walking_snd_channel = pygame.mixer.find_channel()

        self.walking_sound = pygame.mixer.Sound('data/sfx/Walking.ogg')
        self.raygun_sound = pygame.mixer.Sound('data/sfx/Raygun.ogg')
        self.beam_sound = pygame.mixer.Sound('data/sfx/Beam.ogg')
        self.beam_sound_isplaying = False


    def step(self, game, sprite):
        key = pygame.key.get_pressed()

        if self.seen:
            relx = self.sprite.rect.x - game.view.x + 44
            rely = self.sprite.rect.y - game.view.y + 5
            game.deferred_effects.append(lambda:game.screen.blit(game.images['warn'][0], (relx, rely, 0, 0) ) )
            self.seen = False

        dx, dy = 0, 0
        if key[K_w]:
            dy -= 1
            self.walking_snd_channel.queue(self.walking_sound)
        if key[K_s]:
            dy += 1
            self.walking_snd_channel.queue(self.walking_sound)
        if key[K_a]:
            dx -= 1
            self.walking_snd_channel.queue(self.walking_sound)
        if key[K_d]:
            dx += 1
            self.walking_snd_channel.queue(self.walking_sound)
        if key[K_SPACE] and game.frame % 8 == 0:
            self.fire(game, sprite)
        if key[K_LSHIFT]:
            self.top_speed = 15.0
            self.speed     = 3.0
        else:
            self.top_speed = 5.0
            self.speed     = 1.0

        buttons = pygame.mouse.get_pressed()
        loc = pygame.mouse.get_pos()

        if (dx != 0 or dy != 0): self.mouse_move = False

        if buttons[0] == 0 and self.beam_sound_isplaying == True:
            self.beam_sound.stop()
            self.beam_sound_isplaying = False

        if buttons[2]:
            self.target = euclid.Vector2(game.view.x + loc[0], game.view.y + loc[1])
            self.mouse_move = True

        if buttons[0]:
            if not self.beam_sound_isplaying:
                self.beam_sound.play()
                self.beam_sound_isplaying = True

            loc = pygame.mouse.get_pos()
            loc = list(loc)

            def s2t(x, y):
                stx = x / game.tile_w
                sty = y / game.tile_h
                return stx, sty

            # find selected tile
            tx, ty = s2t(game.view.x + loc[0], game.view.y + loc[1])
            #game.set([tx, ty], 2)

            # ugly ray gun effect
            relx = self.sprite.rect.x - game.view.x + 44
            rely = self.sprite.rect.y - game.view.y + 5

            SelectionTest(game, (game.view.x + loc[0], game.view.y + loc[1]), None)
            if self.player_target and game.frame % 5 == 0:
                self.player_target.scale(0.9)
                self.player_target = None

            relx2 = relx
            rely2 = rely

            jitter = random.randint(0, 3)
            if jitter % 2 == 0:
                relx += jitter
                rely2 += jitter
                loc[1] += jitter * 3
            else:
                rely += jitter
                loc[0] += jitter * 3
                relx2 += jitter

            game.deferred_effects.append(lambda:
                                         pygame.draw.line(game.screen, [0, 0, 255],
                                                          [relx, rely], loc, 2))
            game.deferred_effects.append(lambda:
                                         pygame.draw.line(game.screen, [0, 255, 255],
                                                          [relx2, rely2], loc, 3))
            #self.beam_sound.stop()

        if self.mouse_move:
            if self.move_toward(self.target, self.speed, 10.0):
                self.mouse_move = False
        else:
            self.accelerate(euclid.Vector2(dx*self.speed,dy*self.speed))

        if not self.verlet_move():
            self.mouse_move = False
            return

        oldframe = int(self.frame)
        self.frame = (self.frame + 0.2) % len(self.frames)
        if oldframe != int(self.frame):
            self.set_image(self.frames[int(self.frame)])

        self.view_me(game)

    def fire(self, game, sprite):
        Bullet('shot', game, sprite)
        self.raygun_sound.play()

    def learn(self, target):
        self.known_items.append(target)

    def morph(self):
        target = random.choice(self.known_items)

    def hit(self, game, sprite, other):
        push(sprite, other)
        self.get_sprite_pos()
        self.view_me(game)

class Bullet(Sprite):
    def __init__(self, name, game, tile, values=None):
        origin = [tile.rect.right, tile.rect.centery - 2]
        super(Bullet, self).__init__(name, 'shot', game, origin, values)
        self.sprite.agroups = game.string2groups('enemy')
        self.sprite.hit = lambda game, sprite, other: self.hit(game, sprite, other)

    def step(self, game, sprite):
        self.sprite.rect.x += 8
        if self.sprite.rect.left > game.view.right:
            game.sprites.remove(self.sprite)

    def hit(self, game, sprite, other):
        if other in game.sprites:
            game.sprites.remove(other)
        game.player.sprite.score += 500

class Human(Sprite):
    def __init__(self, game, tile, values=None):
        super(Human, self).__init__('cow', 'enemy', game, tile, values)
        self.sprite.agroups = game.string2groups('Background')
        self.sprite.hit = lambda game, sprite, other: self.hit(game, sprite, other)
        self.waypoint = 0
        self.waypoints = []
        self.speed = 1.0
        self.top_speed = 4.0
        self.stuck_sensor = 0

        for pts in xrange(10):
            self.waypoints.append(euclid.Vector2(random.randint(10, game.bounds.width-10),random.randint(10, game.bounds.height-10)))

    def step(self, game, sprite):
        self.move(game)

    def move(self, game):
        target = self.waypoints[self.waypoint]

        if visibility.can_be_seen(game.player.position, self.position, target):
            game.player.seen = True

        if self.move_toward(target, self.speed, 10.0):
            self.waypoint = (self.waypoint + 1) % len(self.waypoints)

        if not self.verlet_move():
            self.waypoint = (self.waypoint + 1) % len(self.waypoints)

        self.set_sprite_pos()

        def close(a, b, epsilon):
            if a == b:
                return True
            if a - epsilon < b and a > b:
                return True
            if a + epsilon > b and a < b:
                return True
            return False

        if close(self.last_pos.x, self.position.x, 3.0) \
           and close(self.last_pos.y, self.position.y, 3.0):
            if self.stuck_sensor == 5:
                self.waypoints = []
                for pts in xrange(10):
                    self.waypoints.append(euclid.Vector2(random.randint(10, game.bounds.width-10),random.randint(10, game.bounds.height-10)))
                self.waypoint = (self.waypoint + 1) % len(self.waypoints)
                self.stuck_sensor = 0
            else:
                self.stuck_sensor += 1

    def hit(self, game, sprite, other):
        push(sprite, other)
        self.get_sprite_pos()

class Saucer(Sprite):
    def __init__(self, game, tile, values=None):
        super(Saucer, self).__init__('saucer0', 'Background', game, tile, values)
        self.frames.append(game.images['saucer1'])
        self.frames.append(game.images['saucer2'])

        #d = time.time()
        #self.test = sprite_eater.SpriteEater(self.sprite.image)
        #while self.test.advance_frame():
        #    self.test.advance_frame()
        #    self.test.advance_frame()
        #    newimage = self.sprite.image.copy()
        #    self.test.blit_to(newimage)
        #    self.frames.append(newimage)
        #logit('took', time.time() - d)

    def step(self, game, sprite):
        oldframe = int(self.frame)
        self.frame = (self.frame + 0.1) % len(self.frames)
        if oldframe != int(self.frame):
            self.set_image(self.frames[int(self.frame)])

class Tree(Sprite):
    def __init__(self, game, tile, values=None):
        super(Tree, self).__init__('tree', 'Background', game, tile, values)

    def step(self, game, sprite):
        pass

class Bush(Sprite):
    def __init__(self, game, tile, values=None):
        super(Bush, self).__init__('bush', 'Background', game, tile, values)

    def step(self, game, sprite):
        pass

class SelectionTest(Sprite):
    def __init__(self, game, tile, values=None):
        super(SelectionTest, self).__init__('cow', 'shot', game, tile, values)
        self.sprite.agroups = game.string2groups('enemy,Background')
        self.sprite.hit = lambda game, sprite, other: self.hit(game, sprite, other)
        self.lived_once = False

    def step(self, game, sprite):
        if self.lived_once == False:
            self.lived_once = True
            return
        game.sprites.remove(sprite)

    def hit(self, game, sprite, other):
        game.player.player_target = other.backref

def push(mover, away_from):
    if mover._rect.bottom <= away_from._rect.top and mover.rect.bottom > away_from.rect.top:
        mover.rect.bottom = away_from.rect.top
    if mover._rect.right <= away_from._rect.left \
           and mover.rect.right > away_from.rect.left:
        mover.rect.right = away_from.rect.left
    if mover._rect.left >= away_from._rect.right \
           and mover.rect.left < away_from.rect.right:
        mover.rect.left = away_from.rect.right
    if mover._rect.top >= away_from._rect.bottom \
           and mover.rect.top < away_from.rect.bottom:
        mover.rect.top = away_from.rect.bottom
