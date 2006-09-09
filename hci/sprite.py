# Copyright (c) 2006 Matthew Gregan <kinetik@flim.org>
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

import random
import time
import math
import cPickle

from pygame.locals import *
import pygame
from pgu import tilevid, algo, vid
import euclid
import movement
import sprite_eater
import visibility

def VectorToDegrees(vec):
    if vec.magnitude_squared() == 0.0: return 0.0
    ang = 180.0 - math.atan2(vec[0], vec[1]) * 360.0 / (2.0 * math.pi)
    if ang < 0.0: ang += 360.0
    ang = math.fmod(ang, 360.0)
    return ang

def DegreesToVector(ang):
    ang /= 180.0
    ang *= math.pi
    return euclid.Vector2(math.sin(ang), -math.cos(ang))

class Sprite(object):
    MIN_MOVEMENT_SQ = 0.1

    def __init__(self, name, group, game, tile, values=None):
        self.name = name
        self.group = group
        rect = tile
        if hasattr(tile, 'rect'):
            rect = tile.rect
        self.sprite = tilevid.Sprite(game.images[self.name], rect)
        self.sprite.loop = self.step
        self.sprite.groups = game.string2groups(self.group)
        self.hitmask = pygame.surfarray.array_alpha(self.sprite.image)
        self.sprite.backref = self
        self.bounds = pygame.Rect(game.bounds)
        self.bounds.inflate_ip(-self.sprite.rect.w * 2, -self.sprite.rect.h * 2)
        self.trophy = False

        # size/rotation
        self.orig_image   = self.sprite.image
        self.orig_shape   = self.sprite.shape
        self.scale_factor = 1.0
        self.rotation     = 0.0

        # animation
        self.dir_func = self.direction4
        self.frame = 0.0
        self.frames = { ' ': ([]),
                        'u': ([]),
                        'd': ([]),
                        'l': ([]),
                        'r': ([]),
                        'ur': ([]),
                        'dr': ([]),
                        'ul': ([]),
                        'dl': ([]), }
        self.frames[' '].append(game.images[self.name])

        # movement
        self.last_pos  = euclid.Vector2(0, 0)
        self.position  = euclid.Vector2(0, 0)
        self.get_sprite_pos()
        self.stop()
        self.accel     = 0.0
        self.drag      = 0.85
        self.top_speed = 0.0
        self.target    = None
        self.waypoint = 0
        self.waypoints = []
        if values:
            self.load_path(values[0])
            values = values[1:]

        # something to do with PGU?
        if hasattr(tile, 'rect'):
            game.clayer[tile.ty][tile.tx] = 0
        game.sprites.append(self.sprite)

    def set_scale(self, new_scale_factor):
        self.scale_factor = new_scale_factor
        self.reimage()

    def set_rotation(self, new_rotation):
        self.rotation = new_rotation
        self.reimage()

    def scale(self, scale_factor):
        self.scale_factor *= scale_factor
        self.reimage()

    def rotate(self, rotation):
        self.rotation += rotation
        self.reimage()

    def reimage(self):
        if (self.scale_factor == 1.0 and self.rotation == 0.0):
            self.sprite.setimage((self.orig_image, self.orig_shape))
            return

        newshape = self.orig_shape.inflate(0, 0)

        if self.scale_factor != 1.0:
            newshape.width *= self.scale_factor
            newshape.height *= self.scale_factor

        oldc = self.sprite.rect.center
        newsurf = pygame.transform.rotozoom(self.orig_image, self.rotation, self.scale_factor)
        self.sprite.setimage((newsurf, newshape))
        self.sprite.rect.center = oldc

    def set_image(self, new_image):
        oldc = self.sprite.rect.center
        self.sprite.setimage(new_image)
        self.sprite.rect.center = oldc

        self.orig_image = self.sprite.image
        self.orig_shape = self.sprite.shape
        self.reimage()

    def get_image(self):
        return self.orig_image

    def get_sprite_pos(self):
        self.position[0] = self.sprite.rect.centerx
        self.position[1] = self.sprite.rect.centery

    def set_sprite_pos(self):
        self.sprite.rect.centerx = self.position[0]
        self.sprite.rect.centery = self.position[1]

    def stop(self):
        self.last_pos[0] = self.position[0]
        self.last_pos[1] = self.position[1]
        #self.waypoint = 0
        #self.waypoints = []

    def accelerate(self, vector):
        move_vec = self.velocity() + vector

        if move_vec.magnitude() > self.top_speed:
            move_vec.normalize()
            move_vec *= self.top_speed

        self.position = self.last_pos + move_vec

    def move_toward(self, target, speed, min_distance):
        to_target = target - self.position
        length = to_target.magnitude()

        if (length <= min_distance):
            return True

        to_target /= length
        to_target *= speed
        self.accelerate(to_target)

        return False

    def velocity(self):
        return self.position - self.last_pos

    def direction4(self):
        vel = self.velocity()
        ang = VectorToDegrees(vel)

        if ang >= 315.0 or  ang < 45.0:  return 'u'
        if ang < 135.0: return 'r'
        if ang < 225.0: return 'd'
        if ang < 315.0: return 'l'

        assert(False)

    def direction8(self):
        vel = self.velocity()
        ang = VectorToDegrees(vel)

        if ang >= 337.5 or  ang < 22.5:  return 'u'
        if ang < 67.5:  return 'ur'
        if ang < 112.5: return 'r'
        if ang < 157.5: return 'dr'
        if ang < 202.5: return 'd'
        if ang < 247.5: return 'dl'
        if ang < 292.5: return 'l'
        if ang < 337.5: return 'ul'

        assert(False)

    def moving(self):
        return self.velocity.magnitude_squared() >= self.MIN_MOVEMENT_SQ

    def verlet_move(self, check_bounds = True):
        # use verlet integration to move our sprite
        move_vec = self.velocity()

        if move_vec.magnitude_squared() < self.MIN_MOVEMENT_SQ:
            return False

        move_vec *= self.drag

        if check_bounds:
            if self.position[0] < self.bounds.left:    self.position[0] = self.bounds.left
            if self.position[0] > self.bounds.right:   self.position[0] = self.bounds.right
            if self.position[1] < self.bounds.top:     self.position[1] = self.bounds.top
            if self.position[1] > self.bounds.bottom:  self.position[1] = self.bounds.bottom

        self.last_pos = self.position
        self.position = self.last_pos + move_vec
        self.set_sprite_pos()

        return True

    def view_me(self, game):
        gx = self.position[0] - (game.view.w/2) + game.tile_w
        gy = self.position[1] - (game.view.h/2) + game.tile_h

        game.view.x = gx
        game.view.y = gy

    def load_path(self, pathname):
        file = open('data/paths/' + pathname, 'r')
        path = cPickle.load(file)
        for x, y in path:
            self.waypoints.append(euclid.Vector2(x, y))
        self.target = self.waypoints[0]

    def animate(self, step):
        dir = self.dir_func()
        if (len(self.frames[dir]) == 0):
            dir = ' '

        oldframe = int(self.frame)
        self.frame = (self.frame + step) % len(self.frames[dir])
        if oldframe != int(self.frame):
            self.set_image(self.frames[dir][int(self.frame)])

    def step(self, game, sprite):
        if self.trophy:
            relx = self.position[0]  - (game.images['trophy'][0].get_width()/2)
            rely = self.sprite.rect.y  - (game.images['trophy'][0].get_height())
            game.deferred_effects.append(lambda: game.screen.blit(game.images['trophy'][0], (relx- game.view.x, rely-game.view.y, 0, 0)))

    def get_sucked(self):
        return

