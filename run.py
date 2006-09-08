#! /usr/bin/env python

# Copyright (c) 2006 Matthew Gregan <kinetik@flim.org>
#                    Joseph Miller  <joff@goolehax.com>
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
try:
    import pygame
except ImportError, e:
    print >> sys.stderr, "fatal: %s. " % e
    sys.exit(1)

sys.path.append('thirdparty')

from hci import game

if len(sys.argv) > 1:
    if sys.argv[1] == '--profile':
        import hotshot, hotshot.stats
        prof = hotshot.Profile('game.prof')
        prof.runcall(game.run)
        prof.close()
        stats = hotshot.stats.load('game.prof')
        stats.strip_dirs()
        stats.sort_stats('time', 'calls')
        stats.print_stats(20)
    elif sys.argv[1] == '--psyco':
        import psyco
        psyco.full()
        game.run()
else:
    game.run()
