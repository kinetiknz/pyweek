#! /usr/bin/env python
#
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

import sys
import os
try:
    basename = os.path.dirname(__file__)
    libdir = os.path.abspath(os.path.join(basename, 'lib'))
    thirddir = os.path.abspath(os.path.join(basename, 'thirdparty'))
    sys.path.insert(0, libdir)
    sys.path.insert(0, thirddir)
except:
    pass

import main
main.main()
