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

from pygame.locals import *
import pygame
from pgu import tilevid
import euclid

import movement
import sprite_eater
import visibility

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
        self.frame = 0.0
        self.frames = []
        self.frames.append(game.images[self.name])

        if hasattr(tile, 'rect'):
            game.clayer[tile.ty][tile.tx] = 0
        game.sprites.append(self.sprite)

    def step(self, game, sprite):
        raise AbstractClassException

class Player(Sprite):
    def __init__(self, game, tile, values=None):
        super(Player, self).__init__('player', 'player', game, tile, values)
        self.frames.append(game.images['player1'])
        self.frames.append(game.images['player2'])
        self.frames.append(game.images['player3'])
	self.frames.append(game.images['player4'])
	self.frames.append(game.images['player5'])
	self.frames.append(game.images['player6'])
        self.sprite.agroups = game.string2groups('Background')
        self.sprite.hit  = lambda game, sprite, other: self.hit(game, sprite, other)
        self.sprite.shoot = lambda game, sprite: self.fire(game, sprite)
        self.sprite.score = 0
        self.seen = False
        self.mouse_move = False

        game.player = self

        self.known_items = []

    def step(self, game, sprite):
        key = pygame.key.get_pressed()

        if self.seen:
            relx = self.sprite.rect.x - game.view.x + 44
            rely = self.sprite.rect.y - game.view.y + 5
            game.deferred_effects.append(lambda:game.screen.blit(game.images['warn'][0], (relx, rely, 0, 0) ) )
            self.seen = False

        dx, dy = 0, 0
        if key[K_w]: dy -= 1
        if key[K_s]: dy += 1
        if key[K_a]: dx -= 1
        if key[K_d]: dx += 1
        if key[K_SPACE] and game.frame % 8 == 0:
            self.fire(game, sprite)
        if key[K_LSHIFT]: self.speed = 15
        else: self.speed = 5

        buttons = pygame.mouse.get_pressed()
        loc = pygame.mouse.get_pos()

        if buttons[2]:
            self.move_to = euclid.Vector2(game.view.x + loc[0], game.view.y + loc[1])
            self.mouse_move = True

        if buttons[0]:
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

        if ( dx == 0 and dy == 0 and not self.mouse_move ):
            return

        if (self.mouse_move):
            mypos = euclid.Vector2(self.sprite.rect.x, self.sprite.rect.y)

            if movement.move(mypos, self.move_to, self.speed):
                self.mouse_move = False

            self.sprite.rect.x = mypos[0]
            self.sprite.rect.y = mypos[1]
        else:
            self.sprite.rect.x += dx * self.speed
            self.sprite.rect.y += dy * self.speed

        oldframe = int(self.frame)
        self.frame = (self.frame + 0.2) % len(self.frames)
        if oldframe != int(self.frame):
            self.sprite.setimage(self.frames[int(self.frame)])

        self.view_me(game)

    def view_me(self, game):
        # cheezy bounds enforcement
        bounds = pygame.Rect(game.bounds)
        bounds.inflate_ip(-self.sprite.rect.w, -self.sprite.rect.h)
        self.sprite.rect.clamp_ip(bounds)

        gx = self.sprite.rect.x - (game.view.w/2) + game.tile_w
        gy = self.sprite.rect.y - (game.view.h/2) + game.tile_h

        game.view.x = gx
        game.view.y = gy

    def fire(self, game, sprite):
        Bullet('shot', game, sprite)

    def learn(self, target):
        self.known_items.append(target)

    def morph(self):
        target = random.choice(self.known_items)

    def hit(self, game, sprite, other):
        push(sprite, other)
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
        self.waypoint = 0
        self.waypoints = []

        for pts in xrange(10):
            self.waypoints.append(euclid.Vector2(random.randint(10, game.bounds.width-10),random.randint(10, game.bounds.height-10)))

    def step(self, game, sprite):
        self.move(game)

    def move(self, game):
        myloc = euclid.Vector2(self.sprite.rect.x, self.sprite.rect.y)
        #target = euclid.Vector2(game.player.sprite.rect.x, game.player.sprite.rect.y)
        target = self.waypoints[self.waypoint]

        player_pos = euclid.Vector2(game.player.sprite.rect.x, game.player.sprite.rect.y)

        if visibility.can_be_seen(player_pos, myloc, target):
            game.player.seen = True

        if movement.move(myloc, target, 4):
            self.waypoint = (self.waypoint + 1) % len(self.waypoints)

        self.sprite.rect.x = myloc[0]
        self.sprite.rect.y = myloc[1]

    def hit(self, game, sprite, other):
        push(sprite, other)

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
            self.sprite.setimage(self.frames[int(self.frame)])

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
