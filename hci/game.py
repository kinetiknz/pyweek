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
import splashscreen
from pygame.locals import *
import pygame
from pgu import tilevid

def initialize_modules():
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

def player_new(g, t, value):
    g.clayer[t.ty][t.tx] = 0
    s = tilevid.Sprite(g.images['player'], t.rect)
    g.sprites.append(s)
    s.loop = player_loop
    s.groups = g.string2groups('player')
    s.score = 0
    s.shoot = player_shoot
    g.player = s

def player_loop(g, s):
    if s.rect.right < g.view.left: g.quit = 1
    s.rect.x += 1

    k = pygame.key.get_pressed()
    dx, dy = 0, 0
    if k[K_UP]: dy -= 1
    if k[K_DOWN]: dy += 1
    if k[K_LEFT]: dx -= 1
    if k[K_RIGHT]: dx += 1
    if k[K_SPACE] and g.frame % 8 == 0:
        shot_new(g, s, None)

    s.rect.x += dx * 5
    s.rect.y += dy * 5
    s.rect.clamp_ip(g.view)

def player_shoot(g, s):
    shot_new(g, s, None)

def shot_new(g, t, value):
    s = tilevid.Sprite(g.images['shot'], [t.rect.right, t.rect.centery - 2])
    g.sprites.append(s)
    s.agroups = g.string2groups('enemy')
    s.hit = shot_hit
    s.loop = shot_loop

def shot_loop(g, s):
    s.rect.x += 8
    if s.rect.left > g.view.right:
        g.sprites.remove(s)

def shot_hit(g, s, a):
    if a in g.sprites: g.sprites.remove(a)
    g.player.score += 500

def enemy_new(g, t, value):
    g.clayer[t.ty][t.tx] = 0
    s = tilevid.Sprite(g.images['enemy'], t.rect)
    g.sprites.append(s)
    s.loop = enemy_loop
    s.move = value['move']
    s.origin = pygame.Rect(s.rect)
    s.frame = g.frame
    s.groups = g.string2groups('enemy')
    s.agroups = g.string2groups('player')
    s.hit = enemy_hit

def enemy_hit(g, s, a):
    g.quit = 1

def enemy_loop(g, s):
    if s.rect.right < g.view.left:
        g.sprites.remove(s)
    s.move(g, s)

def enemy_move_line(g, s):
    s.rect.x -= 3

def enemy_move_sine(g, s):
    s.rect.x -= 2
    s.rect.y = s.origin.y + 65 * math.sin((g.frame - s.frame) / 10.0)

def enemy_move_circle(g, s):
    s.origin.x -= 1
    s.rect.y = s.origin.y + 50 * math.sin((g.frame - s.frame) / 10.0)
    s.rect.x = s.origin.x + 50 * math.sin((g.frame - s.frame) / 10.0)

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
    1: (player_new, None),
    2: (enemy_new, {'move': enemy_move_line}),
    3: (enemy_new, {'move': enemy_move_sine}),
    4: (enemy_new, {'move': enemy_move_circle}),
    }

tdata = {
    0x01: ('player', tile_block,
           {'top': 1, 'bottom': 1, 'left': 1, 'right': 1}),
    0x02: ('player', tile_block,
           {'top': 1, 'bottom': 1, 'left': 1, 'right': 1}),
    0x20: ('player', tile_coin, None),
    0x30: ('player', tile_fire, None),
    }

def run():
    initialize_modules()

    screen_w = 640
    screen_h = 480
    tile_w = 16
    tile_h = 16

    game = tilevid.Tilevid()
    game.screen = pygame.display.set_mode([screen_w, screen_h])
    game.view.w, game.view.h = screen_w, screen_h
    game.frame = 0

    game.tga_load_tiles('data/test/tiles.png', [tile_h, tile_w], tdata)
    game.tga_load_level('data/test/level.png')
    game.bounds = pygame.Rect(tile_w, tile_h,
                              (len(game.tlayer[0])-2)*tile_w,
                              (len(game.tlayer)-2)*tile_h)

    game.load_images(idata)
    game.run_codes(cdata, (0, 0, 25, 17))

    splash_image = pygame.image.load('data/screens/splash.png')
    splashscreen.fade_in(game.screen, splash_image)
    pygame.time.wait(1000)
    splashscreen.fade_out(game.screen, splash_image)

    t = pygame.time.Clock()

    game.quit = 0
    game.paint(game.screen)

    game.pause = 0

    stars = []
    for n in range(256):
        stars.append([random.randrange(0, screen_w),
                      random.randrange(0, screen_h),
                      random.randrange(2, 8)])

    text = pygame.font.Font(None, 36)

    direction = 1
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

            game.screen.fill([0, 0, 0])
            for n in range(256):
                x, y, s = stars[n]
                if (game.frame * s) % 8 < s:
                    x -= 1
                if x < 0: x += screen_w
                stars[n][0] = x
                r = random.randint
                ri = random.randint(100, 255)
                game.screen.set_at([x, y], [ri, ri, ri])

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

            game.frame += 1
            pygame.display.flip()

        t.tick(60)

    return 0