class Player(Sprite):
    def __init__(self, game, tile, values=None):
        super(Player, self).__init__('player_u1', 'player', game, tile, values)
        self.frames['u'].append(game.images['player_u1'])
        self.frames['u'].append(game.images['player_u2'])
        self.frames['u'].append(game.images['player_u3'])
        self.frames['u'].append(game.images['player_u4'])
        self.frames['d'].append(game.images['player_d1'])
        self.frames['d'].append(game.images['player_d2'])
        self.frames['d'].append(game.images['player_d3'])
        self.frames['d'].append(game.images['player_d4'])
        self.frames['l'].append(game.images['player_l1'])
        self.frames['l'].append(game.images['player_l2'])
        self.frames['l'].append(game.images['player_l3'])
        self.frames['l'].append(game.images['player_l4'])
        self.frames['r'].append(game.images['player_r1'])
        self.frames['r'].append(game.images['player_r2'])
        self.frames['r'].append(game.images['player_r3'])
        self.frames['r'].append(game.images['player_r4'])

        self.sprite.agroups = game.string2groups('Background,animal,farmer,fbi')
        self.sprite.hit  = self.hit
        self.sprite.score = 0
        self.gun_pos = {' ': euclid.Vector2(0.0, 0.0),
                        'r': euclid.Vector2(7.0, 21.0),
                        'l': euclid.Vector2(0.0, 21.0),
                        'u': euclid.Vector2(-12.0, 18.0),
                        'd': euclid.Vector2(11.0, 20.0),
                        }
        self.recording = False
        self.seen = False
        self.mouse_move = False
        self.speed = 1.0
        self.top_speed = 5.0
        self.suck_target = None
        self.impersonating = None
        self.lvl_complete = False
        self.last_sweat_drop = None

        self.state = 'landing'
        self.set_image(game.images['none'])
        Saucer(game, tile, values)

        game.player = self

        self.known_items = []
        

        self.walking_sound = pygame.mixer.Sound('data/sfx/Walking.ogg')
        self.walking_sound.set_volume(0.5)

        self.morph_sound   = pygame.mixer.Sound('data/sfx/Morph.ogg')
        self.unmorph_sound = pygame.mixer.Sound('data/sfx/MorphBack.ogg')
        self.beam_sound    = pygame.mixer.Sound('data/sfx/Beam.ogg')
        self.walking_sound_isplaying = False

    def landed(self, game):
        self.state = 'normal'
        self.set_image(self.frames[' '][int(self.frame)])

    def gun_dir(self):
        xn = self.direction4()
        if xn not in self.gun_pos:
            xn = ' '
        return xn

    def suck(self, game):
        if self.suck_target:
            self.suck_target.stop()
            self.suck_target.speed = 0.0
            self.suck_target.top_speed = 0.0
            self.suck_target.waypoints = []
            self.suck_target.waypoint = 0
            self.suck_target.target = None
            self.suck_target.trophy = False
            self.suck_target.get_sucked()

        if self.suck_progress >= 1.0:
            if self.suck_target:
                self.learn(self.suck_target)
                game.sprites.remove(self.suck_target.sprite)
            self.suck_target = None
            self.state = 'normal'
            self.beam_sound.stop()

            lvl_complete = True
            for s in game.sprites:
                if s.backref.trophy:
                    lvl_complete = False
            if lvl_complete:
                self.lvl_complete = True
            return

        gun_pos = euclid.Vector2(self.position[0], self.position[1]) + self.gun_pos[self.gun_dir()]

        loc = [self.suck_target_pos[0], \
               self.suck_target_pos[1] ]

        if self.suck_target:
            self.suck_target.set_rotation(720.0 * self.suck_progress)
            self.suck_target.set_scale(0.1 + (0.9*(1.0-self.suck_progress)))

            vec = self.suck_target.position - gun_pos
            vec.normalize()
            vec *= ((1.0-self.suck_progress) * self.suck_distance)
            self.suck_target.position = gun_pos + vec
            self.suck_target.set_sprite_pos()

            loc = [self.suck_target.position[0], \
                   self.suck_target.position[1] ]

        # ugly ray gun effect
        relx = gun_pos[0] - game.view.x
        rely = gun_pos[1] - game.view.y

        ln = algo.getline([relx, rely], [loc[0]-game.view.x,loc[1]-game.view.y])
        for l in xrange(0, len(ln), 7):
            def draw():
                c = [0, random.randint(0, 255), 255]
                r = [relx, rely]
                rx = random.randint(-5, 5)
                ry = random.randint(-5, 5)
                p = ln[l][0] + rx, ln[l][1] + ry
                def proc():
                    pygame.draw.line(game.screen, c, r, p, 2)
                return proc

            game.deferred_effects.append(draw())

        for l in xrange(10):
            rsx = random.gauss(0, 7) + loc[0]
            rsy = random.gauss(0, 7) + loc[1]
            game.deferred_effects.append(lambda: game.screen.blit(game.images['laser'][0], ( rsx - game.view.x, rsy - game.view.y, 0, 0)))
        self.suck_progress += 0.02

    def step(self, game, sprite):
        if self.state == 'landing':
            self.view_me(game)
            return
        
        if not self.last_sweat_drop or (self.position - self.last_sweat_drop.position).magnitude() > 50.0:
            drop = SweatDrop(game, (self.position[0], self.position[1]))
            if self.last_sweat_drop: self.last_sweat_drop.next = drop
            self.last_sweat_drop = drop

        game.deferred_effects.append(lambda: self.draw_morph_targets(game))

        key = pygame.key.get_pressed()

        if self.seen:
            # relx = self.position[0] - game.view.x - (game.images['warn'][0].get_width()/2)
            # rely = self.position[1] - game.view.y - (game.images['warn'][0].get_height()/2)
            # game.deferred_effects.append(lambda: game.screen.blit(game.images['warn'][0], (relx, rely, 0, 0)))
            self.seen = False

        if self.state == 'sucking':
            self.suck(game)

        dx, dy = 0, 0
        if key[K_w] or key[K_UP]: dy -= 1
        if key[K_s] or key[K_DOWN]: dy += 1
        if key[K_a] or key[K_LEFT]: dx -= 1
        if key[K_d] or key[K_RIGHT]: dx += 1
        if key[K_LSHIFT]:
            self.top_speed = 15.0
            self.speed     = 3.0
        else:
            self.top_speed = 5.0
            self.speed     = 1.0

        if key[K_f]:
            loc = pygame.mouse.get_pos()
            click_pos = euclid.Vector2(loc[0] + game.view.x, loc[1] + game.view.y)
            StationaryCow(game, (click_pos[0], click_pos[1]), None)

        if self.impersonating:
            self.set_image(self.impersonating.get_image())
            return

        buttons = pygame.mouse.get_pressed()
        loc = pygame.mouse.get_pos()

        if (dx != 0 or dy != 0):
            self.mouse_move = False
            if not self.walking_sound_isplaying:
                 self.walking_sound.play(-1)
                 self.walking_sound_isplaying = True

        if (dx == 0 and dy == 0):
            if self.walking_sound_isplaying:
                self.walking_sound.stop()
                self.walking_sound_isplaying = False

        if buttons[0]:
            self.target = euclid.Vector2(game.view.x + loc[0], game.view.y + loc[1])
            self.mouse_move = True
            if self.recording: self.recorded_path.append(self.target)

        if buttons[2] and not self.state == 'sucking':
            loc       = pygame.mouse.get_pos()
            click_pos = euclid.Vector2(loc[0]+game.view.x, loc[1]+game.view.y)
            gun_pos   = self.position + self.gun_pos[self.gun_dir()]

            #def s2t(x, y):
            #    stx = x / game.tile_w
            #    sty = y / game.tile_h
            #    return stx, sty

            # find selected tile
            # tx, ty = s2t(game.view.x + loc[0], game.view.y + loc[1])
            #game.set([tx, ty], 2)

            me_to_click       = click_pos - gun_pos
            distance_to_click = me_to_click.magnitude()

            if distance_to_click > 120.0:
                me_to_click /= (distance_to_click)
                me_to_click *= 120.0
                click_pos    = gun_pos + me_to_click

            self.state = 'sucking'
            self.suck_progress = 0.0
            self.beam_sound.play()
            self.suck_distance = (click_pos - gun_pos).magnitude()
            self.suck_target_pos = click_pos
            self.suck_target = None

            # ugly ray gun logic
            SelectionTest(game, (click_pos[0], click_pos[1]), None)

        if self.mouse_move:
            if self.move_toward(self.target, self.speed, 10.0):
                self.mouse_move = False
        else:
            self.accelerate(euclid.Vector2(dx*self.speed, dy*self.speed))

        if not self.verlet_move():
            self.mouse_move = False
            self.walking_sound.stop()
            return

        self.animate(0.2)
        self.view_me(game)

    def learn(self, target):
        self.known_items.append(target)

    def morph(self):
        if not self.impersonating and len(self.known_items) == 0:
            return
        if not self.impersonating:
            self.impersonating = random.choice(self.known_items)
            self.state = 'cloaked'
            self.stop()
            self.known_items.remove(self.impersonating)
            self.morph_sound.play()
        else:
            self.unmorph_sound.play()
            self.set_image(self.frames[' '][0])
            self.impersonating = None

    def cloaked(self):
        if self.impersonating:
            return True
        if self.state == 'landing':
            return True
        return False

    def draw_morph_targets(self, game):
        scale_to = 32.0
        x, y = game.view.w - scale_to, 0
        for t in self.known_items:
            def draw():
                dx = x
                dy = y
                sx, sy = scale_to, scale_to
                rect = t.get_image().get_rect()
                sx = float(rect.w / scale_to)
                sy = float(rect.h / scale_to)
                if sx == sy:
                    sx = 1.0
                    sy = 1.0
                elif sx > sy:
                    sy /= sx
                    sx = 1.0
                elif sy > sx:
                    sx /= sy
                    sy = 1.0
                sx = int(sx * scale_to)
                sy = int(sy * scale_to)
                img = pygame.transform.scale(t.get_image(), (sx, sy))
                def proc():
                    game.screen.blit(img, (dx, dy, scale_to, scale_to))
                return proc
            game.deferred_effects.append(draw())
            y += scale_to

    def hit(self, game, sprite, other):
        if self.suck_target and other is self.suck_target.sprite:
            return

        if other.backref.group == 'fbi':
            game.game_over = True

        push(sprite, other)
        self.get_sprite_pos()
        self.view_me(game)
        self.stop()

