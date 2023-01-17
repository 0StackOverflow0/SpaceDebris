from copy import deepcopy
from tabnanny import verbose
import pygame
from pygame.locals import *
import math
import random
from numba import njit
from time import perf_counter
from contextlib import contextmanager

@contextmanager
def catchtime() -> float:
    start = perf_counter()
    yield lambda: perf_counter() - start

display = (1200,1200)
middle  = (display[0]/2,display[1]/2)
verbose = False


red = (255,0,0)
green = (0,255,0)
blue = (0,0,255)
darkBlue = (0,0,128)
white = (255,255,255)
black = (0,0,0)
pink = (255,200,200)

@njit
def theta(a):
    return (2 * math.pi) * (a / 360)

@njit
def cos_t(a):
    return math.cos(theta(a))

@njit
def sin_t(a):
    return math.sin(theta(a))

@njit
def obj_angle(a, b):
    return math.atan2(b, a)* (180 / math.pi)

@njit
def rotated(coor, a):
    x, y = coor
    return ((x * cos_t(a)) + (y * sin_t(a)),
            (y * cos_t(a)) + (-x * sin_t(a)))

def rotate_obj(obj, pos, angle):
    r = [ rotated(side, angle) for side in obj ]
    return [(x + pos[0], y + pos[1]) for x, y in r ] 

def collision(obj_a, pos_b):
    pos_a = obj_a.pos

    hull_a   = [rotated(side, obj_a.angle) for side in obj_a.hull]
    hull_a_r = deepcopy(hull_a)
    first = hull_a_r.pop(0)
    hull_a_r.append(first)
 
    t_pos_b = (pos_b[0] - pos_a[0], pos_b[1] - pos_a[1])
    angle2 = obj_angle(t_pos_b[0], t_pos_b[1])
    r_pos_b = rotated(t_pos_b, -angle2)

    if r_pos_b[0] < 25.0:
        collide = True
        mvt = 9999999.0
        for a_1, a_2 in zip(hull_a, hull_a_r):
            t_a_2 = (a_2[0] - a_1[0], a_2[1] - a_1[1])
            # jit this
            #angle = math.atan2(t_a_2[1], t_a_2[0])* (180 / math.pi)
            angle = obj_angle(t_a_2[0], t_a_2[1])
            t_pos_b = (pos_b[0] - pos_a[0] - a_1[0], pos_b[1] - pos_a[1] - a_1[1])
            # jit this, this might be deletable actually
            #angle2 = math.atan2(t_pos_b[1], t_pos_b[0])* (180 / math.pi)
            r_pos_b = rotated(t_pos_b, angle)
            if r_pos_b[1] >= 0:
                mvt = mvt if mvt < r_pos_b[1] else r_pos_b[1] # not the best calculation, revisit
            else:
                collide = False

        return collide
    return False


class bullet:
    mass = 0.1

    def __init__(self):
        direction = rotated((0.0,-5.0), ship.angle)
        self.vel = (ship.vel[0] + (direction[0] * 2.5/5.0), ship.vel[1] + (direction[1] * 2.5/5.0))
        self.pos = (ship.pos[0] + direction[0], ship.pos[1] + direction[1])

    def move(self):
        x_a, y_a = sun.accel(self)
        self.vel = (self.vel[0] + x_a, self.vel[1] + y_a)
        self.pos = (self.pos[0] + self.vel[0], self.pos[1] + self.vel[1])
        if self.pos[0] < 0 or self.pos[1] < 0 or \
            self.pos[0] > display[0] or self.pos[1] > display[1]:
            return False
        return True

    def draw(self, screen):
        pygame.draw.circle(screen, white, self.pos, 2.0, 1)
        
bullets = []


class afterburn:
    def __init__(self):
        angle = ship.angle + random.randint(-15, 15)
        direction = rotated((0.0,4.0), angle)
        self.vel = (ship.vel[0] + (direction[0] * 1.0/4.0), ship.vel[1] + (direction[1] * 1.0/4.0))
        self.pos = (ship.pos[0] + direction[0], ship.pos[1] + direction[1])
        self.ttl = random.randint(0,50)

    def move(self):
        self.pos = (self.pos[0] + self.vel[0], self.pos[1] + self.vel[1])
        if self.pos[0] < 0 or self.pos[1] < 0 or \
            self.pos[0] > display[0] or self.pos[1] > display[1]:
            return False
        self.ttl -= 1
        if self.ttl < 1:
            return False
        return True

    def draw(self, screen):
        pygame.draw.circle(screen, white, self.pos, 1.0, 1)

burns = []

