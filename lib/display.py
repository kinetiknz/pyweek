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
import player
import sprite
import level

pygame.init()

width  = 640
height = 480

screen = pygame.display.set_mode([width, height])
view   = [0, 0, 640, 480]

sprite_list = []
player      = None
lvl         = None

def update(seconds_elapsed):
    for s in sprite_list:
        s.move(seconds_elapsed)
        if s.alive():
            if isinstance(s, sprite.Dart):
                s.check_for_balloons(sprite_list)

    player.check_balloons(sprite_list)
    player.check_darts(sprite_list)

    view[1] = -player.position[1] + 400
    level.bound_view(lvl, view)
    
    screen.fill(0)
    screen.blit(lvl.fg, view)

    dead_sprites = filter(lambda s: not s.alive(), sprite_list)
    for dead in dead_sprites:
        sprite_list.remove(dead)

    for s in sprite_list:
        s.render(screen, view)

    pygame.display.flip()