class Bullet(Sprite):
    def __init__(self, name, game, tile, values=None):
        origin = [tile.rect.right, tile.rect.centery - 2]
        super(Bullet, self).__init__(name, 'shot', game, origin, values)
        self.sprite.agroups = game.string2groups('enemy')
        self.sprite.hit = self.hit

    def step(self, game, sprite):
        self.sprite.rect.x += 8
        if self.sprite.rect.left > game.view.right:
            game.sprites.remove(self.sprite)

    def hit(self, game, sprite, other):
        if other in game.sprites:
            game.sprites.remove(other)
        game.player.sprite.score += 500

class Human(Sprite):
    def __init__(self, image, group, game, tile, values=None):
        super(Human, self).__init__(image, group, game, tile, values)
        self.sprite.agroups = game.string2groups('Background,farmer,animal')
        self.sprite.hit = self.hit
        self.speed = 0.0
        self.top_speed = 0.0
        self.seen_count = 0
        self.target = None
        self.sound_sucked_scream = pygame.mixer.Sound('data/sfx/Wilhelm-Long.ogg')
        self.sound_spotted_scream = pygame.mixer.Sound('data/sfx/Wilhelm.ogg')
        self.sound_spotted_scream.set_volume(0.25)

    def step(self, game, sprite):
        if not game.player.cloaked() and self.target and \
               visibility.can_be_seen(game.player.position, self.position, self.target):
            if self.seen_count == 0:
                game.player.seen = True
                self.seen_count = 60
                self.seen_alien(game)
            self.seeing_alien(game)
        else:
            self.not_seeing_alien()

            if self.seen_count > 0:
                self.seen_count = 0
                self.lost_alien(game)

        self.move(game)

    def lost_alien(self, game):
        pass

    def seen_alien(self, game):
        pass

    def not_seeing_alien(self):
        pass

    def seeing_alien(self, game):
        game.player_last_seen = game.player.position
        if self.seen_count > 1:
            relx = self.position[0] - (game.images['warn'][0].get_width()/2)
            rely = self.sprite.rect.y  - (game.images['warn'][0].get_height()) - 5
            game.deferred_effects.append(lambda: game.screen.blit(game.images['warn'][0], (relx - game.view.x, rely - game.view.y, 0, 0)))
            self.seen_count -= 1

    def reached_target(self):
        pass

    def move_blocked(self):
        pass

    def move(self, game):
        got_there = False

        if self.target:
            if self.move_toward(self.target, self.speed, 40.0):
                self.reached_target()
                got_there = True

        if not self.verlet_move() and not got_there:
            self.move_blocked()

        self.set_sprite_pos()

    def hit(self, game, sprite, other):
        push(sprite, other)
        self.get_sprite_pos()

    def get_sucked(self):
        self.sound_sucked_scream.play()

