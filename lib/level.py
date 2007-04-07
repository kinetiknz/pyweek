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

def rect_val(s):
    x,y,w,h  = s.split(',')
    return pygame.Rect(int(x), int(y), int(w), int(h))

class Level(object):
    def __init__(self, name):
        self.bg_path = util.filepath(name) + ".png"
        self.bg = util.load_image(self.bg_path)
        self.fg = util.load_image(util.filepath(name) + "_skin.png")
        self.bg_rect = self.bg.get_rect()

        self.fg_path = util.filepath(name) + ".dsc"
        kv = read_desc(open(self.fg_path, "r"))
        self.name = kv["name"]
        self.area = rect_val(kv["area"])
        self.solid = hex_val(kv["solid"])
        self.background = hex_val(kv["background"])
        self.spike = hex_val(kv["spike"])
        self.spawn = coord_val(kv["player"])

        self.wind_left = hex_val(kv["wind_left"])
        self.wind_right = hex_val(kv["wind_right"])
        self.wind = (self.wind_left, self.wind_right)

    def __str__(self):
        return "[Level \"%s\": 0x%06x/0x%06x (%d, %d)]" % (
            self.name, self.solid, self.background,
            self.spawn[0], self.spawn[1])

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

        # TODO: this check should be dealt with by designing the levels to
        # be surrounded by solid areas except where the player can escape.
        if (   rect.left < 0
             or rect.right >= self.bg_rect.width
             or rect.top < 0
             or rect.bottom >= self.bg_rect.height ):
            return self.solid

        # Just check the four corners for speed
        for x in xrange(rect.left, rect.right, rect.width / 3):
            for y in xrange(rect.top, rect.bottom, rect.height / 3):
                contents = self.check_point(x, y, contents)

        return contents

    def check_wind_point(self, x, y, contents):
        if contents in self.wind:
            return contents

        col = self.bg.get_at((x,y))
        col_as_int = (col[0] * 256 * 256) + (col[1] * 256) + col[2]
        if col_as_int in self.wind:
            return col_as_int
        else:
            return contents

    def check_wind(self, rect):
        contents = self.background

        # Just check the four corners for speed
        contents = self.check_wind_point(rect.left,  rect.top,    contents)
        contents = self.check_wind_point(rect.right, rect.top,    contents)
        contents = self.check_wind_point(rect.left,  rect.bottom, contents)
        contents = self.check_wind_point(rect.right, rect.bottom, contents)

        return contents

def bound_view(level, view):
    y = view[1]
    top = -level.area.top
    bottom = -(level.area.bottom - 480)

    if y < bottom:
        y = bottom
    if y > top:
        y = top
    view[1] = y

    x = view[0]
    left = -level.area.left
    right = -(level.area.right - 600)

    if x < right:
        x = right
    if x > left:
        x = left
    view[0] = x
