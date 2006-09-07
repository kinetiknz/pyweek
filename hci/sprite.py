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
import cPickle

from pygame.locals import *
import pygame
from pgu import tilevid, algo
import euclid
import movement
import sprite_eater
import visibility

class Sprite(object):
    MIN_MOVEMENT_SQ = 0.1

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
        self.sprite.backref = self
        self.bounds = pygame.Rect(game.bounds)
        self.bounds.inflate_ip(-self.sprite.rect.w * 2, -self.sprite.rect.h * 2)
        self.trophy = False

        # size/rotation
        self.orig_image   = self.sprite.image
        self.orig_shape   = self.sprite.shape
        self.scale_factor = 1.0
        self.rotation     = 0.0

        # animation
        self.frame = 0.0
        self.frames = []
        self.frames.append(game.images[self.name])

        # movement
        self.last_pos  = euclid.Vector2(0, 0)
        self.position  = euclid.Vector2(0, 0)
        self.get_sprite_pos()
        self.stop()
        self.accel     = 0.0
        self.drag      = 0.85
        self.top_speed = 0.0
        self.target    = None
        self.waypoint = 0
        self.waypoints = []

        # something to do with PGU?
        if hasattr(tile, 'rect'):
            game.clayer[tile.ty][tile.tx] = 0
        game.sprites.append(self.sprite)

    def set_scale(self, new_scale_factor):
        self.scale_factor = new_scale_factor
        self.reimage()

    def set_rotation(self, new_rotation):
        self.rotation = new_rotation
        self.reimage()

    def scale(self, scale_factor):
        self.scale_factor *= scale_factor
        self.reimage()

    def rotate(self, rotation):
        self.rotation += rotation
        self.reimage()

    def reimage(self):
        if (self.scale_factor == 1.0 and self.rotation == 0.0):
            self.sprite.setimage((self.orig_image, self.orig_shape))
            return

        newshape = self.orig_shape.inflate(0, 0)

        if self.scale_factor != 1.0:
            newshape.width *= self.scale_factor
            newshape.height *= self.scale_factor

        oldc = self.sprite.rect.center
        newsurf = pygame.transform.rotozoom(self.orig_image, self.rotation, self.scale_factor)
        self.sprite.setimage((newsurf, newshape))
        self.sprite.rect.center = oldc

    def set_image(self, new_image):
        oldc = self.sprite.rect.center
        self.sprite.setimage(new_image)
        self.sprite.rect.center = oldc

        self.orig_image = self.sprite.image
        self.orig_shape = self.sprite.shape
        self.reimage()

    def get_image(self):
        return self.orig_image

    def get_sprite_pos(self):
        self.position[0] = self.sprite.rect.centerx
        self.position[1] = self.sprite.rect.centery

    def set_sprite_pos(self):
        self.sprite.rect.centerx = self.position[0]
        self.sprite.rect.centery = self.position[1]

    def stop(self):
        self.last_pos[0] = self.position[0]
        self.last_pos[1] = self.position[1]
        self.waypoint = 0
        self.waypoints = []

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

    def moving(self):
        return self.velocity.magnitude_squared() >= self.MIN_MOVEMENT_SQ

    def verlet_move(self, check_bounds = True):
        # use verlet integration to move our sprite
        move_vec = self.velocity()

        if move_vec.magnitude_squared() < self.MIN_MOVEMENT_SQ:
            return False

        move_vec *= self.drag

        if check_bounds:
            if self.position[0] < self.bounds.left:    self.position[0] = self.bounds.left
            if self.position[0] > self.bounds.right:   self.position[0] = self.bounds.right
            if self.position[1] < self.bounds.top:     self.position[1] = self.bounds.top
            if self.position[1] > self.bounds.bottom:  self.position[1] = self.bounds.bottom

        self.last_pos = self.position
        self.position = self.last_pos + move_vec
        self.set_sprite_pos()

        return True

    def view_me(self, game):
        gx = self.position[0] - (game.view.w/2) + game.tile_w
        gy = self.position[1] - (game.view.h/2) + game.tile_h

        game.view.x = gx
        game.view.y = gy

    def load_path(self, pathname):
        file = open('data/paths/' + pathname, 'r')
        path = cPickle.load(file)
        for x, y in path:
            self.waypoints.append(euclid.Vector2(x, y))

    def animate(self, step):
        oldframe = int(self.frame)
        self.frame = (self.frame + step) % len(self.frames)
        if oldframe != int(self.frame):
            self.set_image(self.frames[int(self.frame)])

    def step(self, game, sprite):
        pass

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
        self.recording = False
        self.seen = False
        self.mouse_move = False
        self.speed = 1.0
        self.top_speed = 5.0
        self.player_target = None
        self.impersonating = None

        self.landing = True
        self.set_image(game.images['none'])
        Saucer(game, tile, values)

        game.player = self

        self.known_items = {}

        self.walking_sound = pygame.mixer.Sound('data/sfx/Walking.ogg')
        self.walking_sound.set_volume(0.5)

        self.raygun_sound  = pygame.mixer.Sound('data/sfx/Raygun.ogg')
        self.beam_sound    = pygame.mixer.Sound('data/sfx/Beam.ogg')
        self.beam_sound_isplaying    = False
        self.walking_sound_isplaying = False

    def landed(self, game):
        self.landing = False
        self.set_image(self.frames[int(self.frame)])

    def step(self, game, sprite):
        if self.landing:
            self.view_me(game)
            return

        game.deferred_effects.append(lambda: self.draw_morph_targets(game))

        key = pygame.key.get_pressed()

        if self.seen:
            # relx = self.position[0] - game.view.x - (game.images['warn'][0].get_width()/2)
            # rely = self.position[1] - game.view.y - (game.images['warn'][0].get_height()/2)
            # game.deferred_effects.append(lambda: game.screen.blit(game.images['warn'][0], (relx, rely, 0, 0)))
            self.seen = False

        dx, dy = 0, 0
        if key[K_w]: dy -= 1
        if key[K_s]: dy += 1
        if key[K_a]: dx -= 1
        if key[K_d]: dx += 1
        if key[K_SPACE] and game.frame % 8 == 0:
            self.fire(game, sprite)
        if key[K_LSHIFT]:
            self.top_speed = 15.0
            self.speed     = 3.0
        else:
            self.top_speed = 5.0
            self.speed     = 1.0

        if self.impersonating:
            self.set_image(self.impersonating.get_image())
            return

        buttons = pygame.mouse.get_pressed()
        loc = pygame.mouse.get_pos()

        if (dx != 0 or dy != 0):
            self.mouse_move = False
            if not self.walking_sound_isplaying:
                 self.walking_sound.play(-1)
                 self.walking_sound_isplaying = True

        if (dx == 0 and dy == 0):
            if self.walking_sound_isplaying:
                self.walking_sound.stop()
                self.walking_sound_isplaying = False

        if buttons[2] == 0 and self.beam_sound_isplaying == True:
            self.beam_sound.stop()
            self.beam_sound_isplaying = False

        if buttons[0]:
            self.target = euclid.Vector2(game.view.x + loc[0], game.view.y + loc[1])
            self.mouse_move = True
            if self.recording: self.recorded_path.append(self.target)

        if buttons[2]:
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

            # ugly ray gun logic
            SelectionTest(game, (game.view.x + loc[0], game.view.y + loc[1]), None)
            if self.player_target and not self.player_target.__class__ in self.known_items:
                self.player_target.stop()
                self.player_target.waypoints.append(self.position)
                movement.move(self.player_target.position, self.position, 1)
                self.player_target.rotate(6.25)
                self.player_target.scale(0.95)
                self.player_target.set_sprite_pos()
                if self.player_target.scale_factor < 0.25:
                    self.learn(self.player_target)
                    game.sprites.remove(self.player_target.sprite)
                    self.player_target = None

            # ugly ray gun effect
            relx = self.position[0] - game.view.x + 24
            rely = self.position[1] - game.view.y - 12

            ln = algo.getline([relx, rely], loc)
            for l in xrange(0, len(ln), 7):
                def draw():
                    c = [0, random.randint(0, 255), 255]
                    r = [relx, rely]
                    rx = random.randint(-5, 5)
                    ry = random.randint(-5, 5)
                    p = ln[l][0] + rx, ln[l][1] + ry
                    def proc():
                        pygame.draw.line(game.screen, c, r, p, 2)
                    return proc

                game.deferred_effects.append(draw())

            for l in xrange(10):
                rsx = random.gauss(0, 7)
                rsy = random.gauss(0, 7)
                SelectionTest(game, (game.view.x + loc[0] + rsx,
                                     game.view.y + loc[1] + rsy), None)

        if self.mouse_move:
            if self.move_toward(self.target, self.speed, 10.0):
                self.mouse_move = False
        else:
            self.accelerate(euclid.Vector2(dx*self.speed, dy*self.speed))

        if not self.verlet_move():
            self.mouse_move = False
            self.walking_sound.stop()
            return

        self.animate(0.2)
        self.view_me(game)

    def fire(self, game, sprite):
        Bullet('shot', game, sprite)
        self.raygun_sound.play()

    def learn(self, target):
        self.known_items[target.__class__] = target

    def morph(self):
        if not self.impersonating and len(self.known_items) == 0:
            return
        if not self.impersonating:
            self.impersonating = random.choice(self.known_items.values())
            del self.known_items[self.impersonating.__class__]
        else:
            self.set_image(self.frames[0])
            self.impersonating = None

    def draw_morph_targets(self, game):
        scale_to = 32
        x, y = game.view.w - scale_to, 0
        for t in self.known_items.values():
            def draw():
                dx = x
                dy = y
                img = pygame.transform.scale(t.get_image(), (scale_to, scale_to))
                def proc():
                    game.screen.blit(img, (dx, dy, 0, 0))
                return proc
            game.deferred_effects.append(draw())
            y += scale_to

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
        super(Human, self).__init__('enemy', 'enemy', game, tile, values)
        self.sprite.agroups = game.string2groups('Background')
        self.sprite.hit = lambda game, sprite, other: self.hit(game, sprite, other)
        self.speed = 1.0
        self.top_speed = 4.0
        #self.load_path('lake_circuit')

    def step(self, game, sprite):
        self.move(game)

    def move(self, game):
        if len(self.waypoints) == 0: return

        target = self.waypoints[self.waypoint]

        if visibility.can_be_seen(game.player.position, self.position, target):
            game.player.seen = True
            relx = self.position[0] - game.view.x - (game.images['warn'][0].get_width()/2)
            rely = self.sprite.rect.y - game.view.y - (game.images['warn'][0].get_height())
            game.deferred_effects.append(lambda: game.screen.blit(game.images['warn'][0], (relx, rely, 0, 0)))


        if self.move_toward(target, self.speed, 10.0):
            self.waypoint = (self.waypoint + 1) % len(self.waypoints)

        if not self.verlet_move():
            self.waypoint = (self.waypoint + 1) % len(self.waypoints)

        self.set_sprite_pos()

    def hit(self, game, sprite, other):
        push(sprite, other)
        self.get_sprite_pos()