class FBI(Human):
    def __init__(self, game, tile, values=None):
        super(FBI, self).__init__('fbi_d1', 'fbi', game, tile, values)
        self.sprite.agroups = game.string2groups('Background,farmer,player,animal,sweatdrop')
        self.frames['d'].append(game.images['fbi_d1'])
        self.frames['d'].append(game.images['fbi_d2'])
        self.frames['u'].append(game.images['fbi_u1'])
        self.frames['u'].append(game.images['fbi_u2'])
        self.frames['l'].append(game.images['fbi_l1'])
        self.frames['l'].append(game.images['fbi_l2'])
        self.frames['r'].append(game.images['fbi_r1'])
        self.frames['r'].append(game.images['fbi_r2'])
        self.speed = 2.0
        self.top_speed = 4.0
        self.target = None

    def seeing_alien(self, game):
        super(FBI, self).seeing_alien(game)
        self.target = game.player.position

    def not_seeing_alien(self):
        super(FBI, self).not_seeing_alien()
        #self.target = None

    def move(self, game):
        if self.target:
            self.move_toward(self.target, self.speed, 40.0)
        else:
            self.target = game.player_last_seen

        if self.verlet_move():
            self.animate(0.1)

        self.set_sprite_pos()

        if (self.position - game.player.position).magnitude() < 50.0:
            game.game_over = True

    def hit(self, game, sprite, other):
        super(FBI, self).hit(game, sprite, other)

        if (other.backref.__class__ is SweatDrop):
            if (self.seen_count <= 0):
                self.target = other.backref.next.position            
            game.sprites.remove(other)
 
        if (other.backref is game.player):
            game.game_over = True

