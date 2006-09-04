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

import sys
import math
import random

from pygame.locals import *
import pygame
from pgu import tilevid

import splashscreen
import menu

def logit(*args):
    print args
    sys.stdout.flush()

def initialize_modules():
    '''Initialize PyGame modules.  If any modules fail, report all failures
    and exit the program.'''
    modules = (pygame.display, pygame.mixer, pygame.font)
    errors = []

    for m in modules:
        try:
            m.init()
        except pygame.error, e:
            errors.append(e)

    for e in errors:
        print >> sys.stderr, 'initialization failure: %s' %e

    if errors: sys.exit(1)

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
        self.groups = game.string2groups(self.group)

        if hasattr(tile, 'rect'):
            game.clayer[tile.ty][tile.tx] = 0
        game.sprites.append(self.sprite)

    def step(self, game, sprite):
        raise AbstractClassException

class Player(Sprite):
    def __init__(self, game, tile, values=None):
        super(Player, self).__init__('player', 'player', game, tile, values)
        self.sprite.score = 0
        self.sprite.shoot = lambda game, sprite: self.fire(game, sprite)

        game.player = self.sprite
        self.sprite.rect.x = 320
        self.sprite.rect.y = 240

    def step(self, game, sprite):
        key = pygame.key.get_pressed()

        dx, dy = 0, 0
        if key[K_UP]: dy -= 1
        if key[K_DOWN]: dy += 1
        if key[K_LEFT]: dx -= 1
        if key[K_RIGHT]: dx += 1
        if key[K_SPACE] and game.frame % 8 == 0:
            self.fire(game, sprite)
        if key[K_LSHIFT]: self.speed = 5
        else: self.speed = 2

        self.sprite.rect.x += dx * self.speed
        self.sprite.rect.y += dy * self.speed

        gx = self.sprite.rect.x - (game.view.w/2) + 32
        gy = self.sprite.rect.y - (game.view.h/2) + 32

        game.view.x = gx
        game.view.y = gy

    def fire(self, game, sprite):
        Bullet('shot', game, sprite)

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
        game.player.score += 500

class Enemy(Sprite):
    def __init__(self, game, tile, values=None):
        super(Enemy, self).__init__('enemy', 'enemy', game, tile, values)
        self.sprite.agroups = game.string2groups('player')
        self.sprite.hit = lambda game, sprite, other: self.hit(game, sprite, other)

    def step(self, game, sprite):
        if self.sprite.rect.right < game.view.left:
            game.sprites.remove(self.sprite)
        self.move()

    def move(self):
        s.rect.x -= 3

    def hit(self, game, sprite, other):
        logit(self, 'hit', other)

def tile_block(g, t, a):
    c = t.config
    if c['top'] == 1 and a._rect.bottom <= t._rect.top \
           and a.rect.bottom > t.rect.top:
        a.rect.bottom = t.rect.top
    if c['left'] == 1 and a._rect.right <= t._rect.left \
           and a.rect.right > t.rect.left:
        a.rect.right = t.rect.left
    if c['right'] == 1 and a._rect.left >= t._rect.right \
           and a.rect.left < t.rect.right:
        a.rect.left = t.rect.right
    if c['bottom'] == 1 and a._rect.top >= t._rect.bottom \
           and a.rect.top < t.rect.bottom:
        a.rect.top = t.rect.bottom

def tile_coin(g, t, a):
    a.score += 100
    g.set([t.tx, t.ty], 0)

def tile_fire(g, t, a):
    g.quit = 1

idata = [
    ('player', 'data/test/player.png', (4, 4, 24, 24)),
    ('enemy', 'data/test/enemy.png', (4, 4, 24, 24)),
    ('shot', 'data/test/shot.png', (1, 2, 6, 4))
    ]

cdata = {
    1: (lambda g, t, v: Player(g, t, v), None),
    2: (lambda g, t, v: Enemy(g, t, v), None),
    3: (lambda g, t, v: Enemy(g, t, v), None),
    4: (lambda g, t, v: Enemy(g, t, v), None),
    }

tdata = {
#    0x01: ('player', tile_block,
#           {'top': 1, 'bottom': 1, 'left': 1, 'right': 1}),
    0x02: ('player', tile_block,
           {'top': 1, 'bottom': 1, 'left': 1, 'right': 1}),
    0x20: ('player', tile_coin, None),
    0x30: ('player', tile_fire, None),
    }

def run():
    initialize_modules()

    screen_w = 640
    screen_h = 480
    tile_w = 32
    tile_h = 32

    game = tilevid.Tilevid()
    game.screen = pygame.display.set_mode([screen_w, screen_h])
    game.view.w, game.view.h = screen_w, screen_h
    game.frame = 0

    game.tga_load_tiles('data/tilesets/testset.png', [tile_h, tile_w], tdata)
    game.tga_load_level('data/maps/beachhead.tga', True)
    game.bounds = pygame.Rect(tile_w, tile_h,
                              (len(game.tlayer[0])-2)*tile_w,
                              (len(game.tlayer)-2)*tile_h)

    game.load_images(idata)
    game.run_codes(cdata, (0, 0, 25, 17))

    splash_image = pygame.image.load('data/screens/splash.png')
    #splashscreen.fade_in(game.screen, splash_image)
    #pygame.time.wait(1000)
    #splashscreen.fade_out(game.screen, splash_image)

    game.menu_font = pygame.font.Font('data/fonts/analgesics.ttf', 36)
    selection = menu.show([screen_w, screen_h], game.screen, splash_image, game.menu_font)

    t = pygame.time.Clock()

    game.quit = 0
    game.paint(game.screen)

    game.pause = 0

    if selection == -1: game.quit = 1

    text = pygame.font.Font(None, 36)
    text_sm = pygame.font.Font(None, 16)

    direction = 0
    while not game.quit:
        for e in pygame.event.get():
            if e.type is QUIT: game.quit = 1
            if e.type is KEYDOWN:
                if e.key == K_ESCAPE: game.quit = 1
                if e.key == K_F10: pygame.display.toggle_fullscreen()
                if e.key == K_RETURN: game.pause = not game.pause

        if not game.pause:
            if game.view.x == game.bounds.w - screen_w + tile_w \
                   and direction == 1:
                direction = -1
            elif game.view.x == tile_w and direction == -1:
                direction = 1
            game.view.x += direction

            game.run_codes(cdata, (game.view.right/tile_w, 0, 1, 17))
            game.loop()

            game.paint(game.screen)

            caption = "FPS %2.2f" % t.get_fps()
            txt = text.render(caption, 1, [0, 0, 0])
            game.screen.blit(txt, [1, screen_h - txt.get_height() + 1])
            txt = text.render(caption, 1, [255, 255, 255])
            game.screen.blit(txt, [0, screen_h - txt.get_height()])

            caption = "SCORE %05d" % game.player.score
            txt = text.render(caption, 1, [0, 0, 0])
            game.screen.blit(txt, [0, 0])
            txt = text.render(caption, 1, [255, 255, 255])
            game.screen.blit(txt, [1, 1])

            caption = "view %r, player %r, world bounds %r" % (game.view, game.player.rect, game.bounds)
            txt = text_sm.render(caption, 1, [0, 0, 0])
            game.screen.blit(txt, [0, 240])

            game.frame += 1
            pygame.display.flip()

        t.tick(60)

    return 0