class star:
    g_const = 0.025
    mass    = 500.0

    def __init__(self):
        self.vector = lambda pos : (float(middle[0] - pos[0]), float(middle[1] - pos[1]))
        self.r_x    = lambda pos : abs(self.vector(pos)[0]) / ( abs(self.vector(pos)[1]) + 0.000001)
        self.r_y    = lambda pos : abs(self.vector(pos)[1]) / ( abs(self.vector(pos)[0]) + 0.000001)
        self.radius      = lambda pos : math.sqrt(
            math.pow(self.vector(pos)[0], 2) +
            math.pow(self.vector(pos)[1], 2)
        )
        self.force     = lambda obj : (self.g_const * obj.mass * self.mass) / self.radius(obj.pos)
        self.accel     = lambda obj : ((1 if self.vector(obj.pos)[0] > 0 else -1 ) * self.force(obj) / math.sqrt(1 + math.pow(self.r_x(obj.pos),2)) * self.r_x(obj.pos), 
                                       (1 if self.vector(obj.pos)[1] > 0 else -1 ) * self.force(obj) / math.sqrt(1 + math.pow(self.r_y(obj.pos),2)) * self.r_y(obj.pos))

    def draw(self, screen):
        pygame.draw.circle(screen, white, middle, 10.0, 10)

sun = star()

class fragment:
    mass = 1.0

    def __init__(self):
        angle = random.randint(0,360)
        radius = random.randint(300,600)
        self.pos   = rotated((radius,0.0), angle)
        self.pos   = (self.pos[0] + middle[0], self.pos[1] + middle[1])
        self.vel   = rotated((math.sqrt( 10000.0 / ( 3.0 * radius )),0.0), angle + 90)
        self.r_vel = (random.random() * 4.0) - 2.0
        self.angle = angle
        self.hull  = [(-12.5,10.825),(0,-10.825), (12.5,10.825)]

    def draw(self, screen):
        pygame.draw.lines(screen, white, True, rotate_obj(self.hull, self.pos, self.angle))
        
    def move(self):
        x_a, y_a = sun.accel(self)
        self.vel = (self.vel[0] + x_a, self.vel[1] + y_a)
        self.pos = (self.pos[0] + self.vel[0], self.pos[1] + self.vel[1])
        self.angle += self.r_vel
        if self.pos[0] < 0 or self.pos[1] < 0 or \
            self.pos[0] > display[0] or self.pos[1] > display[1]:
            return False
        return True

class astroid:
    mass = 6.0

    def __init__(self):
        angle = random.randint(0,360)
        radius = random.randint(200,500)
        self.pos   = rotated((radius,0.0), angle)
        self.pos   = (self.pos[0] + middle[0], self.pos[1] + middle[1])
        self.vel   = rotated((math.sqrt( 60000.0 / ( 3.0 * radius )),0.0), angle + 90)
        self.r_vel = (random.random() * 4.0) - 2.0
        self.angle = random.randint(0,360)
        self.hull  = [(-25.0,0.0),(-12.5,-21.65),(12.5,-21.65),(25.0,0.0),(12.5,21.65),(-12.5,21.65)]

    def draw(self, screen):
        pygame.draw.lines(screen, white, True, rotate_obj(self.hull, self.pos, self.angle))
        
    def move(self):
        x_a, y_a = sun.accel(self)
        self.vel = (self.vel[0] + x_a, self.vel[1] + y_a)
        self.pos = (self.pos[0] + self.vel[0], self.pos[1] + self.vel[1])
        self.angle += self.r_vel
        if self.pos[0] < 0 or self.pos[1] < 0 or \
            self.pos[0] > display[0] or self.pos[1] > display[1]:
            return False
        return True

    def split(self):
        frags = [ fragment() for _ in range(6) ]
        def update(f, i):
            f.angle = self.angle + (60 * i)
            pos = rotated((-17.677,0.0),f.angle - 30)
            f.pos = (self.pos[0] + pos[0], self.pos[1] + pos[1])
            f.vel = ((self.vel[0] / 2.0) + (pos[0] / 15.0), (self.vel[1] / 2.0) + (pos[1] / 15.0)) # self.vel
            f.r_vel = self.r_vel * 2.0
        [ update(f, i) for i, f in enumerate(frags) ]
        return frags

#astroids = [astroid() for _ in range(random.randint(4,6))] + [fragment() for _ in range(random.randint(6,9))]
#astroids = [astroid() for _ in range(random.randint(7,9))] + [fragment() for _ in range(random.randint(11,15))]
astroids = [astroid() for _ in range(random.randint(10,12))] + [fragment() for _ in range(random.randint(17,21))]


class space:
    over = False
    win  = False

game = space()