class Farmer(Human):
    def __init__(self, game, tile, values=None):
        super(Farmer, self).__init__('farmer_d0', 'farmer', game, tile, values)
        self.frames['l'].append(game.images['farmer_l0'])
        self.frames['r'].append(game.images['farmer_r0'])
        self.frames['d'].append(game.images['farmer_d0'])
        self.frames['u'].append(game.images['farmer_u0'])
        self.speed = 0.5
        self.top_speed = 1.0

    def step(self, game, sprite):
        super(Farmer, self).step(game, sprite)

    def move_blocked(self):
        self.waypoint = (self.waypoint + 1) % len(self.waypoints)
        self.target = self.waypoints[self.waypoint]

    def reached_target(self):
        if self.seen_count > 0:
            # we reached the alien.. do nothing
            pass
        else:
            # goto my next waypoint
            self.waypoint = (self.waypoint + 1) % len(self.waypoints)
            self.target = self.waypoints[self.waypoint]

    def hit(self, game, sprite, other):
        super(Farmer, self).hit(game, sprite, other)

    def lost_alien(self, game):
        super(Farmer, self).lost_alien(game)
        if len(self.waypoints) > 0:
            self.target = self.waypoints[self.waypoint]
            self.top_speed = 1.0

    def seen_alien(self, game):
        super(Farmer, self).seen_alien(game)
        self.sound_spotted_scream.play()
        self.stop()
        self.top_speed = 0.5
        self.target = game.player.position
        game.player_last_seen = game.player.position

        # spawn an FBI agent!
        if len(game.fbi_spawns) > 0:
            random.choice(game.fbi_spawns).spawn(game.player.position.copy())

    def seeing_alien(self, game):
        super(Farmer, self).seeing_alien(game)
        self.target = game.player.position