class Cow(Sprite):
    def __init__(self, game, tile, values=None):
        super(Cow, self).__init__('cow1', 'enemy', game, tile, values)
        self.frames.append(game.images['cow2'])
        self.sprite.agroups = game.string2groups('Background')
        self.sprite.hit = lambda game, sprite, other: self.hit(game, sprite, other)
        self.speed = 0.2
        self.top_speed = 0.4
        self.trophy = True
        self.load_path('lvl1_cow')

    def step(self, game, sprite):
        self.move(game)

        if self.trophy:
            relx = self.position[0] - game.view.x - (game.images['trophy'][0].get_width()/2)
            rely = self.sprite.rect.y - game.view.y - (game.images['trophy'][0].get_height())
            game.deferred_effects.append(lambda: game.screen.blit(game.images['trophy'][0], (relx, rely, 0, 0)))

    def move(self, game):
        if len(self.waypoints) == 0: return

        target = self.waypoints[self.waypoint]

        if self.move_toward(target, self.speed, 10.0):
            self.waypoint = (self.waypoint + 1) % len(self.waypoints)

        if not self.verlet_move():
            self.waypoint = (self.waypoint + 1) % len(self.waypoints)

        self.animate(0.025)
        self.set_sprite_pos()


    def hit(self, game, sprite, other):
        push(sprite, other)
        self.get_sprite_pos()

