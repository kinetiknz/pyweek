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

def add_a_balloon(base_pos, lvl):
    new = sprite.Balloon(lvl)
    new.position = base_pos + euclid.Vector2(random.randrange(250.0, 450.0), random.randrange(0.0, 150.0))
    display.sprite_list.append(new)

class SplashRunner(object):
    def run(self):
        pass

class MenuRunner(object):
    def __init__(self, levels):
        self.levels = levels

    def run(self):
        '''Display the game menu.  Return an index into self.levels to indicate where to start from.'''
        return 0

class GameEndRunner(object):
    def __init__(self, win):
        self.win = win

    def run(self):
        '''Display a win or lose graphic depending on self.win.  Return 2 to try
           playing again from the current level, 1 to return to the menu, and 0
           to quit the game.'''
        return 0

class LevelRunner(object):
    def __init__(self, name):
        self.name = name

    def run(self):
        '''Return True to indicate the level was beaten, False to indicate the player died.'''
        lvl = level.load_level(self.name)

        stick_guy      = player.Player(lvl, display.sprite_list)
        display.player = stick_guy
        display.lvl    = lvl

        display.sprite_list.append(stick_guy)

        # TODO: this should be set up by the level loader
        emit = sprite.Emitter(lvl, display.sprite_list)
        emit.position = stick_guy.position + euclid.Vector2(300.0, 200.0)
        display.sprite_list.append(emit)

        # TODO: this should be set up by the level loader
        launch = sprite.DartLauncher(lvl, display.sprite_list)
        launch.position = stick_guy.position + euclid.Vector2(0.0, 0.0)
        display.sprite_list.append(launch)

        # TODO: this should be set up by the level loader
        for i in xrange(0,20):
            add_a_balloon(stick_guy.position, lvl)

        timer = pygame.time.Clock()

        fps_limit = 1.0/60.0

        while 1:
            for e in pygame.event.get():
                if e.type == pygame.QUIT or \
                        e.type == pygame.KEYDOWN and \
                        e.key == pygame.K_ESCAPE:
                    sys.exit(0)

                if e.type == pygame.KEYUP:
                    if e.key == pygame.K_UP:
                        stick_guy.add_balloon()
                    elif e.key == pygame.K_DOWN:
                        stick_guy.drop_balloon()

            elapsed = timer.tick() / 1000.0

            # why not just use timer.tick(fps)?  good question.  it seems to eat
            # a lot more CPU than seems reasonable, almost as if it uses
            # pygame.time.delay rather than pygame.time.wait... but! the docs
            # say that only timer.tick_busy_loop() does this.  *shrug*
            if elapsed < fps_limit:
                dt = int((fps_limit - elapsed) * 1000)
                pygame.time.wait(dt)

            keys = pygame.key.get_pressed()

            if (keys[pygame.K_LEFT]):
                stick_guy.move_left()

            if (keys[pygame.K_RIGHT]):
                stick_guy.move_right()

            display.update(elapsed)

def main():
    levels = [LevelRunner("level_01"), LevelRunner("t001")]

    splash = SplashRunner()
    menu = MenuRunner(levels)

    splash.run()

    play = 1
    lastlevel = -1

    while play > 0:
        if play == 1:
            picked = menu.run()
            to_play = levels[picked:]
        else:
            to_play = levels[lastlevel:]

        # play from the selected level onwards...
        for level in to_play:
            display.sprite_list = []
            win = level.run()
            if win:
                lastlevel += 1
            else:
                break

        gameend = GameEndRunner(win)
        play = gameend.run()