class Cow(Sprite):
    def __init__(self, game, tile, values=None):
        super(Cow, self).__init__('cow_l1', 'animal', game, tile, values)
        self.frames['l'].append(game.images['cow_l0'])
        self.frames['l'].append(game.images['cow_l1'])
        self.frames['r'].append(game.images['cow_r0'])
        self.frames['r'].append(game.images['cow_r1'])
        self.frames['d'].append(game.images['cow_d0'])
        self.frames['d'].append(game.images['cow_d1'])
        self.frames['u'].append(game.images['cow_u0'])
        self.frames['u'].append(game.images['cow_u1'])
        self.frames['ul'].append(game.images['cow_ul0'])
        self.frames['ul'].append(game.images['cow_ul1'])
        self.frames['ur'].append(game.images['cow_ur0'])
        self.frames['ur'].append(game.images['cow_ur1'])
        self.frames['dl'].append(game.images['cow_dl0'])
        self.frames['dl'].append(game.images['cow_dl1'])
        self.frames['dr'].append(game.images['cow_dr0'])
        self.frames['dr'].append(game.images['cow_dr1'])
        self.dir_func = self.direction8
        self.sprite.agroups = game.string2groups('')
        self.sprite.hit = self.hit
        self.speed = 0.2
        self.top_speed = 0.4
        
        if self.waypoints == 0:
            self.target = euclid.Vector2([random.uniform(-10.0, 10.0), \
                                          random.uniform(-10.0, 10.0) ] )
            
        self.sound_one_cow = pygame.mixer.Sound('data/sfx/One-Cow.ogg')
        self.sound_one_cow.set_volume(0.3)
        self.sound_two_cows = pygame.mixer.Sound('data/sfx/Two-Cows-Loop.ogg')
        self.sound_two_cows.set_volume(0.3)
        self.sound_two_cows.play(-1)

    def step(self, game, sprite):
        super(Cow, self).step(game, sprite)
        self.move(game)

    def move(self, game):
        if len(self.waypoints) == 0: return

        target = self.waypoints[self.waypoint]

        if self.move_toward(target, self.speed, 10.0):
            self.waypoint = (self.waypoint + 1) % len(self.waypoints)

        if not self.verlet_move():
            self.waypoint = (self.waypoint + 1) % len(self.waypoints)

        self.animate(0.04)
        self.set_sprite_pos()

    def hit(self, game, sprite, other):
        # push(sprite, other)
        # self.get_sprite_pos()
        pass

    def get_sucked(self):
        self.sound_one_cow.play()
        self.sound_two_cows.stop()

