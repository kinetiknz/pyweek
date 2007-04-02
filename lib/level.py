#! /usr/bin/env python
'''Level loading module.

Loads level files (a bitmap image and associated description file).
'''

import pygame.image as img
import pygame.surface as srf
import data

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
        self.bg_path = data.filepath(name) + ".png"
        self.bg = img.load(self.bg_path)
        self.bg = srf.Surface.convert(self.bg)
        self.bg_rect = self.bg.get_rect()

        self.fg_path = data.filepath(name) + ".dsc"
        kv = read_desc(open(self.fg_path, "r"))
        self.name = kv["name"]
        self.solid = hex_val(kv["solid"])
        self.background = hex_val(kv["background"])
        self.spawn = coord_val(kv["player"])

    def __str__(self):
        return "[Level \"%s\": 0x%06x/0x%06x (%d, %d)]" % (
            self.name, self.solid, self.background,
            self.spawn[0], self.spawn[1])
        
    def area_is_bg(self, rect_to_check):
        if (   rect_to_check.left < 0 
            or rect_to_check.right > self.bg_rect.width
            or rect_to_check.top < 0 
            or rect_to_check.bottom > self.bg_rect.height ):
            return False
        
        for x in xrange(rect_to_check.left, rect_to_check.right):
            for y in xrange(rect_to_check.top, rect_to_check.bottom):
                col = self.bg.get_at((x,y))
                col_as_int = (col[0] * 256 * 256) + (col[1] * 256) + col[2]
                if (col_as_int == self.solid):
                    return False
        return True

'''Some silly code for development and testing.'''
if __name__ == "__main__":
    import sys
    import pygame
    pygame.init()
    screen = pygame.display.set_mode([640, 480])

    lvl = load_level("t001")
    print lvl

    view = [20, 0, 600, 480]

    dir = -1

    while 1:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                sys.exit(0)
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                sys.exit(0)
        screen.fill(0)
        screen.blit(lvl.bg, view)
        pygame.display.flip()
        view[1] += dir
        if view[1] == -(lvl.bg_rect.h - 480) or view[1] == 0:
            dir = -dir
