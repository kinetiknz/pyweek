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

if __name__ == '__main__':
    import sys
    sys.path.append('../thirdparty')

import euclid
import math


# mypos - a Vector2 of my location
# otherpos - a Vector2 of their location
# other_look_at - a Vector2 point that they are looking at
# view_angle - The angle in radians representing total width of their view cone
# view_distance2 - The maximum distance they can see (squared)
#
# returns True if my pos is within visible range

def can_be_seen(mypos, otherpos, other_look_at, view_angle = (math.pi/2.0), view_distance2 = 80000.0):
    assert isinstance(mypos, euclid.Vector2)
    assert isinstance(otherpos, euclid.Vector2)
    assert isinstance(other_look_at, euclid.Vector2)

    them2me = mypos - otherpos
    dist    = them2me.magnitude_squared()

    if (dist > view_distance2):
        return False

    them_look = other_look_at - otherpos
    them_look.normalize()
    them2me.normalize()

    if them_look == them2me: return True

    angle_between = math.acos(them2me.dot(them_look))


    if (angle_between > view_angle/2.0):
        return False

    return True

def run_test():
    me = euclid.Vector2(100,100)
    them = euclid.Vector2(120, 120)

    if can_be_seen(me, them, me):
        print('Test1 OK')
    else:
        print('Test1 Failed')

    lookat = euclid.Vector2(140, 140)

    if can_be_seen(me, them, lookat):
        print('Test2 Failed')
    else:
        print('Test2 OK')

    them = euclid.Vector2(210, 210)

    if can_be_seen(me, them, me):
        print('Test3 Failed')
    else:
        print('Test3 OK')

    if can_be_seen(euclid.Vector2(29,-30),euclid.Vector2(0,0), euclid.Vector2(0, -20)):
        print('Test4 OK')
    else:
        print('Test4 Failed')

    if can_be_seen(euclid.Vector2(-29,-30),euclid.Vector2(0,0), euclid.Vector2(0, -20)):
        print('Test5 OK')
    else:
        print('Test5 Failed')

    if can_be_seen(euclid.Vector2(31,-30),euclid.Vector2(0,0), euclid.Vector2(0, -20)):
        print('Test6 Failed')
    else:
        print('Test6 OK')

    if can_be_seen(euclid.Vector2(-31,-30),euclid.Vector2(0,0), euclid.Vector2(0, -20)):
        print('Test7 Failed')
    else:
        print('Test7 OK')

if __name__ == '__main__':
  run_test()