class CollectableCow(Cow):
    def __init__(self, game, tile, values=None):
        super(CollectableCow, self).__init__(game, tile, values)
        self.trophy = True

class StationaryCow(Cow):
    def __init__(self, game, tile, values=None):
        super(StationaryCow, self).__init__(game, tile, values)
        facing = random.choice([y for x in self.frames.values() for y in x])
        self.set_image(facing)

class Saucer(Sprite):
    def __init__(self, game, tile, values=None):
        super(Saucer, self).__init__('saucer0', 'Background', game, tile, values)
        self.frames[' '].append(game.images['saucer1'])
        self.frames[' '].append(game.images['saucer2'])
        self.speed     = 3.0
        self.top_speed = 7.0
        self.set_scale(3.0)
        self.land_pos      = self.position.copy()
        self.position[1]   = game.view.y
        self.land_distance = (self.land_pos - self.position).magnitude()
        self.stop()
        pygame.mixer.music.load('data/sfx/SaucerLand.ogg')
        pygame.mixer.music.play(0, 0.0)

        #d = time.time()
        #self.test = sprite_eater.SpriteEater(self.sprite.image)
        #while self.test.advance_frame():
        #    self.test.advance_frame()
        #    self.test.advance_frame()
        #    newimage = self.sprite.image.copy()
        #    self.test.blit_to(newimage)
        #    self.frames.append(newimage)
        #logit('took', time.time() - d)

    def step(self, game, sprite):
        if game.player.state == 'landing':
            percent = 1.0 - ((self.land_pos - self.position).magnitude() / self.land_distance)
            self.move_toward(self.land_pos, self.speed * (1.0 - percent), 10.0)

            if not self.verlet_move(False):
                game.player.landed(game)
                self.stop()
                self.speed = 0.0
                self.top_speed = 0.0
                self.set_scale(1.0)
                self.set_rotation(0.0)
                self.set_sprite_pos()
                return

            self.set_sprite_pos()
            self.animate(1.0 - (0.9 * percent))
            self.set_scale(3.0 - (2.0 * (math.pow(percent, 1.5))))
            self.set_rotation(math.sin(percent*math.pi*6.0)*1.0)
        else:
            self.animate(0.1)

