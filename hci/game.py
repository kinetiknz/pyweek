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

def test_collision(obj1, obj2):
    r1, h1 = obj1.rect, obj1.hitmask
    r2, h2 = obj2.rect, obj2.hitmask

    r = r1.clip(r2)
    x1, y1 = r.x - r1.x, r.y - r1.y
    x2, y2 = r.x - r2.x, r.y - r2.y

    x = 0
    y = 0
    while 1:
        if h1[x + x1][y + y1]:
            if h2[x + x2][y + y2]:
                return True
        if h1[x1 - x][y1 - y]:
            if h2[x2 - x][y2 - y]:
                return True
        x += 1
        if x >= r.width:
            x = 0
            y += 1
            if y >= r.height/2:
                return False

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
        self.sprite.agroups = game.string2groups('Background')
        self.sprite.hit  = lambda game, sprite, other: self.hit(game, sprite, other)
        self.sprite.shoot = lambda game, sprite: self.fire(game, sprite)
        self.sprite.score = 0

        game.player = self

        self.known_items = []

    def step(self, game, sprite):
        key = pygame.key.get_pressed()

        dx, dy = 0, 0
        if key[K_UP]: dy -= 1
        if key[K_DOWN]: dy += 1
        if key[K_LEFT]: dx -= 1
        if key[K_RIGHT]: dx += 1
        if key[K_SPACE] and game.frame % 8 == 0:
            self.fire(game, sprite)
        if key[K_LSHIFT]: self.speed = 15
        else: self.speed = 5

        if (dx == 0 and dy == 0): return
        
        # get smart and give the player finer control over their movement
        # move them in x first and do a collide test. then do Y... 
        
        self.oldpos = (self.sprite.rect.x, self.sprite.rect.y)
        self.sprite.rect.x += dx * self.speed
        
        game.loop_spritehits()
    
        self.oldpos = (self.sprite.rect.x, self.sprite.rect.y)
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

        gx = self.sprite.rect.x - (game.view.w/2) + 32
        gy = self.sprite.rect.y - (game.view.h/2) + 32

        game.view.x = gx
        game.view.y = gy

    def fire(self, game, sprite):
        Bullet('shot', game, sprite)

    def learn(self, target):
        self.known_items.append(target)

    def morph(self):
        target = random.choice(self.known_items)
   
    def hit(self, game, sprite, other):
        if test_collision(self, other.backref):           
            self.sprite.rect.x, self.sprite.rect.y = self.oldpos
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

class Enemy(Sprite):
    def __init__(self, game, tile, values=None):
        super(Enemy, self).__init__('enemy', 'enemy', game, tile, values)
        self.sprite.agroups = game.string2groups('player')
        self.sprite.hit = lambda game, sprite, other: self.hit(game, sprite, other)

    def step(self, game, sprite):
        if self.sprite.rect.right < game.view.left:
            #game.sprites.remove(self.sprite)
            logit(self, 'would\'ve been removed')
        self.move()

    def move(self):
        self.sprite.rect.x -= 3

    def hit(self, game, sprite, other):
        logit(self, 'hit', other)

class Saucer(Sprite):
    def __init__(self, game, tile, values=None):
        super(Saucer, self).__init__('saucer0', 'Background', game, tile, values)
        self.frames.append(game.images['saucer1'])
        self.frames.append(game.images['saucer2'])

    def step(self, game, sprite):
        oldframe = int(self.frame)
        self.frame = (self.frame + 0.1) % len(self.frames)
        if oldframe != int(self.frame):
            self.sprite.setimage(self.frames[int(self.frame)])

    
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
    ('player', 'data/test/alien/alien-top.png', (4, 4, 48, 24)),
    ('player1', 'data/test/alien/alien-top2.png', (4, 4, 48, 24)),   
    ('player2', 'data/test/alien/alien-top3.png', (4, 4, 48, 24)),  
    ('player3', 'data/test/alien/alien-top4.png', (4, 4, 48, 24)),           
    ('saucer0', 'data/test/Saucer0.png', (4, 4, 192, 114)),
    ('saucer1', 'data/test/Saucer1.png', (4, 4, 192, 114)),
    ('saucer2', 'data/test/Saucer2.png', (4, 4, 192, 114)),
    ('enemy', 'data/test/enemy.png', (4, 4, 24, 24)),
    ('shot', 'data/test/shot.png', (1, 2, 6, 4))
    ]

cdata = {
    1: (lambda g, t, v: Player(g, t, v), None),
    #2: (lambda g, t, v: Enemy(g, t, v), None),
    #3: (lambda g, t, v: Enemy(g, t, v), None),
    #4: (lambda g, t, v: Enemy(g, t, v), None),
    5: (lambda g, t, v: Saucer(g, t, v), None),
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
    game.run_codes(cdata, (0, 0, len(game.tlayer[0]), len(game.tlayer)))

    splash_image = pygame.image.load('data/screens/splash.png')
    menu_image   = pygame.image.load('data/screens/menu.png')
    
    # splashscreen.fade_in(game.screen, splash_image)
    # pygame.time.wait(500)
    # splashscreen.fade_out(game.screen, splash_image)

    game.menu_font = pygame.font.Font('data/fonts/Another_.ttf', 36)
    selection = menu.show([screen_w, screen_h], game.screen, menu_image, game.menu_font)

    t = pygame.time.Clock()

    game.quit = 0
    game.paint(game.screen)

    game.pause = 0

    if selection == -1: game.quit = 1

    text = pygame.font.Font(None, 36)
    text_sm = pygame.font.Font(None, 16)

    game.player.view_me(game)

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

            caption = "SCORE %05d" % game.player.sprite.score
            txt = text.render(caption, 1, [0, 0, 0])
            game.screen.blit(txt, [0, 0])
            txt = text.render(caption, 1, [255, 255, 255])
            game.screen.blit(txt, [1, 1])

            game.frame += 1
            pygame.display.flip()

        t.tick(60)

    return 0
