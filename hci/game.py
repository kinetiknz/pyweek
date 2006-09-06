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

from pygame.locals import *
import pygame
from pgu import tilevid

import splashscreen
import menu
import sprite

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
    ('player4', 'data/test/alien/alien-top5.png', (4, 4, 48, 24)),
    ('player5', 'data/test/alien/alien-top6.png', (4, 4, 48, 24)),
    ('saucer0', 'data/test/Saucer0.png', (4, 4, 192, 114)),
    ('saucer1', 'data/test/Saucer1.png', (4, 4, 192, 114)),
    ('saucer2', 'data/test/Saucer2.png', (4, 4, 192, 114)),
    ('enemy', 'data/test/enemy.png', (4, 4, 24, 24)),
    ('cow',   'data/test/Clareta.png', (1, 1, 30, 30)),
    ('warn',   'data/test/Warning.png', (0, 0, 16, 16)),
    ('shot', 'data/test/shot.png', (1, 2, 6, 4)),
    ('tree', 'data/test/treebiggersize.png', (20, 20, 95, 95)),
    ('bush', 'data/test/treepinkflower.png', (4, 4, 48, 48)),
    ]

cdata = {
    1: (lambda g, t, v: sprite.Player(g, t, v), None),
    2: (lambda g, t, v: sprite.Human(g, t, v), None),
    3: (lambda g, t, v: sprite.Bush(g, t, v), None),
    4: (lambda g, t, v: sprite.Tree(g, t, v), None),
    5: (lambda g, t, v: sprite.Saucer(g, t, v), None),
    }

tdata = {
    0x02: ('enemy,player', tile_block, {'top': 1, 'bottom': 1, 'left': 1, 'right': 1}),
    0x20: ('player', tile_coin, None),
    0x30: ('player', tile_fire, None),
    }

def run():
    initialize_modules()

    try:
        version = open('_MTN/revision').read().strip()
    except IOError, e:
        version = '?'

    game = tilevid.Tilevid()
    game.view.w = 640
    game.view.h = 480
    game.tile_w = 32
    game.tile_h = 32
    game.screen = pygame.display.set_mode([game.view.w, game.view.h])
    pygame.display.set_caption("PyWeek 3: The Disappearing Act [rev %.6s...]" % version)
    game.frame = 0

    game.tga_load_tiles('data/tilesets/testset.png', [game.tile_w, game.tile_h], tdata)
    game.tga_load_level('data/maps/beachhead.tga', True)
    game.bounds = pygame.Rect(game.tile_w, game.tile_h,
                              (len(game.tlayer[0])-2)*game.tile_w,
                              (len(game.tlayer)-2)*game.tile_h)

    game.load_images(idata)
    game.run_codes(cdata, (0, 0, len(game.tlayer[0]), len(game.tlayer)))

    splash_image = pygame.image.load('data/screens/splash.png')
    menu_image   = pygame.image.load('data/screens/menu.png')

    #splashscreen.fade_in(game.screen, splash_image)
    #pygame.time.wait(500)
    #splashscreen.fade_out(game.screen, splash_image)

    game.deferred_effects = []

    game.menu_font = pygame.font.Font('data/fonts/Another_.ttf', 36)
    selection = menu.show([game.view.w, game.view.h], game.screen, menu_image, game.menu_font)

    music = pygame.mixer.music
    music.load('data/music/Track01.ogg')
    music.play(-1,0.0)

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

        if game.pause:
            caption = "GAME PAUSED"
            music.pause()
            txt = text.render(caption, 1, [0, 0, 0])
            dx = game.view.w/2 - txt.get_rect().w/2
            dy = game.view.h/2 - txt.get_rect().h/2
            game.screen.blit(txt, [dx + 1, dy + 1])
            txt = text.render(caption, 1, [255, 255, 255])
            game.screen.blit(txt, [dx, dy])
            pygame.display.flip()
        else:
            music.unpause()
            if game.view.x == game.bounds.w - game.view.w + game.tile_w \
                   and direction == 1:
                direction = -1
            elif game.view.x == game.tile_w and direction == -1:
                direction = 1
            game.view.x += direction

            game.run_codes(cdata, (game.view.right/game.tile_w, 0, 1, 17))
            game.loop()

            game.paint(game.screen)

            for e in game.deferred_effects[:]:
                e()
                game.deferred_effects.remove(e)

            caption = "FPS %2.2f" % t.get_fps()
            txt = text.render(caption, 1, [0, 0, 0])
            game.screen.blit(txt, [1, game.view.w - txt.get_height() + 1])
            txt = text.render(caption, 1, [255, 255, 255])
            game.screen.blit(txt, [0, game.view.h - txt.get_height()])

            caption = "SCORE %05d" % game.player.sprite.score
            txt = text.render(caption, 1, [0, 0, 0])
            game.screen.blit(txt, [0, 0])
            txt = text.render(caption, 1, [255, 255, 255])
            game.screen.blit(txt, [1, 1])

            game.frame += 1
            pygame.display.flip()

        t.tick(60)

    return 0