class shuttle:
    turn   = (False, False)
    thrust = False
    t_vel  = 0.005
    mass   = 1.0
    cooldown = 0
    angle  = random.randint(0,360)
    radius = random.randint(50,100)
    pos    = rotate_obj([(radius,0.0)], middle, angle)[0]
    vel    = rotated((math.sqrt( 5000.0 / ( 3.0 * radius )),0.0), angle + 90)
    hull   = [(0,-5),(4,5),(0,4),(-4,5)]

    def leftDown(self):
        self.turn = (True, self.turn[1])

    def leftUp(self):
        self.turn = (False, self.turn[1])

    def rightDown(self):
        self.turn = (self.turn[0], True)

    def rightUp(self):
        self.turn = (self.turn[0], False)

    def thrustDown(self):
        self.thrust = True

    def thrustUp(self):
        self.thrust = False

    def fire(self):
        if ship.cooldown <= 0:
            bullets.append(bullet())
            ship.cooldown += 1

    def draw(self, screen):
        pygame.draw.lines(screen, white, True, rotate_obj(self.hull, self.pos, self.angle))

    def move(self):   
        if self.turn[0]:
            self.angle += 5
        if self.turn[1]:
            self.angle -= 5
        if self.thrust:
            x, y = rotated((0.0,-self.t_vel), self.angle)
            self.vel = (self.vel[0] + x, self.vel[1] + y)
            burns.append(afterburn())

        x_a, y_a = sun.accel(self)
        self.vel = (self.vel[0] + x_a, self.vel[1] + y_a)

        self.pos = (self.pos[0] + self.vel[0], self.pos[1] + self.vel[1])

        if self.pos[0] > display[0] or \
            self.pos[1] > display[1] or \
            self.pos[0] < 0 or \
            self.pos[1] < 0:
            game.over = True
            game.win  = True
        
        if self.cooldown > 0:
            self.cooldown -= 1

ship = shuttle()

def setup():
    pass

def loop(screen):
    move()
    
    with catchtime() as t:
        collisions()
    
    print(f"Time for collisions: {t()}")

    screen.fill((0, 0, 0))

    sun.draw(screen)
    ship.draw(screen)
    [o.draw(screen) for o in bullets]
    [o.draw(screen) for o in burns]
    [o.draw(screen) for o in astroids]
        
    if verbose:
        font = pygame.font.SysFont(None, 24)
        img = font.render(f'force: {sun.force(ship)}', True, blue)
        screen.blit(img, (20, 0))
        img = font.render(f'velocity: {ship.vel}', True, blue)
        screen.blit(img, (20, 20))
        img = font.render(f'accel: {sun.accel(ship)}', True, blue)
        screen.blit(img, (20, 40))
        img = font.render(f'vector: {sun.vector(ship)}', True, blue)
        screen.blit(img, (20, 60))
        #img = font.render(f'ratio: {ratio()}', True, blue)
        #screen.blit(img, (20, 80))
        img = font.render(f'radius: {sun.radius(ship)}', True, blue)
        screen.blit(img, (20, 100))

    pygame.display.flip()
    pygame.time.wait(10) # 100 fps max

def move():
    global bullets, burns, astroids
    ship.move()
    bullets = [ b for b in bullets if b.move() ]
    burns = [ b for b in burns if b.move() ]
    astroids = [ a for a in astroids if a.move() ]

def collisions():
    global astroids
    split_a  = [ a for a in astroids if type(a) is astroid and any(collision(a, b.pos) for b in bullets) ]
    astroids = [ a for a in astroids if not any(collision(a, b.pos) for b in bullets) ]
    split_a  = [ a.split() for a in split_a ]
    astroids += [ f for fragments in split_a for f in fragments ]
    game.over |= any(collision(ship, b.pos) for b in bullets)
    game.over |= any(collision(a, b) for a in astroids for b in rotate_obj(ship.hull, ship.pos, ship.angle))

def main():
    pygame.init()
    screen = pygame.display.set_mode(display, DOUBLEBUF)

    setup()

    while not game.over:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    ship.leftDown()
                if event.key == pygame.K_RIGHT:
                    ship.rightDown()
                if event.key == pygame.K_UP:
                    ship.thrustDown()
                if event.key == pygame.K_DOWN:
                    ship.fire()
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    ship.leftUp()
                if event.key == pygame.K_RIGHT:
                    ship.rightUp()
                if event.key == pygame.K_UP:
                    ship.thrustUp()
        ship.fire()
        loop(screen)

    font = pygame.font.SysFont(None, 42)
    img = font.render(f'Game Over', True, blue)
    screen.blit(img, (middle[0] - 85, middle[1] - 45))
    img = font.render(f'{"Win" if game.win else "Lost"}', True, blue)
    screen.blit(img, (middle[0] - 32, middle[1] + 25))

    import time
    pygame.display.flip()
    time.sleep(10)
    #pygame.time.wait(10000) # 100 fps max


main()