class Saucer(Sprite):
    def __init__(self, game, tile, values=None):
        super(Saucer, self).__init__('saucer0', 'Background', game, tile, values)
        self.frames.append(game.images['saucer1'])
        self.frames.append(game.images['saucer2'])
        self.speed     = 3.0
        self.top_speed = 7.0
        self.set_scale(3.0)
        self.land_pos      = self.position.copy()
        self.position[1]   = game.view.y
        self.land_distance = (self.land_pos - self.position).magnitude()
        self.stop()
        pygame.mixer.music.load('data/sfx/SaucerLand.ogg')
        pygame.mixer.music.play(0, 0.0)

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
        if game.player.landing:
            percent = 1.0 - ((self.land_pos - self.position).magnitude() / self.land_distance)
            self.move_toward(self.land_pos, self.speed * (1.0 - percent), 10.0)

            if not self.verlet_move(False):
                game.player.landed(game)
                self.stop()
                self.speed = 0.0
                self.top_speed = 0.0
                self.set_scale(1.0)
                self.set_rotation(0.0)
                self.set_sprite_pos()
                return

            self.set_sprite_pos()
            self.animate(1.0 - (0.9 * percent))
            self.set_scale(3.0 - (2.0 * (math.pow(percent, 1.5))))
            self.set_rotation(math.sin(percent*math.pi*6.0)*1.0)
        else:
            self.animate(0.1)

class Tree(Sprite):
    def __init__(self, game, tile, values=None):
        super(Tree, self).__init__('tree', 'Background', game, tile, values)

class Bush(Sprite):
    def __init__(self, game, tile, values=None):
        super(Bush, self).__init__('bush', 'Background', game, tile, values)

class SelectionTest(Sprite):
    def __init__(self, game, tile, values=None):
        super(SelectionTest, self).__init__('laser', 'shot', game, tile, values)
        self.sprite.agroups = game.string2groups('enemy,Background')
        self.sprite.hit = lambda game, sprite, other: self.hit(game, sprite, other)
        self.lived_once = False

    def step(self, game, sprite):
        if self.lived_once == False:
            self.lived_once = True
            return
        game.player.player_target = None
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