class Tree(Sprite):
    def __init__(self, game, tile, values=None):
        super(Tree, self).__init__('tree', 'Background', game, tile, values)
        self.suckable = True

class Bush(Sprite):
    def __init__(self, game, tile, values=None):
        super(Bush, self).__init__('bush', 'Background', game, tile, values)

class Chicken(Sprite):
    def __init__(self, game, tile, values=None):
        super(Chicken, self).__init__('chick1', 'Background', game, tile, values)
        for x in xrange(10):
            idle = random.randint(0, 60)
            for y in xrange(idle):
                self.frames[' '].append(game.images['chick1'])
            peck = random.randint(0, 7)
            for y in xrange(peck):
                self.frames[' '].append(game.images['chick1'])
                self.frames[' '].append(game.images['chick2'])

    def step(self, game, sprite):
        self.animate(0.2)


class FBISpawn(Sprite):
    def __init__(self, game, tile, values=None):
        super(FBISpawn, self).__init__('none', 'hidden', game, tile, values)
        self.sprite.agroups = game.string2groups('fbi_spawn')
        game.fbi_spawns.append(self)
        self.tile = vid.Tile(tile.image)
        self.tile.tx = tile.tx
        self.tile.ty = tile.ty
        self.tile.agroups = tile.agroups
        self.tile.rect    = tile.rect.inflate(0,0)
        self.game = game

        if values:
            self.values = values[:]
        else:
            self.values = None


    def spawn(self, target_pos):
        agent = FBI(self.game, self.tile, self.values)
        agent.target = target_pos

class SweatDrop(Sprite):
    def __init__(self, game, tile, values=None):
        super(SweatDrop, self).__init__('laser', 'sweatdrop', game, tile, values)
        self.sprite.agroups = 0
        self.next = None

class VisionTest(Sprite):
    def __init__(self, game, tile, values=None):
        super(VisionTest, self).__init__('laser', 'hidden', game, tile, values)
        self.sprite.agroups = game.string2groups('animal,Background,farmer,fbi,player')
        self.sprite.hit = self.hit
        self.lived_once = False

    def step(self, game, sprite):
        if self.lived_once == False:
            self.lived_once = True
            return
        # game.sprites.remove(sprite)

    def tile_blocked(self):
        pass

    def hit(self, game, sprite, other):
        pass

class SelectionTest(Sprite):
    def __init__(self, game, tile, values=None):
        super(SelectionTest, self).__init__('none', 'shot', game, tile, values)
        self.sprite.agroups = game.string2groups('animal,Background')
        self.sprite.hit = self.hit
        self.lived_once = False

    def step(self, game, sprite):
        if self.lived_once == False:
            self.lived_once = True
            return
        game.sprites.remove(sprite)

    def hit(self, game, sprite, other):
        if  (hasattr(other.backref, 'suckable') and other.backref.suckable) or other.backref.trophy:
            game.player.suck_target = other.backref

def push(mover, away_from):
    if mover._rect.bottom <= away_from._rect.top and mover.rect.bottom > away_from.rect.top:
        mover.rect.bottom = away_from.rect.top
    if mover._rect.right <= away_from._rect.left \
           and mover.rect.right > away_from.rect.left:
        mover.rect.right = away_from.rect.left
    if mover._rect.left >= away_from._rect.right \
           and mover.rect.left < away_from.rect.right:
        mover.rect.left = away_from.rect.right
    if mover._rect.top >= away_from._rect.bottom \
           and mover.rect.top < away_from.rect.bottom:
        mover.rect.top = away_from.rect.bottom
