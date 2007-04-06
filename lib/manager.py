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

'''Entity management module

Runs entity logic and rendering based on logic and render priority set on
entity.
'''

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
