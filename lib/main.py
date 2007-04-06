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

'''Game main module.

Contains the entry point used by the run_game.py script.

Feel free to put all your game code here, or in other modules in this "lib"
directory.
'''

import random
import pygame
import display
import player
import sprite
import level
import euclid
import sys

def add_a_balloon(guy, lvl):
    new = sprite.Balloon(lvl)
    new.position = guy.position + euclid.Vector2(random.randrange(250.0, 450.0), random.randrange(0.0, 150.0))
    display.sprite_list.append(new)

def main():
    lvl = level.load_level("t001")
    print lvl

    stick_guy      = player.Player(lvl, display.sprite_list)
    display.player = stick_guy
    display.level  = lvl


    display.sprite_list.append(stick_guy)

    emit = sprite.Emitter(lvl, display.sprite_list)
    emit.position = stick_guy.position + euclid.Vector2(300.0, 200.0)
    display.sprite_list.append(emit)

    launch = sprite.DartLauncher(lvl, display.sprite_list)
    launch.position = stick_guy.position + euclid.Vector2(0.0, 0.0)
    display.sprite_list.append(launch)



    for i in xrange(0,20):
        add_a_balloon(stick_guy, lvl)


    timer = pygame.time.Clock()

    while 1:
        for e in pygame.event.get():
            if e.type == pygame.QUIT or \
                    e.type == pygame.KEYDOWN and \
                    e.key == pygame.K_ESCAPE:
                sys.exit(0)

            if e.type == pygame.KEYUP:
                if e.key == pygame.K_UP:
                    stick_guy.add_balloon()
                if e.key == pygame.K_DOWN:
                    stick_guy.drop_balloon()

        elapsed = timer.tick() / 1000.0

        keys = pygame.key.get_pressed()

        if (keys[pygame.K_LEFT]):
            stick_guy.move_left()

        if (keys[pygame.K_RIGHT]):
            stick_guy.move_right()

        display.update(elapsed)
