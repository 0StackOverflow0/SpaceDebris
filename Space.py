from tabnanny import verbose
from turtle import circle
import pygame
from pygame.locals import *
import numpy as np
import math
import random


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

turn   = (False, False)
thrust = False
t_vel  = 0.005
#angle = 0
angle = random.randint(0,360)
#pos   = (4,5)
pos = (random.randint(-100, 100) + middle[0], random.randint(-100, 100) + middle[1])
#vel   = (0.0,0.0)
vel = (random.random() * 5.0, random.random() * 5.0)
hull  = [(0,-5),(4,5),(0,4),(-4,5)]
theta = lambda a : (2 * math.pi) * (a / 360)
cos_t = lambda a : math.cos(theta(a))
sin_t = lambda a : math.sin(theta(a))
rotated = lambda coor, a : [((x * cos_t(a)) + (y * sin_t(a)),
                     (y * cos_t(a)) + (-x * sin_t(a))) for x, y in coor]
ship  = lambda : [(x + pos[0], y + pos[1]) for x, y in rotated(hull, angle)]

g_const   = 0.05
ship_mass = 1.0
sun_mass  = 250.0
vector    = lambda pos : (float(middle[0] - pos[0]), float(middle[1] - pos[1]))
r_x       = lambda : abs(vector(pos)[0]) / abs(vector(pos)[1])
r_y       = lambda : abs(vector(pos)[1]) / abs(vector(pos)[0])
radius    = lambda coor : math.sqrt(
    math.pow(vector(coor)[0], 2) +
    math.pow(vector(coor)[1], 2)
)
force     = lambda : (g_const * ship_mass * sun_mass) / radius(pos)
accel     = lambda : ((1 if vector(pos)[0] > 0 else -1 ) * force() / math.sqrt(1 + math.pow(r_x(),2)) * r_x(), 
                      (1 if vector(pos)[1] > 0 else -1 ) * force() / math.sqrt(1 + math.pow(r_y(),2)) * r_y())

class bullet:
    def __init__(self):
        direction = rotated([(0.0,-5.0)], angle)[0]
        self.velocity = (vel[0] + (direction[0] * 3.0/5.0), vel[1] + (direction[1] * 3.0/5.0))
        self.position = (pos[0] + direction[0], pos[1] + direction[1])

    def update(self):
        self.position = (self.position[0] + self.velocity[0], self.position[1] + self.velocity[1])
        if self.position[0] < 0 or self.position[1] < 0 or \
            self.position[0] > display[0] or self.position[1] > display[1]:
            return False
        return True
        
bullets = []

class afterburn:
    def __init__(self):
        global angle
        temp_angle = angle
        angle += random.randint(-15, 15)
        direction = rotated([(0.0,4.0)], angle)[0]
        angle = temp_angle
        self.velocity = (vel[0] + (direction[0] * 1.0/4.0), vel[1] + (direction[1] * 1.0/4.0))
        self.position = (pos[0] + direction[0], pos[1] + direction[1])
        self.ttl = random.randint(5,50)

    def update(self):
        self.position = (self.position[0] + self.velocity[0], self.position[1] + self.velocity[1])
        if self.position[0] < 0 or self.position[1] < 0 or \
            self.position[0] > display[0] or self.position[1] > display[1]:
            return False
        self.ttl -= 1
        if self.ttl < 1:
            return False
        return True

burns = []

def setup():
    pass

def loop(screen):
    global bullets, burns
    pygame.draw.circle(screen, white, middle, 10.0, 10)
    pygame.draw.lines(screen, white, True, ship())
    [pygame.draw.circle(screen, white, b.position, 2.0, 1) for b in bullets]
    [pygame.draw.circle(screen, white, b.position, 1.0, 1) for b in burns]

def move():
    global turn, angle, vel, pos, bullets, burns
    if turn[0]:
        angle += 5
    if turn[1]:
        angle -= 5
    if thrust:
        x, y = rotated([(0.0,-t_vel)], angle)[0]
        vel = (vel[0] + x, vel[1] + y)
        if random.randint(0,100) % 4 == 0:
            burns.append(afterburn())

    x_a, y_a = accel()
    vel = (vel[0] + x_a, vel[1] + y_a)

    pos = (pos[0] + vel[0], pos[1] + vel[1])

    if pos[0] > display[0]:
        pos = (0, pos[1])
    if pos[1] > display[1]:
        pos = (pos[0], 0)
        
    if pos[0] < 0:
        pos = (display[0], pos[1])
    if pos[1] < 0:
        pos = (pos[0], display[1])

    bullets = [ b for b in bullets if b.update() ]
    burns = [ b for b in burns if b.update() ]

def main():
    global thrust, turn, bullets, verbose
    pygame.init()
    screen = pygame.display.set_mode(display, DOUBLEBUF)

    setup()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    turn = (True, turn[1])
                if event.key == pygame.K_RIGHT:
                    turn = (turn[0], True)
                if event.key == pygame.K_UP:
                    thrust = (True, thrust)
                if event.key == pygame.K_DOWN:
                    bullets.append(bullet())
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    turn = (False, turn[1])
                if event.key == pygame.K_RIGHT:
                    turn = (turn[0], False)
                if event.key == pygame.K_UP:
                    thrust = False

        move()

        screen.fill((0, 0, 0))

        loop(screen)

        if verbose:
            font = pygame.font.SysFont(None, 24)
            img = font.render(f'force: {force()}', True, blue)
            screen.blit(img, (20, 0))
            img = font.render(f'velocity: {vel}', True, blue)
            screen.blit(img, (20, 20))
            img = font.render(f'accel: {accel()}', True, blue)
            screen.blit(img, (20, 40))
            img = font.render(f'vector: {vector()}', True, blue)
            screen.blit(img, (20, 60))
            #img = font.render(f'ratio: {ratio()}', True, blue)
            #screen.blit(img, (20, 80))
            img = font.render(f'radius: {radius()}', True, blue)
            screen.blit(img, (20, 100))

        pygame.display.flip()
        pygame.time.wait(10) # 100 fps max


main()