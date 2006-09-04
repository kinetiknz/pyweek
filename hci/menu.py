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
import splashscreen
from pygame.locals import *

menu_items   = [ 'One', 'Two','And another one']
selected     = 0
font_y_space = 10

def show(dispsize, display, bg_image, font):
    # splashscreen.fade_in(display, bg_image, 5)
    return 0

    if (not draw_items(dispsize, display, font)): return -1

    while 1:
        for e in pygame.event.get():
            if e.type is QUIT: return -1
            if e.type is KEYDOWN:
                if e.key == K_ESCAPE: return -1
                if e.key == K_F10: pygame.display.toggle_fullscreen()
                if e.key == K_RETURN:
                    return selected
    
def draw_items(dispsize, display, font):
    totalh = 0
    sizes = []
    
    for item in menu_items:
        the_size = font.size(item)
        the_rect = pygame.Rect(0,0,the_size[0],the_size[1])
        sizes.append(the_rect)
        totalh += the_rect.height
        totalh += font_y_space
        
    if (totalh > dispsize[1]): return False
    
    y_pos = (dispsize[1] - totalh)/2.0
    
    for i in xrange(len(menu_items)):
        font_surface = font.render(menu_items[i], True, [255,255,255])
        display.blit(font_surface, [dispsize[0]-sizes[i].width/2.0, y_pos])
        y_pos += sizes[i].height
        y_pos += font_y_space
        
    return True
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    