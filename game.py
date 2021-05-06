import os, sys
import pygame
import math
import cmath
from numpy.random import default_rng
from pygame.locals import *

#set up palette and scoreboard
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
LEFT = "left"
RIGHT = "right"
CENTER = "center"
high_score = 0
delay = 210
#machine learning variables, set ml=False to play for yourself
ml = True
rng = default_rng()
ml_coord = pygame.Vector2(0, 0) #the velocity of the highest-scoring instance so far, updated after each round
ml_tempcoord = pygame.Vector2(0, 0) #the velocity of the highest-scoring instance this round, ported to ml_coord if score is higher
ml_noise = 3 #standard deviation for gauss
ml_round = 1 #DNE
ml_trial = 1 #DNE
ml_target = 10 #change to control number of rounds
ml_trials = 10 #change to control number of rounds
round_array = [] #DNE
round_score = 0 #DNE
round_coord = pygame.Vector2(0, 0)
autoend = True #starts in active mode, press r to switch
        

'''def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error as message:
        print('Cannot load image:', name)
        raise SystemExit(message)
    image = image.convert()
    if colorkey is not None:
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey, RLEACCEL)
    return image, image.get_rect()'''



class Planet(pygame.sprite.Sprite):
    count = 0
    planets = pygame.sprite.Group()
    def __init__(self, posx, posy, radius):
        super().__init__()
        self.radius = radius
        self.mass = .10 * (radius ** 2)
        self.color = WHITE
        self.dead = False
        self.killrad = 30
        self.posx = posx
        self.posy = posy
        self.name = "planet" + str(Planet.count)
        Planet.count += 1
        self.collided = False
        self.render()
        Planet.planets.add(self)

    def render(self):
        self.image = pygame.Surface([(2 * self.radius), (2 * self.radius)])
        self.image.fill(BLACK)
        self.image.set_colorkey(BLACK)
        pygame.draw.circle(self.image, self.color, (self.radius, self.radius), self.radius, 0)
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect.center = [self.posx, self.posy]

    def update(self, *args, **kwargs):
        if self.collided:
            if self.radius > self.killrad:
                self.radius -= 5
                self.mass = .10 * (self.radius ** 2)
                self.render()
                self.collided = False
            else:
                self.dead = True
                self.kill()

    
class Sun(Planet):
    def __init__(self, posx, posy, radius):
        super().__init__(posx, posy, radius)
        self.radius = radius
        self.mass = .07 * (radius ** 2)
        self.color = YELLOW
        self.posx = posx
        self.posy = posy
        self.render()       

 
class Astro(pygame.sprite.Sprite):
    def __init__(self, velo):
        super().__init__()
        self.active = False
        self.mass = 10
        self.posx = 400
        self.posy = 250
        self.radius = 10
        self.startvelocity = pygame.Vector2(0, 0)
        self.velocity = velo
        self.color = [RED, BLUE, GREEN]
        self.score = 0
        self.collided = 0
        self.image = pygame.Surface([(2 * self.radius), (2 * self.radius)])
        self.image.fill(BLACK)
        self.image.set_colorkey(BLACK)
        pygame.draw.circle(self.image, self.color[0], (self.radius, self.radius), self.radius, 0)
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        
        self.rect.center = [self.posx, self.posy]
        
        
    def update(self, planets, suns, centgrav):
        if self.active:
            if suns:
                self._sundown(suns)
            self.planets = planets
##            for planet in self.planets: #obnoxious to for loop twice, but the first one's velocity and the second is collision
##                offsetx = (planet.rect.center[0] - self.rect.center[0])
##                offsety = (planet.rect.center[1] - self.rect.center[1])
##                dist = math.hypot(offsetx, offsety)
##                try:
##                    force = .275 * ((self.mass * planet.mass) / (dist ** 2))
##                except ZeroDivisionError:
##                    force = 0
##                self.velocity.x += (force * offsetx) / self.mass
##                self.velocity.y += (force * offsety) / self.mass

            for planet in self.planets:
                offsetx = (planet.rect.center[0] - self.rect.center[0])
                offsety = (planet.rect.center[1] - self.rect.center[1])
                dist = math.hypot(offsetx, offsety)    
                if self.velocity.x == 0:
                    pass
                else:
                    m = self.velocity.y/self.velocity.x 
                    A = (self.velocity.x ** 2) + (self.velocity.y ** 2) #point slope quadratic
                    B = 2 * ((self.velocity.x * -offsetx) + (self.velocity.y * -offsety))
                    C = (offsetx ** 2) + (offsety ** 2) - ((planet.radius + self.radius) ** 2)
                    D = (B ** 2) - (4 * A * C)
                    if D > 0: # this checks if a line drawn from the player through their velocity would hit the planet

                        try:
                            collide_x = (2 * C) / (-B + math.sqrt(D)) #this is the quadratic formula solving for the minimum value
                            if (0 < collide_x < 1):
                                planet.collided = True
                                relative_collide = ((self.velocity.x * collide_x), (self.velocity.y * collide_x))
                                collide_point = pygame.Vector2(self.rect.center[0] + (self.velocity.x * collide_x), (self.velocity.y * collide_x) + self.rect.center[1])
                                velo_temp =  pygame.Vector2(- relative_collide[0] - self.radius, - relative_collide[1] - self.radius) #store the distance "traveled" to get to the surface
                                self.rect.move_ip(relative_collide[0], relative_collide[1])
                                #self.rect = bounce
                                normal = pygame.Vector2(planet.posx - collide_point.x, planet.posy - collide_point.y)
                                self.velocity = self.velocity.reflect(normal)
                                velo_temp = velo_temp.reflect(normal)
                                self.rect.move_ip(velo_temp)
                                #self.rect = fling
                                self.collided = 0
                                centgrav.change(planets)
                                if planet.radius <= planet.killrad:
                                    self.velocity.x /= 1.25
                                    self.velocity.y /= 1.25
                        except ZeroDivisionError:
                            pass

