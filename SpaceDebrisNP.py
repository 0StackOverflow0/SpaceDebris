from tabnanny import verbose
import pygame
from pygame.locals import *
import numpy as np
import math
import random
from numba import njit, jit
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
    return math.atan2(b, a) * (180 / math.pi)

@njit
def rotated(coor, a):
    x, y = coor
    return np.array(((x * cos_t(a)) + (y * sin_t(a)),
            (y * cos_t(a)) + (-x * sin_t(a))))

def rotate_obj(obj, pos, angle):
    return np.add([ rotated(side, angle) for side in obj ], [pos for _ in range(len(obj))])

@njit
def collide(hull_a, hull_a_r, pos_a, pos_b):
    for a_1, a_2 in zip(hull_a, hull_a_r):
        t_a_2 = np.subtract(a_2, a_1)
        angle = obj_angle(t_a_2[0], t_a_2[1])
        t_pos_b = np.subtract(np.subtract(pos_b, pos_a), a_1)
        r_pos_b = rotated(t_pos_b, angle)
        if r_pos_b[1] <=0:
            return False

    return True

@jit
def collision(pos_a, angle, hull, pos_b):
    hull_a   = np.array([rotated(side, angle) for side in hull])
    hull_a_r = np.copy(hull_a)
    hull_a_r = np.append(hull_a_r, [hull_a[0]], 0)
    hull_a_r = np.delete(hull_a_r, 0, 0)
 
    t_pos_b = np.subtract(pos_b, pos_a)
    angle2 = obj_angle(t_pos_b[0], t_pos_b[1])
    r_pos_b = rotated(t_pos_b, -angle2)

    if r_pos_b[0] < 25.0:
        return collide(hull_a, hull_a_r, pos_a, pos_b)
    return False


class bullet:
    mass = 0.1
    offset = np.array((0.0, -5.0))

    def __init__(self):
        direction = rotated(self.offset, ship.angle)
        self.vel = np.add(ship.vel, ((direction[0] * 2.5/5.0), (direction[1] * 2.5/5.0)))
        self.pos = np.add(ship.pos, direction)

    def move(self):
        accel = sun.accel(self)
        self.vel = np.add(self.vel,accel)
        self.pos = np.add(self.pos, self.vel)
        if self.pos[0] < 0 or self.pos[1] < 0 or \
            self.pos[0] > display[0] or self.pos[1] > display[1]:
            return False
        return True

    def draw(self, screen):
        pygame.draw.circle(screen, white, self.pos, 2.0, 1)
        
bullets = []


class afterburn:
    offset = np.array((0.0,4.0))

    def __init__(self):
        angle = ship.angle + float(random.randint(-15, 15))
        direction = rotated(self.offset, angle)
        self.vel = np.add(ship.vel, np.multiply(direction, 1.0/4.0))
        self.pos = np.add(ship.pos, direction)
        self.ttl = random.randint(0,50)

    def move(self):
        self.pos = np.add(self.pos, self.vel)
        if self.pos[0] < 0 or self.pos[1] < 0 or \
            self.pos[0] > display[0] or self.pos[1] > display[1]:
            # Out of Bounds
            return False
        self.ttl -= 1
        if self.ttl < 1:
            # End of Life
            return False
        return True

    def draw(self, screen):
        pygame.draw.circle(screen, white, self.pos, 1.0, 1)

burns = []

class star:
    g_const = 0.025
    mass    = 500.0

    def __init__(self):
        self.vector = lambda pos : np.subtract(middle, pos)
        self.direction = lambda v : 1 if v > 0 else -1
        self.r_x    = lambda pos : abs(self.vector(pos)[0]) / ( abs(self.vector(pos)[1]) + 0.000001)
        self.r_y    = lambda pos : abs(self.vector(pos)[1]) / ( abs(self.vector(pos)[0]) + 0.000001)
        self.radius = lambda pos : math.sqrt(
            np.sum(
                np.vectorize(lambda x : math.pow(x, 2))(self.vector(pos))
            )
        )
        self.force     = lambda obj : (self.g_const * obj.mass * self.mass) / self.radius(obj.pos)
        self.gravity   = lambda obj : (self.force(obj) / math.sqrt(1 + math.pow(self.r_x(obj.pos),2)) * self.r_x(obj.pos),
                                       self.force(obj) / math.sqrt(1 + math.pow(self.r_y(obj.pos),2)) * self.r_y(obj.pos))
        self.accel     = lambda obj : np.multiply(np.vectorize(self.direction)(self.vector(obj.pos)), self.gravity(obj))

    def draw(self, screen):
        pygame.draw.circle(screen, white, middle, 10.0, 10)

sun = star()

