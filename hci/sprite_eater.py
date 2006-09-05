# Copyright (c) 2006 Matthew Gregan <kinetik@flim.org>
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
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

import pygame
import random

magic_colour_r = 0
magic_colour_g = 255
magic_colour_b = 0

magic_colour = [0,255,0]
transparent  = 0

class SpriteEater(object):
    def __init__(self, surface):
        self.surface = surface.copy()
        print self.surface.get_flags()
        self.surfarray = pygame.surfarray.array3d(surface)
        self.alphas    = pygame.surfarray.array_alpha(surface)
        self.width = surface.get_width()
        self.height = surface.get_height()

        self.points = []

        #surfarray = pygame.surfarray.pixels3d(self.surface)
        #alphas    = pygame.surfarray.pixels_alpha(self.surface)

        for i in xrange(20):
            pos = [random.randint(0,self.width-1), random.randint(0, self.height-1)]
            self.points.append(pos)
            self.zap(self.surfarray, pos)

    def blit_to(self, surface):
        #surface.blit(self.surface, (0,0))
        pygame.surfarray.blit_array(surface, self.surfarray)

        dst_alpha = pygame.surfarray.pixels_alpha(surface)
        for x in xrange(self.width):
            for y in xrange(self.height):
                dst_alpha[x][y] = self.alphas[x][y]

    def advance_frame(self):
        #surfarray = pygame.surfarray.pixels3d(self.surface)
        #alphas    = pygame.surfarray.pixels_alpha(self.surface)
        newlist = []

        print(len(self.points))

        for point in self.points:
            new_point = [point[0], point[1]]

            if self.walk(self.surfarray, self.alphas, new_point):
                self.zap(self.surfarray, new_point)
                newlist.append(new_point)
                newlist.append(point)
            else:
                self.alphas[point[0]][point[1]] = transparent

        self.points = newlist
        # pygame.surfarray.blit_array(self.surface, surfarray)

        return len(self.points) > 0

    def old_advance_frame(self):
        #surfarray = pygame.surfarray.pixels3d(self.surface)
        #alphas    = pygame.surfarray.pixels_alpha(self.surface)

        newlist = []

        for point in self.points:
            self.zap(self.surfarray, point)
            die = True

            x = point[0]-1
            y = point[1]

            if self.safe(self.surfarray, self.alphas, x,y):
                self.zap(self.surfarray, (x,y))
                newlist.append((x,y))
                die = False

            x = point[0]+1
            if self.safe(self.surfarray, self.alphas, x,y):
                self.zap(self.surfarray, (x,y))
                newlist.append((x,y))
                die = False

            x = point[0]
            y = point[1]-1
            if self.safe(self.surfarray, self.alphas, x,y):
                self.zap(self.surfarray, (x,y))
                newlist.append((x,y))
                die = False

            y = point[1]+1
            if self.safe(self.surfarray, self.alphas, x,y):
                self.zap(self.surfarray, (x,y))
                newlist.append((x,y))
                die = False

            y = point[1]

            if die:
                self.alphas[x][y] = transparent
            else:
                newlist.append(point)

        print(len(newlist))

        self.points = newlist

        return len(self.points) > 0

    def zap(self, surfarray, pos):
        surfarray[pos[0]][pos[1]][0] = magic_colour_r
        surfarray[pos[0]][pos[1]][1] = magic_colour_g
        surfarray[pos[0]][pos[1]][2] = magic_colour_b

    def safe(self, surfarray, alphas, x, y):
        if x < 0 or y < 0 or x >= self.width or y >= self.height: return False
        if alphas[x][y]    == transparent: return False
        if surfarray[x][y][0] != magic_colour_r: return True
        if surfarray[x][y][1] != magic_colour_g: return True
        if surfarray[x][y][2] != magic_colour_b: return True
        return False

    def walk(self, surfarray, alphas, pos):
        dir = random.randint(0,3)
        sdir = dir

        while 1:
            if dir == 0:
                y = pos[1]-1
                x = pos[0]
            elif dir == 1:
                y = pos[1]+1
                x = pos[0]
            elif dir == 2:
                x = pos[0]+1
                y = pos[1]
            else:
                x  = pos[0]-1
                y  = pos[1]

            if self.safe(surfarray, alphas, x,y):
                pos[0] = x
                pos[1] = y
                return True
            else:
                dir = (dir + 1) % 4

            if dir == sdir: return False