##old colliision formula, do not ingest                
##                if (dist <  (planet.radius + 10)): #put this last, that way it can use the current frame's velocity and angle 
##                    if self.collided > 7:
##                        normal = pygame.Vector2(offsetx, offsety)
##                        self.velocity = self.velocity.reflect(normal)
##                        self.colorChange()
##                        self.Score(planet)
##                        planet.collided = True
##                        self.collided = 0

                if planet.collided == True:
                    self.colorChange()
                    self.Score(planet)
                    self.velocity.x /= 1.05
                    self.velocity.y /= 1.05
                           
            if self.collided >= 0:
                newpos = self.rect.move(self.velocity.x, self.velocity.y)
            else:
                newpos = self.rect
            self.collided += 1 
            self.rect = newpos
                                 

    def colorChange(self):
        self.color.append(self.color.pop(0))
        pygame.draw.circle(self.image, self.color[0], (self.radius, self.radius), self.radius, 0)

    def Score(self, planet):
        if self.color[0] == RED:
            mult = 1
        elif self.color[0] == BLUE:
            mult = 1.5
        elif self.color[0] == GREEN:
            mult = 2
        self.score += int(mult * (12000 / planet.radius))

        
    def _sundown(self, suns):
        self.suns = suns
        for sun in self.suns:
            offsetx = (sun.rect.center[0] - self.rect.center[0])
            offsety = (sun.rect.center[1] - self.rect.center[1])
            dist = math.hypot(offsetx, offsety)
            if (dist <  (sun.radius + 10)):
                main() #change this to add like an actual death screen

                
