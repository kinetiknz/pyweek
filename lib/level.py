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

'''Level loading module.

Loads level files (a bitmap image and associated description file).
'''

import pygame.image
import pygame.surface
import util

def load_level(level):
    return Level(level)

MIN_SUPPORTED = 1
MAX_SUPPORTED = 1

def read_desc(file):
    v, vi = file.readline().split("=", 1)
    v = v.strip()
    vi = int(vi)
    if v != "version" or vi < MIN_SUPPORTED or vi > MAX_SUPPORTED:
        raise Exception("unsupported level format")
    d = {}
    for l in file:
        l = l.strip()
        if len(l) == 0 or l[0] == "#":
            continue
        k, v = l.split("=", 1)
        k = k.strip()
        v = v.strip()
        d[k] = v
    return d

def hex_val(s):
    assert s[0] == "#"
    return int(s[1:], 16)

def coord_val(s):
    x, y = s.split(',', 1)
    return int(x), int(y)

class Level(object):
    def __init__(self, name):
        self.bg_path = util.filepath(name) + ".png"
        self.bg = util.load_image(self.bg_path)
        self.fg = util.load_image(util.filepath(name) + "_skin.png")
        self.bg_rect = self.bg.get_rect()

        self.fg_path = util.filepath(name) + ".dsc"
        kv = read_desc(open(self.fg_path, "r"))
        self.name = kv["name"]
        self.solid = hex_val(kv["solid"])
        self.background = hex_val(kv["background"])
        self.spike = hex_val(kv["spike"])
        self.spawn = coord_val(kv["player"])

    def __str__(self):
        return "[Level \"%s\": 0x%06x/0x%06x (%d, %d)]" % (
            self.name, self.solid, self.background,
            self.spawn[0], self.spawn[1])

    def view_player(self):
        """Return a rect with the view centered on the player."""
        return [self.spawn[0], self.spawn[1], 600, 480]

    def check_point(self, x,y, contents):
        if contents == self.spike:
            return contents

        col = self.bg.get_at((x,y))
        col_as_int = (col[0] * 256 * 256) + (col[1] * 256) + col[2]
        if (col_as_int == self.solid) and (contents != self.spike):
            return self.solid
        elif (col_as_int == self.spike):
            return self.spike
        else:
            return contents

    def check_area(self, rect):
        contents = self.background

        if (   rect.left < 0
             or rect.right >= self.bg_rect.width
             or rect.top < 0
             or rect.bottom >= self.bg_rect.height ):
            return self.solid

        # Just check the four corners for speed
        contents = self.check_point(rect.left,  rect.top,    contents)
        contents = self.check_point(rect.right, rect.top,    contents)
        contents = self.check_point(rect.left,  rect.bottom, contents)
        contents = self.check_point(rect.right, rect.bottom, contents)

        return contents


def bound_view(level, view):
    y = view[1]
    top = 0
    bottom = -(level.bg_rect.h - 480)
    if y < bottom:
        y = bottom
    if y > top:
        y = top
    view[1] = y

'''Some silly code for development and testing.'''
if __name__ == "no__main__":
    import sys
    import pygame
    pygame.init()
    screen = pygame.display.set_mode([640, 480])

    lvl = load_level("t001")
    print lvl

    view = lvl.view_player()

    move = 0

    while 1:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                sys.exit(0)
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    sys.exit(0)
                if e.key in (pygame.K_UP, pygame.K_DOWN):
                    if e.key == pygame.K_UP:
                        move = 5
                    else:
                        move = -5
            if e.type == pygame.KEYUP:
                if e.key in (pygame.K_UP, pygame.K_DOWN):
                    move = 0
        view[1] += move
        bound_view(lvl, view)
        screen.fill(0)
        screen.blit(lvl.bg, view)
        pygame.display.flip()

# while 1:
#  for events:
#    all.event(e)
# all.logic()
# all.render()

class Entity(object):
    def __init__(self, logic_priority=50, render_priority=50):
        self.logic_priority = logic_priority
        self.render_priority = render_priority
    @staticmethod
    def cmp_by_logic(lhs, rhs):
        return cmp(lhs.logic_priority, rhs.logic_priority)
    @staticmethod
    def cmp_by_render(lhs, rhs):
        return cmp(lhs.render_priority, rhs.render_priority)
    def __str__(self):
        return "%s(%d, %d)" % (
            self.__class__.__name__, self.logic_priority,
            self.render_priority)
    def event(self, event):
        print self, "event"
        pass
    def logic(self):
        print self, "logic"
        pass
    def render(self, surface):
        print self, "render"
        pass

class EntityManager(object):
    def __init__(self):
        self.entities = []
    def register(self, entity):
        self.entities.append(entity)
    def unregister(self, entity):
        self.entities.remove(entity)
    def _dispatch(self, event, cmp, *args):
        for entity in sorted(self.entities, cmp=cmp):
            if hasattr(entity, event):
                getattr(entity, event)(*args)
    def handle_events(self, event):
        self._dispatch("event", Entity.cmp_by_logic, event)
    def execute_logic(self):
        self._dispatch("logic", Entity.cmp_by_logic)
    def render(self, surface):
        self._dispatch("render", Entity.cmp_by_render, surface)

em = EntityManager()
em.register(Entity(20, 5))
em.register(Entity(15, 20))
em.register(Entity(1, 2))

em.handle_events(None)
em.render(None)
