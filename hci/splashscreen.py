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

def fade_in(display, image):
    alpha = image.get_alpha()
    
    for fade in range(0, 255, 2):
        display.fill([0, 0, 0])
        image.set_alpha(fade)
        display.blit(image, [0,0])
        pygame.display.flip()
        
    image.set_alpha(alpha)

def fade_out(display, image):
    alpha = image.get_alpha()
    
    for fade in range(255, 0, -5):
        display.fill([0, 0, 0])
        image.set_alpha(fade)
        display.blit(image, [0,0])
        pygame.display.flip()
        
    image.set_alpha(alpha)