class fragment:
    mass = 1.0

    def __init__(self):
        angle = float(random.randint(0,360))
        radius = random.randint(300,600)
        self.pos   = rotated(np.array((radius,0.0)), angle)
        self.pos   = np.add(self.pos, middle)
        self.vel   = rotated(np.array((math.sqrt( 10000.0 / ( 3.0 * radius )),0.0)), angle + 90)
        self.r_vel = (random.random() * 4.0) - 2.0
        self.angle = angle
        self.hull  = np.array([
            np.array((-12.5,10.825)),
            np.array((0,-10.825)), 
            np.array((12.5,10.825))
        ])

    def draw(self, screen):
        pygame.draw.lines(screen, white, True, rotate_obj(self.hull, self.pos, self.angle))
        
    def move(self):
        accel = sun.accel(self)
        self.vel = np.add(self.vel, accel)
        self.pos = np.add(self.pos, self.vel)
        self.angle += self.r_vel
        if self.pos[0] < 0 or self.pos[1] < 0 or \
            self.pos[0] > display[0] or self.pos[1] > display[1]:
            # Out of Bounds
            return False
        return True

class astroid:
    mass = 6.0

    def __init__(self):
        angle = float(random.randint(0,360))
        radius = random.randint(200,500)
        self.pos   = rotated(np.array((radius,0.0)), angle)
        self.pos   = np.add(self.pos, middle)
        self.vel   = rotated(np.array((math.sqrt( 60000.0 / ( 3.0 * radius )),0.0)), angle + 90)
        self.r_vel = (random.random() * 4.0) - 2.0
        self.angle = float(random.randint(0,360))
        self.hull  = np.array([
            np.array((-25.0,0.0)),
            np.array((-12.5,-21.65)),
            np.array((12.5,-21.65)),
            np.array((25.0,0.0)),
            np.array((12.5,21.65)),
            np.array((-12.5,21.65))
        ])

    def draw(self, screen):
        pygame.draw.lines(screen, white, True, rotate_obj(self.hull, self.pos, self.angle))
        
    def move(self):
        accel = sun.accel(self)
        self.vel = np.add(self.vel, accel)
        self.pos = np.add(self.pos, self.vel)
        self.angle += self.r_vel
        if self.pos[0] < 0 or self.pos[1] < 0 or \
            self.pos[0] > display[0] or self.pos[1] > display[1]:
            # Out of Bounds
            return False
        return True

    def split(self):
        frags = [ fragment() for _ in range(6) ]
        def update(f, i):
            f.angle = self.angle + (60 * i)
            pos = rotated(np.array((-17.677,0.0)),f.angle - 30)
            f.pos = np.add(self.pos, pos)
            f.vel = np.add(np.divide(self.vel, 2.0), np.divide(pos, 15.0))
            f.r_vel = self.r_vel * 2.0
        [ update(f, i) for i, f in enumerate(frags) ]
        return frags

#astroids = [astroid() for _ in range(random.randint(4,6))] + [fragment() for _ in range(random.randint(6,9))]
#astroids = [astroid() for _ in range(random.randint(7,9))] + [fragment() for _ in range(random.randint(11,15))]
astroids = {astroid() for _ in range(random.randint(10,12))}.union({fragment() for _ in range(random.randint(17,21))})

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
    angle  = float(random.randint(0,360))
    radius = random.randint(50,100)
    pos    = rotate_obj(np.array([(radius,0.0)]), middle, angle)[0]
    vel    = rotated(np.array((math.sqrt( 5000.0 / ( 3.0 * radius )),0.0)), angle + 90)
    hull   = np.array([
        np.array((0,-5)),
        np.array((4,5)),
        np.array((0,4)),
        np.array((-4,5))
    ])

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

        accel = sun.accel(self)
        self.vel = np.add(self.vel, accel)

        self.pos = np.add(self.pos, self.vel)

        if self.pos[0] > display[0] or \
            self.pos[1] > display[1] or \
            self.pos[0] < 0 or \
            self.pos[1] < 0:
            #Out of Bounds
            game.over = True
            game.win  = True
        
        if self.cooldown > 0:
            self.cooldown -= 1

ship = shuttle()

def setup():
    pygame.init()
    return pygame.display.set_mode(display, DOUBLEBUF)

def shutdown(screen):
    font = pygame.font.SysFont(None, 42)
    img = font.render(f'Game Over', True, blue)
    screen.blit(img, (middle[0] - 85, middle[1] - 45))
    img = font.render(f'{"Win" if game.win else "Lost"}', True, blue)
    screen.blit(img, (middle[0] - 32, middle[1] + 25))

    import time
    pygame.display.flip()
    time.sleep(5)

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
    astroids = { a for a in astroids if a.move() }

def collisions():
    global astroids
    split_a  = { a for a in astroids if any(collision(a.pos, a.angle, a.hull, b.pos) for b in bullets) }
    astroids -= split_a
    split_a  = [ a.split() for a in split_a if type(a) is astroid ]
    astroids = astroids.union({ f for fragments in split_a for f in fragments })
    game.over |= any(collision(ship.pos, ship.angle, ship.hull, b.pos) for b in bullets)
    game.over |= any(collision(a.pos, a.angle, a.hull, b) for a in astroids for b in rotate_obj(ship.hull, ship.pos, ship.angle))

def main():
    screen = setup()

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

    shutdown(screen)
    
main()