class CentGrav(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.x = 2
        self.y = 2

        self.image = pygame.Surface((4, 4))
        self.image.fill(RED)
        self.rect = pygame.Rect(self.x - 2, self.y - 2, 4, 4)

    def change(self, planets):
        self.moment_x = 0
        self.moment_y = 0
        self.mass_all = 0
        for planet in planets:
            self.moment_x += planet.rect.center[0] * planet.mass
            self.moment_y += planet.rect.center[1] * planet.mass
            self.mass_all += planet.mass
        try:
            x_pos = int(self.moment_x / self.mass_all) 
            y_pos = int(self.moment_y / self.mass_all)
        except ZeroDivisionError:
            x_pos, y_pos = 0, 0 # fix this, obvs it should only ignore whichever one is 0
        self.rect.center = (x_pos, y_pos)

            
class GaussArray():
    def __init__(self, size, rng):
        self.stddev = ml_noise
        self.size = (1, size)
        self.rng = rng


    def output(self, mag, ang):
        global round_array
        self.mag_array = rng.normal(mag, self.stddev, self.size)
        self.ang_array = rng.normal(ang, self.stddev, self.size)
        self.polar_array = []
        for i in range(len(self.mag_array[0])):
            trial_vect = pygame.Vector2(0, 0)
#            trial_vect.from_polar((int(self.mag_array[0][i]),int(self.ang_array[0][i]))) #so, what I want to do is have the coordinates the machine \
                                                                                         #learns be polar, so that it learns a good combo of distance and accuracy
            trial_coord = [self.mag_array[0][i], self.ang_array[0][i]]
            self.polar_array.append(trial_coord)
        round_array = self.polar_array
        
        
         

def killscreen(astro, Planet, allsprites, Textbox, centgrav):
    global ml
    global ml_tempcoord
    global ml_trial
    global ml_trials
    global ml_round
    global ml_target
    global autoend
    #score = astro.score
    centgrav.kill()
    place = "Final Score: "
    gameover = "Press R to restart"
    global high_score
    if ml:
        if astro.score > high_score:

            ml_tempcoord = astro.startvelocity
                    
    high_score = max(astro.score, high_score)
    for planet in Planet.planets:
        planet.kill()
    if ml:
        pause = False
        global round_score    #to tomorrow connor, fix the seed issue with ml_coord
        if astro.score > round_score:
            round_score = astro.score
            global round_coord
            round_coord = astro.startvelocity
        astro.active = False
        astro.kill()
        if ml_trial < ml_trials:

            reset(allsprites, Textbox, pause)
        elif ml_trial == ml_trials:
            ml_coord = ml_tempcoord

            if ml_round < ml_target:
                if not autoend:
                    pause = True
                    Textbox.textboxes[2]._swap("Round " + str(ml_round) + " Complete!")
                    if round_score:
                        Textbox.textboxes[3]._swap("Top Score: " + str(round_score) + "  Velocity: " + str(int(round_coord.x)) + ", " + str(int(round_coord.y)))
                    else:
                        Textbox.textboxes[3]._swap("Top Score: " + str(round_score) + ". Better luck next round.")
                ml_round += 1
                reset(allsprites, Textbox, pause)
            else:
                Textbox.textboxes[2]._swap("Final Round Complete!")
                Textbox.textboxes[3]._swap("Top Score: " + str(high_score) + "  Velocity: " + str(int(ml_coord.x)) + ", " + str(int(ml_coord.y)))
                ml_round = 1
                ml_coord.x, ml_coord.y = 0, 0
                reset(allsprites, Textbox, True)
    return [place, gameover]

class Textbox():
    textboxes = []
    def __init__(self, screen, color, x, y, justified):
        self.font = pygame.font.Font('freesansbold.ttf', 32)
        self.surface = screen
        self.color = color
        self.text = ""
        self.x = x
        self.y = y
        self.justified = justified
        Textbox.textboxes.append(self)
        
    def update(self):
        if self.text:
            self.pos = (self.x, self.y)
            textobj = self.font.render(self.text, True, self.color, BLACK)
            textRect = textobj.get_rect()
            if self.justified == LEFT:
                textRect.midleft = self.pos
            elif self.justified == CENTER:
                textRect.center = self.pos
            elif self.justified == RIGHT:
                textRect.midright = self.pos
            self.surface.blit(textobj, textRect)

    def _swap(self, text):
        self.text = text

    def _kill(self):
        self.text = ""

def linedraw(surface, newpos, oldpos):
    pygame.draw.line(surface, WHITE, newpos, oldpos, 2)

def reset(allsprites, Textbox, pause):
    global ml_trial
    global ml_trials
    global round_array
    global round_coord
    global round_score



    while pause:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                pause = False
                
        for text in Textbox.textboxes:
                text.update()
        pygame.display.update()
        
    if ml_trial == ml_trials:
        ml_trial = 1
        round_coord.x, round_coord.y = 0, 0      
        round_score = 0
    else:
        ml_trial += 1
    for textbox in Textbox.textboxes:
        textbox._kill()
    for sprite in allsprites:
        sprite.kill()
    main()
            
def pause(paused, astro, Textbox, allsprites, screen):
    setattr(astro, "active", False)
    while paused:
        Textbox.textboxes[3]._swap("Paused")
        for text in Textbox.textboxes:
            text.update()
        allsprites.draw(screen)       
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                astro.active = True
                paused = False
                Textbox.textboxes[3]._kill()

                
def main():
    pygame.init()
    screen = pygame.display.set_mode((1000, 800))
    pygame.display.set_caption('Gravity')
    pygame.mouse.set_visible(1)

    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill(BLACK)
    
    screen.blit(background, (0, 0))
    pygame.display.flip()

    clock = pygame.time.Clock()
    time = 0
    time_passed = 0
    
    planets = pygame.sprite.Group()
    planet0 = Planet(500, 500, 100)
    planet1 = Planet(150, 600, 50)
    planet2 = Planet(750, 250, 25)
    planet3 = Planet(200, 145, 50)
    planet4 = Planet(700, 800, 75)
    suns = pygame.sprite.Group()
    score = Textbox(screen, WHITE, 10, 16, LEFT)
    hscore = Textbox(screen, WHITE, 10, 50, LEFT)
    warning = Textbox(screen, WHITE, 1000, 16, RIGHT)
    pause_txt = Textbox(screen, WHITE, 500, 350, CENTER)
    bonus_txt = Textbox(screen, GREEN, 500, 16, CENTER)
    centgrav = CentGrav()

    if ml:
        flip = False
        trial_txt = Textbox(screen, WHITE, 1000, 785, RIGHT)
        trial_txt._swap(str("Round " + str(ml_round) + ", Trial " + str(ml_trial) + ", Seed " + str(ml_coord)))
        if ml_trial == 1:
            ml_polar = (ml_coord.x, ml_coord.y) #convert x and y of winner into polar coordinates
            gauss = GaussArray(ml_trials, rng)
            gauss.output(ml_coord.x, ml_coord.y)
    #suns.add(sun)
    #lines = pygame.sprite.Group()
    astro = Astro([0, 0])
    dragging = False
    mousepos = (0, 0)
    mousemove = pygame.mouse.get_pos()
    place = ""
    gameover = ""
    bonus_box = ""
    place = "Click and Drag to Fire the Ball"
    score._swap(place)

    allsprites = pygame.sprite.LayeredUpdates((Planet.planets, astro, centgrav))
    allsprites.move_to_front(centgrav)
    centgrav.change(Planet.planets)
    #allsprites.add

    
############## GOING GOING GOING ############## GOING GOING GOING ############## GOING GOING GOING ############## GOING GOING GOING ##############   
############## GOING GOING GOING ############## GOING GOING GOING ############## GOING GOING GOING ############## GOING GOING GOING ##############    
############## GOING GOING GOING ############## GOING GOING GOING ############## GOING GOING GOING ############## GOING GOING GOING ##############

    going = True
    while going:
        clock.tick(60)
        screen.blit(background, (0, 0))
        time += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                going = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                going = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                if ml:
                    global autoend
                    if autoend:
                        autoend = False
                    else:
                        autoend = True
                else:
                    reset(allsprites, Textbox, False)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_p and astro.active:
                paused = True
                pause(paused, astro, Textbox, allsprites, screen)
            if not ml:
                if (event.type == pygame.MOUSEBUTTONDOWN): #& (pygame.mouse.get_pressed(num_buttons=3) == [1, 0, 0]
                    mousepos = pygame.mouse.get_pos()
                    if (astro.rect.collidepoint(mousepos[0], mousepos[1])) & (astro.active == False):
                        dragging = True

                elif (event.type == pygame.MOUSEMOTION) & dragging:
                    mousemove = pygame.mouse.get_pos()
                elif (event.type == pygame.MOUSEBUTTONUP) & dragging:
                    velo = []
                    mousemove2 = mousemove
                    zipobj = zip(mousepos, mousemove2)
                    for list_1, list_2 in zipobj:
                        velo.append(list_1 - list_2)
                    if (abs(velo[0]) + 1) * (abs(velo[1]) + 1) > 12.5:
                        astro.startvelocity = pygame.Vector2(velo[0] / 7, velo[1] / 7)
                        astro.velocity = astro.startvelocity
                        astro.active = True
                    dragging = False

                    
        if ml & (astro.active == False):
            astro.startvelocity = ml_coord
            if time > 20:
                randx = round_array[ml_trial-1][0]
                randy = round_array[ml_trial-1][1]
                astro.startvelocity.x = randx
                astro.startvelocity.y = randy
                astro.velocity = astro.startvelocity
                astro.active = True
                time = 0
                warning._swap(str(round_array[ml_trial-1]))




                
        if dragging:
            linedraw(screen, mousemove, astro.rect.center)
        if astro.active:
            time += 1
            score._kill()
            place = "Score: "
            score._swap(place + str(astro.score))
            if len(Planet.planets) < 1:#############
                time_wait = 30
                time_passed += 1
                if time_passed > time_wait:
                    time_bonus = max(250 * (30 - int(time/60)), 0)
                    astro.score += time_bonus
                    astro.active = False
                    killswitch = killscreen(astro, Planet, allsprites, Textbox, centgrav)
                    time_passed = 0
                    if time_bonus > 0:
                        bonus_box = "Time Bonus! +" + str(time_bonus)
                    for sprite in allsprites:
                        sprite.kill()
                    place, gameover = killswitch[0], killswitch[1]
                    bonus_txt._swap(bonus_box)
            if astro.collided > (delay - 180):
                countdown = "No collision detected, ending round in: "
                timer = 3
                if astro.collided > (delay - 120):
                    timer = 2
                    if astro.collided > (delay - 60):
                        timer = 1
                        if astro.collided > delay:
                            warning._kill()
                            astro.active, astro.collided = False, 0
                            killswitch = killscreen(astro, Planet, allsprites, Textbox, centgrav)
                            place, gameover = killswitch[0], killswitch[1]
                countdown += str(timer)
                #warning._swap(countdown)
##            else:
##                warning._kill()

        #astro._collide(planets)

        allsprites.update(Planet.planets, suns, centgrav)
        allsprites.draw(screen)
        hscore._swap("High Score: " + str(high_score))
        pause_txt._swap(gameover)
        #warning._swap(str(int(clock.get_fps()))) #nice for debug
        for textbox in Textbox.textboxes:
            textbox.update()
        pygame.display.update()
    pygame.quit()
    quit()
    
if __name__ == "__main__":
    main()












