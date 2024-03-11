from collections import defaultdict

from pyglet.image import load, ImageGrid, Animation
from pyglet.window import key

import cocos.layer
import cocos.sprite
import cocos.collision_model as cm
import cocos.euclid as eu
from cocos.menu import *
from cocos.actions import *
from cocos.scenes import FadeTransition

from cocos.audio.pygame.mixer import Sound
from cocos.audio.pygame import mixer

import cocos.particle_systems as ps
import pygame

import random

#Actor
class Actor(cocos.sprite.Sprite):
    def __init__(self,image, x, y):
        super(Actor, self).__init__(image)
        #self.scale = 1.5
        self.position = eu.Vector2(x, y)
        self.cshape = cm.AARectShape(self.position, self.width * 0.07, self.height * 0.35)

    def move(self, offset):
        self.position += offset
        self.cshape.center += offset


    def update(self, elapsed):
        pass

    def collide(self, other):
        pass
    
#Player
class Player(Actor):
    KEYS_PRESSED = defaultdict(int)
    def __init__(self, image, x, y):
        super(Player, self).__init__(image, x, y)
        #player move
        self.speed = eu.Vector2(300, 0)
        self.jumpspeed = eu.Vector2(0, 100)
        self.gravity = eu.Vector2(0, -10)
        self.scale = 1.25

        #player imfo
        self.lives = 7

        #player state
        self.is_ground = False
        self.go_right = True
        self.state = 0 #['idle', 'run']

        self.attack = False
        self.spell = False
        self.attack_temp = 0
        self.combo_count = 0
        self.attack_scale = 0

        self.restart = False

        self.in_bossroom = False
        self.in_kingroom = False

        self.slide = False
        self.slide_temp = 0

        self.isHit = False
        self.isHit_temp = 0

        self.state_list = [[self.is_ground, self.is_ground], \
            [self.go_right, self.go_right], \
            [self.state, self.state], \
            [self.attack, self.attack], \
            [self.slide, self.slide]]
        self.sound()
        
        
    def sound(self):
        pygame.init()
        self.slash_song = pygame.mixer.Sound("sound/character sword.wav")
        self.slash_song.set_volume(0.2)
        self.jump_song = pygame.mixer.Sound("sound/character jump.wav")
        self.jump_song.set_volume(0.3)
        self.hit_song = pygame.mixer.Sound("sound/character hit.wav")
        self.hit_song.set_volume(0.05)
        self.slide_song = pygame.mixer.Sound("sound/swipe.wav")
        self.spell_song = pygame.mixer.Sound("sound/fireball3.wav")
        self.spell_song.set_volume(0.2)

    def update(self, elapsed):
        pressed = Player.KEYS_PRESSED

        #scroll 고정
        scroller1.set_focus(self.x, self.y)
        scroller2.set_focus(self.x, self.y)


        #movement
        movement = pressed[key.RIGHT] - pressed[key.LEFT]
        jump = pressed[key.SPACE]
        attack = pressed[key.Z]
        spell = pressed[key.X]
        slide = pressed[key.LSHIFT]
        restart = pressed[key.R]

        w = self.width * 0.5

        if pressed[key.RIGHT] != 0 or pressed[key.LEFT] != 0:
            self.state = 1
            self.update_state(self.state, 2)
        else:
            self.state = 0
            self.update_state(self.state, 2)

        if movement != 0: #좌우 이동
            self.move(self.speed * movement * elapsed)
            if self.x < w :
                self.x = w
            elif self.x > self.parent.width - w:
                self.x = self.parent.width - w
            self.cshape.center = self.position

        if self.in_bossroom:
            if self.x < 450:
                self.x = 450
            elif self.x > 950:
                self.x = 950
            self.cshape.center = self.position

        if self.in_kingroom:
            if self.x < 1000:
                self.x = 1000
            elif self.x > 1900:
                self.x = 1900
            self.cshape.center = self.position

        #우측 이동
        if movement == -1:
            self.go_right = False
            self.update_state(self.go_right, 1)
            self.attack = False
            self.update_state(self.attack, 3)
        elif movement == 1:
            self.go_right = True
            self.update_state(self.go_right, 1)
            self.attack = False
            self.update_state(self.attack, 3)
            

        #점프start
        if jump != 0 and self.is_ground: #점프(상하이동)
            self.do(Jump(100, 100*movement, 1, 0.5))
            self.is_ground = False
            self.jump_song.play()
            

        # 공격
        if SwordEffect.INSTANCE is None and attack: #and self.state_list[2][1] != 1
            self.attack = True
            self.update_state(self.attack, 3)
            self.slash_song.play()
            
            if self.state_list[3][0] != self.state_list[3][1]:
                if self.state_list[3][1]:
                    if self.state_list[1][1] == 1:
                        effect_type = SwordEffect.TYPE[2]
                        sword_effect = SwordEffect(effect_type, self.x, self.y)
                    else:
                        effect_type = SwordEffect.TYPE[2].get_transform(True, False, 0)
                        sword_effect = SwordEffect(effect_type, self.x, self.y)
                    
                    sword_effect.set_scale(1 + 1 * self.attack_scale)
                    sword_effect.cshape = cm.AARectShape(sword_effect.position, sword_effect.width, sword_effect.height)
                    self.parent.add(sword_effect)

        #spell
        if SpellEffect.INSTANCE is None and spell:
            self.attack = True
            self.update_state(self.attack, 3)
            self.spell_song.play()

            if self.state_list[3][0] != self.state_list[3][1]:
                if self.state_list[3][1]:
                    effect_type = SpellEffect.TYPE[1]
                    if self.state_list[1][1] == 1:
                        spell_effect = SpellEffect(effect_type, self.x + 100, self.y)
                    else:
                        spell_effect = SpellEffect(effect_type, self.x - 100, self.y)
                    
                    self.parent.add(spell_effect)


        if self.attack:
            self.attack_temp += elapsed
        if self.attack_temp >= 0.25:
            self.attack = False
            self.update_state(self.attack, 3)
            self.attack_temp = 0

        if slide:
            self.slide = True
            self.update_state(self.slide, 4)
            self.speed = eu.Vector2(500, 0)
            self.slide_song.play()
        if self.slide:
            self.slide_temp += elapsed
        if self.slide_temp >= 0.25:
            self.slide = False
            self.update_state(self.slide, 4)
            self.speed = eu.Vector2(300, 0)
        if self.slide_temp >= 0.27:
            self.slide_temp = 0

        #print(self.attack_temp)
   
        #땅에 닿아 있는지
        if not self.is_ground:
            self.move(self.gravity)
            self.update_state(self.is_ground, 0)


        if self.isHit:
            self.isHit_temp += elapsed
            if self.isHit_temp < 0.03: self.hit_song.play()
        if self.isHit_temp >= 1:
            self.isHit = False
            self.isHit_temp = 0

        if restart:
            self.restart = True

        #collision model update
        self.cshape.center = self.position

        
    def collide(self, other):
        pass


    def get_position(self):
        return self.position

    def change_img(self, image):
        self.image = image

    def update_state(self, state, index):
        del self.state_list[index][0]
        self.state_list[index].append(state)
        
#Enemy

class Enemy(Actor):
    def __init__(self,image, x, y):
        super(Enemy, self).__init__(image, x, y)
        self.scale = 1.75
        self.speed = eu.Vector2(-30, 0)
        self.jumpspeed = eu.Vector2(0, 100)
        self.gravity = eu.Vector2(0, -10)
        self.cshape = cm.AARectShape(self.position, self.width * 0.07, self.height * 0.1)

        self.is_ground = False

    def update(self, elapsed):
        self.move(self.speed * elapsed)

        if not self.is_ground:
            self.move(self.gravity)

        self.cshape.center = self.position

    def collide(self, other):
        pass

class Enemy_bat(Enemy):
    def __init__(self,image, x, y):
        super(Enemy_bat, self).__init__(image, x, y) 
        self.speed = 3
        self.velocity = eu.Vector2(-50, 0)
        self.max_force = 5
        self.max_velocity = 200

        self.target = None

    def update(self, elapsed):
        if self.target is not None:
            self.pursuit(self.target, elapsed)
        self.position += self.velocity * elapsed
        self.cshape.center = self.position

    def truncate(self, vector, m): # limits vector
        magnitude = abs(vector)
        if magnitude > m:
            vector *= m / magnitude
        return vector

    def pursuit(self, target, dt):
        pos = target.position

        if target.go_right == True:
            target_velocity = eu.Vector2(10, 0)
        else:
            target_velocity = eu.Vector2(-10, 0)
        
        future_pos = pos + target_velocity * dt
        distance = future_pos - eu.Vector2(self.x, self.y)
        steering = distance * self.speed - self.velocity
        steering = self.truncate(steering, self.max_force)
        self.velocity = self.truncate(self.velocity + steering, self.max_velocity)
        
class Enemy_slime(Enemy):
    def __init__(self,image, x, y):
        super().__init__(image, x, y) 
        self.jump_temp = 0
        self.jump = False
        self.speed = eu.Vector2(-30, 0)
        self.jumpspeed = eu.Vector2(0, 100)
        self.gravity = eu.Vector2(0, -10)
        self.cshape = cm.AARectShape(self.position, self.width * 0.07, self.height * 0.1)


    def update(self, elapsed):
        self.move(self.speed * elapsed)

        self.jump_temp += elapsed

        if self.jump_temp >= 3 and self.is_ground: #점프(상하이동)
            self.do(Jump(100, 1 * self.speed[0], 1, 0.5))
            self.is_ground = False
            self.jump_temp = 0
            if not self.jump:
                self.jump = True

        if self.position[0] <= self.width * 0.5 or self.position[0] >= self.parent.width - (self.width * 0.5):
            self.speed *= -1

        if not self.is_ground:
            self.move(self.gravity)
        else:
            if self.jump:
                self.jump = False

        self.cshape.center = self.position

    def collide(self, other):
        pass

class Enemy_ghoul(Enemy):
    def __init__(self,image, x, y):
        super(Enemy_ghoul, self).__init__(image, x, y) 
        self.life = 1
        self.life_temp = 0
        self.lost_life = False
        self.speedForce = 70
        self.speed = eu.Vector2(-70, 0)
        self.target = None
        self.scale = 1.4
        self.sound()

    def sound(self):
        pygame.init()
        self.ghoul_song = pygame.mixer.Sound("sound/burning-ghoul.wav")
        self.ghoul_song.set_volume(0.01)


    def update(self, elapsed):
        self.speedForce += 1.5

        if self.lost_life:
            self.life_temp += elapsed
            if self.life_temp >= 0.5:
                self.lost_life = False
                self.life_temp = 0

        if self.target is not None:
            if abs(self.target.position[0] - self.position[0]) <= 500:
                self.ghoul_song.play()
            if self.target.position[0] < self.position[0]:
                self.speed = eu.Vector2(-self.speedForce, 0)
            elif self.target.position[0] > self.position[0]:
                self.speed = eu.Vector2(self.speedForce, 0)

        self.move(self.speed * elapsed)

        if self.position[0] <= self.width * 0.5 or self.position[0] >= self.parent.width - (self.width * 0.5):
            self.speed *= -1

        if not self.is_ground:
            self.move(self.gravity)

        self.cshape.center = (self.position[0], self.position[1])

class Enemy_wizard(Enemy):
    def __init__(self,image, x, y):
        super(Enemy_wizard, self).__init__(image, x, y)
        self.temp = 0
        self.life = 1
        self.lost_life = False
        self.life_temp = 0
        self.attack = False
        self.fireball = None
        self.state = [self.attack, self.attack]
        self.sound()
        self.target = None

    def sound(self):
        pygame.init()
        self.wizard_fireball_song = pygame.mixer.Sound("sound/fireball3.wav")
        self.wizard_fireball_song.set_volume(0.1)

    def update(self, elapsed):
        self.temp += elapsed

        if self.lost_life:
            self.life_temp += elapsed
            if self.life_temp >= 0.5:
                self.lost_life = False
                self.life_temp = 0

        if self.temp >= 6:
            self.attack = True
            del self.state[0]
            self.state.append(self.attack)

            if self.temp >= 7:
                self.fireball = EnemyFireBall(EnemyFireBall.ANIM2, self.x, self.y)
                EnemyFireBall.INSTANCE = self.fireball
                if self.target is not None:
                    self.fireball.target = self.target
                self.parent.add(self.fireball)
                self.wizard_fireball_song.play()

                self.temp = 0
                self.attack = False
                del self.state[0]
                self.state.append(self.attack)
        else:
            self.attack = False
            del self.state[0]
            self.state.append(self.attack)

class Enemy_fireworm(Enemy):
    def __init__(self,image, x, y):
        super(Enemy_fireworm, self).__init__(image, x, y)
        self.temp = 0
        self.life = 1
        self.lost_life = False
        self.life_temp = 0
        self.attack = False
        self.fireball = None
        self.state = [self.attack, self.attack]
        self.sound()

    def sound(self):
        pygame.init()
        self.fireworm_fireball_song = pygame.mixer.Sound("sound/fireball2.wav")
        self.fireworm_fireball_song.set_volume(0.1)

    def update(self, elapsed):
        self.temp += elapsed

        if self.lost_life:
            self.life_temp += elapsed
            if self.life_temp >= 0.5:
                self.lost_life = False
                self.life_temp = 0

        if self.temp >= 6:
            self.attack = True
            del self.state[0]
            self.state.append(self.attack)
            self.fireworm_fireball_song.play()

            if self.temp >= 7:
                self.fireball = EnemyFireBall(EnemyFireBall.ANIM3, self.x, self.y)
                EnemyFireBall.INSTANCE = self.fireball
                self.fireball.type = 1
                self.parent.add(self.fireball)

                self.temp = 0
                self.attack = False
                del self.state[0]
                self.state.append(self.attack)
        else:
            self.attack = False
            del self.state[0]
            self.state.append(self.attack)
        
class Priest(Enemy):
    IMAGE1 = [load("img/Enemy/priest/cultist_priest_idle_1.png"), \
        load("img/Enemy/priest/cultist_priest_idle_2.png"), \
        load("img/Enemy/priest/cultist_priest_idle_3.png"), \
        load("img/Enemy/priest/cultist_priest_idle_4.png"), \
        load("img/Enemy/priest/cultist_priest_idle_5.png")]
    IMAGE2 = [load("img/Enemy/priest/cultist_priest_attack_1.png"), \
        load("img/Enemy/priest/cultist_priest_attack_2.png"), \
        load("img/Enemy/priest/cultist_priest_attack_3.png"), \
        load("img/Enemy/priest/cultist_priest_attack_4.png"), \
        load("img/Enemy/priest/cultist_priest_attack_5.png")]

    ANIM1 = Animation.from_image_sequence(IMAGE1, duration = 0.1)
    ANIM2 = Animation.from_image_sequence(IMAGE2, duration = 0.1, loop = False)
    ANIM3 = ANIM1.get_transform(True, False, 0)


    def __init__(self,image, x, y):
        super(Priest, self).__init__(image, x, y)
        self.temp = 0
        self.target = None
        self.scale = 0.5
        self.is_attack = False
        self.range = [-30, -20, -10, 10, 20, 30]
        self.state_list = [[self.is_attack, self.is_attack]]
        self.sound()

    def sound(self):
        pygame.init()
        self.priest_attack_song = pygame.mixer.Sound("sound/fireball.wav")
        self.priest_attack_song.set_volume(0.3)

    def update(self, elapsed):
        self.temp += elapsed

        if self.temp >= 5.3:
            self.is_attack = True
            self.update_state(self.is_attack, 0)
            if self.temp >= 6:
                if self.target is not None:
                    rand = random.choice(self.range)
                    pos = self.target.position
                    self.spell = BossSpellEffect(BossSpellEffect.TYPE[5], pos[0] + rand, pos[1])
                    self.spell.type = 5
                    self.parent.add(self.spell)
                    self.temp = 0
                    self.is_attack = False
                    self.update_state(self.is_attack, 0)
        else:
            self.is_attack = False
            self.update_state(self.is_attack, 0)

        if self.state_list[0][0] != self.state_list[0][1]:
            if self.state_list[0][1]:
                self.priest_attack_song.play()
                self.image = Priest.ANIM2
            else:
                self.image = Priest.ANIM1

        self.cshape.center = self.position

    def update_state(self, state, index):
        del self.state_list[index][0]
        self.state_list[index].append(state)
      
class Boss(Actor):
    def __init__(self, image, x, y):
        super(Boss, self).__init__(image, x, y)
        self.scale = 1.75
        self.speed = eu.Vector2(-30, 0)
        self.gravity = eu.Vector2(0, -10)
        self.position = (self.position[0], self.position[1] + 30)
        self.cshape = cm.AARectShape(self.position, self.width * 0.07, self.height * 0.3)

        self.ran_attack = random.randint(1, 3)
        self.temp_attacktime = 0

        self.is_player_around = False
        self.attack = False
        self.state_list = [[self.attack, self.attack]]
        self.cool_time = False
        self.target = None

        self.lost_life = False
        self.life_temp = 0
        self.life = 5

        self.is_ground = False
        self.sound()

    def sound(self):
        pygame.init()
        self.boss_fireball_song = pygame.mixer.Sound("sound/boss_fireball.wav")
        self.boss_fireball_song.set_volume(0.05)
        self.boss_magicball_song = pygame.mixer.Sound("sound/magicball.wav")
        self.boss_magicball_song.set_volume(0.3)
        self.boss_magic_song = pygame.mixer.Sound("sound/boss_magic.wav")
        self.boss_magic_song.set_volume(0.1)
        


    def update(self, elapsed):
        
        #print(self.state_list)
        #print(self.temp)

        if self.is_player_around:
            self.temp_attacktime += elapsed
            
            if self.temp_attacktime < 1 and self.temp_attacktime > 0.97:
                self.position = (random.randint(600, 800), random.randint(130, 400))
                self.cshape.center = self.position
            elif self.temp_attacktime <= 2.5 and self.temp_attacktime > 2.2:
                self.attack = True
                self.update_state(self.attack, 0)
                self.rand_attack = random.randint(1, 3)
            else:
                self.attack = False
                self.update_state(self.attack, 0)
                if self.temp_attacktime >= 7:
                    self.temp_attacktime = 0
        else:
            self.attack = False
            self.update_state(self.attack, 0)
            self.temp_attacktime = 0

        if self.lost_life:
            self.life_temp += elapsed
        if self.life_temp >= 2.5:
            self.lost_life = False
            self.life_temp = 0
        
        #print(self.lost_life)

        if self.state_list[0][0] != self.state_list[0][1]:
            if self.state_list[0][1]:
                self.spell = BossSpellEffect(BossSpellEffect.TYPE[self.rand_attack], self.x, self.y)
                self.spell.type = self.rand_attack
                if self.target is not None:
                    self.spell.target = self.target
                self.parent.add(self.spell)
                if self.rand_attack == 1:
                    self.boss_fireball_song.play()
                elif self.rand_attack == 2:
                    self.boss_magic_song.play()
                elif self.rand_attack == 3:
                    self.boss_magicball_song.play()

        if self.position[0] <= self.width * 0.5 or self.position[0] >= self.parent.width - (self.width * 0.5):
            self.speed *= -1

        if not self.is_ground:
            self.move(self.gravity)

        self.cshape.center = self.position

    def collide(self, other):
        pass

    def change_img(self, image):
        self.image = image

    def update_state(self, state, index):
        del self.state_list[index][0]
        self.state_list[index].append(state)
    
class King(Actor):
    def __init__(self, image, x, y):
        super(King, self).__init__(image, x, y)
        self.scale = 1.75
        self.speed = eu.Vector2(-5, 0)
        self.gravity = eu.Vector2(0, -10)
        self.position = (self.position[0], self.position[1] + 60)
        self.cshape = cm.AARectShape(self.position, self.width * 0.07, self.height)

        self.temp = 0
        self.temp_attack1 = 0
        self.temp_attack2 = 0
        self.temp_attack3 = 0
        self.temp_spawn = 0
        self.spawn = False
        self.is_spawned = False

        self.is_player_around = False
        self.is_player_left = False
        self.is_attack = False
        self.is_chasing = False
        self.attack = 0
        
        self.cool_time = False
        self.target = None
        self.range = [-30, -20, -10, 10, 20, 30]

        self.lost_life = False
        self.life_temp = 0
        self.life = 3

        self.is_ground = False
        self.state_list = [[self.is_player_left, self.is_player_left], [self.attack, self.attack], [self.is_chasing, self.is_chasing], \
            [self.lost_life, self.lost_life]]
        

    def update(self, elapsed):
         
        self.temp += elapsed
        self.temp_spawn += elapsed

        #print(self.spawn)

        if self.temp_spawn > 7:
            if not self.is_spawned:
                self.spawn = True
                self.temp_spawn = 0
                self.is_spawned = True

        if self.target is not None:
            distance = self.target.position[0] - self.position[0]

            if self.target.position[0] < self.position[0]:
                self.is_player_left = True
                self.update_state(self.is_player_left, 0)
            else:
                self.is_player_left = False
                self.update_state(self.is_player_left, 0)

            if not self.is_attack:
                if abs(distance) < 500:
                    self.is_chasing = True
                    self.update_state(self.is_chasing, 2)

                    if distance < 0: #left
                        self.speed = eu.Vector2(-1, 0)
                    else:
                        self.speed = eu.Vector2(1, 0)
                    self.move(self.speed)
                else:
                    self.is_chasing = False
                    self.update_state(self.is_chasing, 2)

        if self.temp > 6:
            self.is_attack = True
            self.cshape = cm.AARectShape(self.position, self.width * 0.33, self.height)
            if self.temp_attack3 >= 1:
                if self.target is not None:
                    rand = random.choice(self.range)
                    pos = self.target.position
                    self.spell = BossSpellEffect(BossSpellEffect.TYPE[4], pos[0] + rand, pos[1] + 20)
                    self.spell.type = 4
                    self.parent.add(self.spell)
                self.temp = 0
                self.temp_attack1 = 0
                self.temp_attack2 = 0
                self.temp_attack3 = 0
                self.attack = 0
                self.cshape = cm.AARectShape(self.position, self.width * 0.07, self.height)
                self.update_state(self.attack, 1)
            elif self.temp_attack2 >= 1:
                self.temp_attack3 += elapsed
                self.attack = 3
                self.update_state(self.attack, 1)
            elif self.temp_attack1 >= 1:
                self.temp_attack2 += elapsed
                self.attack = 2
                self.update_state(self.attack, 1)
            else:
                self.temp_attack1 += elapsed
                self.attack = 1
                self.update_state(self.attack, 1)

        else:
            self.is_attack = False
            self.attack = 0
            self.update_state(self.attack, 1)

        if self.lost_life:
            self.update_state(self.lost_life, 3)
            self.life_temp += elapsed
        else:
            self.lost_life = False
            self.update_state(self.lost_life, 3)

        if self.life_temp >= 1.5:
            self.lost_life = False
            self.update_state(self.lost_life, 3)
            self.life_temp = 0
        
        if self.position[0] <= self.width * 0.5:
           self.position = (self.width * 0.5, self.position[1])
        elif self.position[0] >= self.parent.width - (self.width * 0.5):
           self.position = (self.parent.width - (self.width * 0.5), self.position[1])
           
        if not self.is_ground:
            self.move(self.gravity)

        self.cshape.center = self.position

    def collide(self, other):
        pass

    def change_img(self, image):
        self.image = image

    def update_state(self, state, index):
        del self.state_list[index][0]
        self.state_list[index].append(state)

#NPC

class NPC(Actor):
    def __init__(self,image, x, y):
        super(NPC, self).__init__(image, x, y)
        self.scale = 2
        #self.position = (self.position[0], self.position[1])
        self.cshape = cm.AARectShape(self.position, self.width * 0.07, self.height * 0.1)
       
        self.gravity = eu.Vector2(0, -10)

        self.is_ground = False
        self.state = False
        self.state_list = [[self.state, self.state]]
        self.chat = None
        self.chat_type = 4 #1, 2, 3, 4

    def update(self, elapsed):
        if not self.is_ground:
            self.move(self.gravity)

        self.update_state(self.state, 0)

        #chat
        if self.state_list[0][0] != self.state_list[0][1]:
            if self.state_list[0][1]:
                self.chat = Chat(Chat.TYPE[self.chat_type], self.x, self.y + 70)
                self.chat.scale = 0.8
                self.parent.add(self.chat)
            else:
                if self.chat is not None:
                    self.chat.kill()
        

        self.cshape.center = self.position


    def collide(self, other):
        pass

    def change_img(self, image):
        self.image = image

    def update_state(self, state, index):
        self.state_list[index].append(state)
        del self.state_list[index][0]

class NPC1(NPC):
    def __init__(self,image, x, y):
        super(NPC1, self).__init__(image, x, y)
        self.position = (self.position[0], self.position[1] + 10)
        self.chat = None
        self.type = 1

    def update(self, elapsed):
        if not self.is_ground : self.move(self.gravity)

        self.update_state(self.state, 0)

        if self.state_list[0][0] != self.state_list[0][1]:
            if self.state_list[0][1]:
                self.chat = Chat(Chat.TYPE[self.type], self.x, self.y + 50)
                self.parent.add(self.chat)
            else:
                if self.chat is not None:
                    self.chat.kill()

#Tile

class Tile(cocos.sprite.Sprite):
    def __init__(self, image, x, y):
        super(Tile, self).__init__(image)
        self.position  = eu.Vector2(x, y)
        self.cshape = cm.AARectShape(self.position, self.width * 0.5, self.height * 0.5)

    def update(self, elapsed):
        pass

    def collide(self, other):
        pass

class Platform(Tile):
    img1 = load('img/Platform/ExTile.png')
    img2 = load('img/Platform/ExTile2.png')
    #self.platform.image_anchor = (Platform.img2.width/2, Platform.img2.height/3)
    img3 = load('img/Platform/ExTile3.png')
    #self.platform.image_anchor = (Platform.img3.width/2, Platform.img3.height/3)
    img4 = load('img/Platform/ExTile4.png')
    #self.platform.image_anchor = (Platform.img4.width/2, Platform.img4.height/3)
    img5 = load('img/Platform/ExTile5.png')
    #self.platform.image_anchor = (Platform.img5.width/2, Platform.img5.height/3)


    def __init__(self, x, y):
        super(Platform, self).__init__('img/Platform/ExTile.png', x, y)

class Spike(Tile):
    def __init__(self, x, y):
        super(Spike, self).__init__('img/Traps/Spike.png', x, y)
        self.position = self.position[0], self.position[1] - 5
        self.cshape = cm.AARectShape(self.position, self.width * 0.2, self.height * 0.2)

class Trap(Tile):
    seq = ImageGrid(load('img/Traps/Spike_Trap.png'), 1, 14)
    ANIM1 = Animation.from_image_sequence(seq, duration = 0.2)

    def __init__(self, x, y):
        super(Trap, self).__init__(Trap.ANIM1, x, y)
        self.position = self.position[0], self.position[1]
        self.cshape = cm.AARectShape(self.position, self.width * 0.2, self.height * 0.2)
        self.is_able = False
        self.temp = 0.15

    def update(self, elapsed):
        self.temp += elapsed

        if self.temp >= 2.4:
            if self.temp < 2.8:
                self.is_able = True
            else:
                self.is_able = False
                if self.temp >= 2.91:
                    self.temp = 0

#Effect

class SwordEffect(Actor):
    IMAGE1 = [load('img/Effect1/B001.png'),\
                    load('img/Effect1/B002.png'),\
                    load('img/Effect1/B003.png'),\
                    load('img/Effect1/B004.png'),\
                    load('img/Effect1/B005.png'),\
                    load('img/Effect1/B006.png'),\
                    load('img/Effect1/B007.png'),\
                    load('img/Effect1/B008.png'),\
                    load('img/Effect1/B009.png'),\
                    load('img/Effect1/B010.png')]
    IMAGE2 = [load('img/Effect2/FX001.png'),\
        load('img/Effect2/FX002.png'),\
        load('img/Effect2/FX003.png'),\
        load('img/Effect2/FX004.png'),\
        load('img/Effect2/FX005.png'),\
        load('img/Effect2/FX006.png'),\
        load('img/Effect2/FX007.png'),\
        load('img/Effect2/FX008.png'),\
        load('img/Effect2/FX009.png'),\
        load('img/Effect2/FX010.png'),\
        load('img/Effect2/FX011.png'),\
        load('img/Effect2/FX012.png'),\
        load('img/Effect2/FX013.png'),\
        load('img/Effect2/FX014.png'),\
        load('img/Effect2/FX015.png'),\
        ]
    ANIM1 = Animation.from_image_sequence(IMAGE1, duration = 0.01, loop = False)
    ANIM2 = Animation.from_image_sequence(IMAGE2, duration = 0.01, loop = False)
    TYPE = {1 : ANIM1.get_transform(True, False, 0),\
        2: ANIM2}

    INSTANCE = None

    def __init__(self, image, x, y):
        super(SwordEffect, self).__init__(image, x, y)
        SwordEffect.INSTANCE = self
        self.enemy_list = [Enemy_ghoul, Enemy_wizard, Enemy_fireworm, Boss, King]
        self.cshape = cm.AARectShape(self.position, self.width, self.height)
        self.sound()
        self.temp = 0

    def sound(self):
        pygame.init()
        self.monster_die_song1 = pygame.mixer.Sound("sound/monster die2.wav")
        self.monster_die_song1.set_volume(0.3)
        self.monster_die_song2 = pygame.mixer.Sound("sound/monster die.wav")
        self.monster_die_song2.set_volume(0.1)
        self.monster_die_song3 = pygame.mixer.Sound("sound/monster die3.wav")
        self.monster_die_song3.set_volume(0.1)
        self.king_hit_song = pygame.mixer.Sound("sound/king hit.wav")
        self.king_hit_song.set_volume(0.1)
        self.king_die_song = pygame.mixer.Sound("sound/king die.wav")
        self.king_die_song.set_volume(0.1)
        self.boss_die_song = pygame.mixer.Sound("sound/boss die.wav")
        self.boss_die_song.set_volume(0.1)

    def update(self, elapsed):
        self.temp += elapsed

        if self.temp > 0.3:
            self.kill()

    def collide(self, other):
        if isinstance(other, Enemy) or isinstance(other, Boss) or isinstance(other, King):
            if type(other) in self.enemy_list:
                if not other.lost_life:
                    if other.life == 1:
                        other.life -= 1
                        print("should kill")
                        self.parent.add(Explosion(other.position, ps.Color(1.0, 0.0, 0.0, 0.2)))
                        other.kill()
                        if isinstance(other, King):
                             self.king_die_song.play()
                        elif isinstance(other, Boss):
                            self.boss_die_song.play()
                        else:
                            self.monster_die_song3.play()
                    else:
                        other.do(Blink(3, 0.5))
                        other.life -= 1
                        other.lost_life = True
                        if isinstance(other, King):
                            self.king_hit_song.play()
                        elif isinstance(other, Boss):
                            self.monster_die_song2.play()
                        else:
                            self.monster_die_song2.play()

            else: 
                self.parent.add(Explosion(other.position,  ps.Color(1.0, 0.0, 0.0, 0.2)))
                self.monster_die_song1.play()
                other.kill()

        if isinstance(other, EnemyFireBall):
            other.kill()

    def set_scale(self, scale):
        self.scale = scale


    def on_exit(self):
        super(SwordEffect, self).on_exit()
        SwordEffect.INSTANCE = None

class Heart(Actor):
    heart = [load('img/Player/HP/0.png'), \
                    load('img/Player/HP/1.png'), \
        load('img/Player/HP/2.png'), \
        load('img/Player/HP/3.png'), \
        load('img/Player/HP/4.png'), \
        load('img/Player/HP/5.png'), \
        load('img/Player/HP/6.png')]

    def __init__(self, image, x, y):
        super(Heart, self).__init__(image, x, y)
        self.scale = 0.17

    def set_position(self, player):
        pos = player.get_position()
        if pos[0] >= 330 : 
            if pos[0] >= self.parent.width - 350: self.position = self.parent.width - 550, 450
            else: self.position = pos[0] - 230, 450
        else: self.position = 100, 450

        if player.in_bossroom:
            self.position = 480, 450
        elif player.in_kingroom:
            self.position = 1200, 450


    def change_img(self, image):
        self.image = image

class SpellEffect(Actor):
    seq = ImageGrid(load('img/cauterize.png'), 6, 6)
    ANIM1 = Animation.from_image_sequence(seq, duration = 0.01, loop = False)

    TYPE = {1 : ANIM1}

    INSTANCE = None

    def __init__(self, image, x, y):
        super(SpellEffect, self).__init__(image, x, y)
        self.temp = 0
        SpellEffect.INSTANCE = self
        self.cshape = cm.AARectShape(self.position, self.width * 0.05, self.height * 0.05)
        self.enemy_list = [Enemy_ghoul, Enemy_wizard, Enemy_fireworm, Boss, King]
        self.sound()

    def sound(self):
        pygame.init()
        self.monster_die_song1 = pygame.mixer.Sound("sound/monster die2.wav")
        self.monster_die_song1.set_volume(0.3)
        self.monster_die_song2 = pygame.mixer.Sound("sound/monster die.wav")
        self.monster_die_song2.set_volume(0.1)
        self.monster_die_song3 = pygame.mixer.Sound("sound/monster die3.wav")
        self.monster_die_song3.set_volume(0.1)
        self.king_hit_song = pygame.mixer.Sound("sound/king hit.wav")
        self.king_hit_song.set_volume(0.1)
        self.king_die_song = pygame.mixer.Sound("sound/king die.wav")
        self.king_die_song.set_volume(0.1)
        self.boss_die_song = pygame.mixer.Sound("sound/boss die.wav")
        self.boss_die_song.set_volume(0.1)

    def update(self, elapsed):
        self.temp += elapsed
        if self.temp > 0.3:
            self.kill()

    def collide(self, other):
        if isinstance(other, Enemy) or isinstance(other, Boss) or isinstance(other, King):
            if type(other) in self.enemy_list:
                if not other.lost_life:
                    if other.life == 1:
                        other.life -= 1
                        print("should kill")
                        self.parent.add(Explosion(other.position, ps.Color(1.0, 0.0, 0.0, 0.2)))
                        other.kill()
                        if isinstance(other, King):
                                self.king_die_song.play()
                        elif isinstance(other, Boss):
                            self.boss_die_song.play()
                        else:
                            self.monster_die_song3.play()
                    else:
                        other.do(Blink(3, 0.5))
                        other.life -= 1
                        other.lost_life = True
                        if isinstance(other, King):
                            self.king_hit_song.play()
                        elif isinstance(other, Boss):
                            self.monster_die_song2.play()
                        else:
                            self.monster_die_song2.play()

            else: 
                self.parent.add(Explosion(other.position,  ps.Color(1.0, 0.0, 0.0, 0.2)))
                self.monster_die_song1.play()
                other.kill()

        if isinstance(other, EnemyFireBall):
            other.kill()


    def on_exit(self):
        super(SpellEffect, self).on_exit()
        SpellEffect.INSTANCE = None

class BossSpellEffect(Actor):
    seq1 = ImageGrid(load('img/BossMagic/fireball.png'), 10, 4)
    seq2 = ImageGrid(load('img/BossMagic/flash_freeze.png'), 12, 8)
    seq3 = ImageGrid(load('img/BossMagic/skull_smoke_green.png'), 2, 19)
    seq4 = ImageGrid(load('img/BossMagic/explosion_fire.png'), 5, 6)
    seq5 = ImageGrid(load('img/BossMagic/explosion_magic.png'), 5, 6)

    ANIM1 = Animation.from_image_sequence(seq1, duration = 0.01, loop = False)
    ANIM2 = Animation.from_image_sequence(seq2, duration = 0.01, loop = False)
    ANIM3 = Animation.from_image_sequence(seq3, duration = 0.07)
    ANIM4 = Animation.from_image_sequence(seq4, duration = 0.05, loop = False)
    ANIM5 = Animation.from_image_sequence(seq5, duration = 0.05, loop = False)

    TYPE = {1 : ANIM1, 2 : ANIM2, 3 : ANIM3, 4:ANIM4, 5:ANIM5}

    INSTANCE = None

    def __init__(self, image, x, y):
        super(BossSpellEffect, self).__init__(image, x, y)
        self.temp = 0
        self.type = 0 #type : 1=fireball, 2=안개.., 3=회색 뭉텅이
        BossSpellEffect.INSTANCE = self
        self.cshape = cm.AARectShape(self.position, self.width * 0.1, self.height * 0.1)
        self.target = None
        self.velocity = eu.Vector2(0, 0)
        self.temp_bool = False

        self.speed = 0.2
        self.max_force = 5
        self.max_velocity = 200

        self.set_velocity()


    def update(self, elapsed):
        if self.type == 1:
            if self.target is not None:
                self.velocity = eu.Vector2(self.target.position[0] - self.position[0], self.target.position[1] - self.position[1])
            self.move(self.truncate(self.velocity, 3))

        elif self.type == 2:
            self.temp += elapsed
            self.scale = 1.2
            self.cshape = cm.AARectShape(self.position, self.width * 0.35, self.height * 0.35)
            if self.temp > 1.2:
                self.kill()
                self.scale = 1
                self.cshape = cm.AARectShape(self.position, self.width * 0.1, self.height * 0.1)
                self.temp = 0
            
        elif self.type == 3:
            self.temp += elapsed
            if not self.temp_bool:
                self.position = self.rand_pos()
                self.cshape.center = self.position
                self.temp_bool = True
            if self.temp >= 1.5:
                if self.target is not None: 
                    self.pursuit(self.target, elapsed)
                    self.position += self.velocity * elapsed
                self.cshape.center = self.position
            if self.temp >= 7:
                self.kill()
                self.temp = 0

        elif self.type == 4 or self.type == 5:
            self.scale = 1.5
            self.temp += elapsed
            if self.temp >= 1:
                self.kill()
                self.temp = 0
                self.scale = 1
                

        
    def set_velocity(self):
        if self.target is not None:
            if self.target.position[0] <= self.position[0]:
                self.velocity = eu.Vector2(-5, 0)
            else:
                self.velocity = eu.Vector2(5, 0)

    def rand_pos(self):
        pos_x = random.randint(400, 900)
        pos_y = random.randint(200, 400)
        return (pos_x, pos_y)
        
    def truncate(self, vector, m): # limits vector
        magnitude = abs(vector)
        if magnitude > m:
            vector *= m / magnitude
        return vector

    def pursuit(self, target, dt):
        pos = target.position
        if target.go_right == True:
            target_velocity = eu.Vector2(10, 0)
        else:
            target_velocity = eu.Vector2(-10, 0)

        future_pos = pos + target_velocity * dt
        distance = future_pos - eu.Vector2(self.x, self.y)
        steering = distance * self.speed - self.velocity
        steering = self.truncate(steering, self.max_force)
        self.velocity = self.truncate(self.velocity + steering, self.max_velocity)



    def collide(self, other):
        if self.type == 1 or self.type == 3:
            if isinstance(other, Player):
                if other.slide:
                    self.kill()
                else:
                    self.kill()
            self.temp = 0

        if isinstance(other, Player):
            print('Ooch')

    def on_exit(self):
        super(BossSpellEffect, self).on_exit()
        BossSpellEffect.INSTANCE = None

class EnemyFireBall(Actor):
    seq1 = ImageGrid(load('img/BossMagic/fireball.png'), 10, 4)
    seq2 = ImageGrid(load('img/Enemy/fireball.png'), 1, 3)
    seq3 = ImageGrid(load('img/Enemy/fireball2.png'), 1, 6)

    ANIM1 = Animation.from_image_sequence(seq1, duration = 0.01, loop = False)
    ANIM2 = Animation.from_image_sequence(seq2, duration = 0.01, loop = False)
    ANIM3 = Animation.from_image_sequence(seq3, duration = 0.01, loop = False)
    ANIM3.get_transform(True, False, 0)
    ANIM3.scale = 1.5
    
    INSTANCE = None

    def __init__(self, image, x, y):
        super(EnemyFireBall, self).__init__(image, x, y)
        EnemyFireBall.INSTANCE = self
        self.cshape = cm.AARectShape(self.position, self.width * 0.1, self.height * 0.1)
        
        self.temp = 0
        self.speed = 3
        self.velocity = eu.Vector2(-50, 0)
        self.max_force = 3
        self.max_velocity = 200
        self.type = 0 # 0 - seek player, 1 - horizontal

        self.target = None

    def update(self, elapsed):

        if self.type == 0:
            if self.target is not None:
                self.pursuit(self.target, elapsed)
            self.position += self.velocity * elapsed

            self.cshape.center = self.position
        elif self.type == 1:
            self.move(eu.Vector2(-10, 0))

        

    def truncate(self, vector, m): # limits vector
        magnitude = abs(vector)
        if magnitude > m:
            vector *= m / magnitude
        return vector

    def pursuit(self, target, dt):
        pos = target.position
        if target.go_right == True:
            target_velocity = eu.Vector2(10, 0)
        else:
            target_velocity = eu.Vector2(-10, 0)
        future_pos = pos + target_velocity * dt
        distance = future_pos - eu.Vector2(self.x, self.y)
        steering = distance * self.speed - self.velocity
        steering = self.truncate(steering, self.max_force)
        self.velocity = self.truncate(self.velocity + steering, self.max_velocity)



    def collide(self, other):
        if isinstance(other, Player):
            print('Ooch')
            self.kill()

    def on_exit(self):
        super(EnemyFireBall, self).on_exit()
        EnemyFireBall.INSTANCE = None

class Explosion(ps.ParticleSystem):
    total_particles = 300
    duration = 0.1
    gravity = eu.Point2(0, 0)
    angle = 90.0; angle_var = 360.0
    speed = 60.0; speed_var = 20.0
    life = 0.5; life_var = 0.2

    emission_rate = total_particles / duration
    start_color_var = ps.Color(1.0, 0.0, 0.0, 0.2)
    end_color = ps.Color(0.0, 0.0, 0.0, 1.0)
    end_color_var = ps.Color(0.0, 0.0, 0.0, 0.0)
    size = 15
    size_var = 10.0
    blend_additive = True

    

    def __init__(self, pos, color):
        super(Explosion, self).__init__()
        self.position = pos
        self.start_color = color
        
class Chat(Actor):
    seq1 = ImageGrid(load('img/NPC/chat_z.png'), 1, 7)
    seq2 = ImageGrid(load('img/NPC/chat_x.png'), 1, 7)
    seq3 = ImageGrid(load('img/NPC/chat_space.png'), 1, 7)
    seq4 = ImageGrid(load('img/NPC/chat_shift.png'), 1, 7)
    image1 = load('img/story.png')

    ANIM1 = Animation.from_image_sequence(seq1, duration = 0.1, loop = False)
    ANIM2 = Animation.from_image_sequence(seq2, duration = 0.1, loop = False)
    ANIM3 = Animation.from_image_sequence(seq3, duration = 0.1, loop = False)
    ANIM4 = Animation.from_image_sequence(seq4, duration = 0.1, loop = False)

    TYPE = {1 : ANIM1, 2 : ANIM2, 3 : ANIM3, 4 : ANIM4, 5 : image1}


    chat_base = load('img/NPC/chat_base.png')

    def __init__(self, image, x, y):
        super(Chat, self).__init__(image, x, y)
        self.scale = 2

    def update(self, elapsed):

        pass

    def on_exit(self):
        super(Chat, self).on_exit()
        
class Portal(Actor):
    def __init__(self, image, x, y):
        super(Portal, self).__init__(image, x, y)
        self.scale = 5

class Wing(Actor):
    seq1 = ImageGrid(load('img/Player/wings.png'), 8, 6)

    ANIM1 = Animation.from_image_sequence(seq1, duration = 0.1, loop = False)

    def __init__(self, image, x, y):
        super(Wing, self).__init__(image, x, y)
        self.scale = 1
        self.image = Wing.ANIM1

#BackGroundLayer
class BackgroundLayer_main(cocos.layer.Layer):
    def __init__(self):
        super().__init__()

        self.px_width = 650
        self.px_height = 488

        bg = cocos.sprite.Sprite('img/Background_main.png')
        bg.position = self.px_width/2, self.px_height/2

        self.add(bg)

class BackgroundLayer_clear(cocos.layer.Layer):
    def __init__(self):
        super().__init__()

        self.px_width = 650
        self.px_height = 488

        bg = cocos.sprite.Sprite('img/clear.png')
        bg.position = self.px_width/2, self.px_height/2

        self.add(bg)

class BackgroundLayer1(cocos.layer.ScrollableLayer):
    def __init__(self):
        super().__init__()

        self.px_width = 1920
        self.px_height = 1080

        bg = cocos.sprite.Sprite('img/Background1.png')
        bg.position = self.px_width/2, self.px_height/5

        self.add(bg)

class BackgroundLayer2(cocos.layer.ScrollableLayer):
    def __init__(self):
        super().__init__()

        self.px_width = 3840
        self.px_height = 600

        bg = cocos.sprite.Sprite('img/stage2_background.png')
        bg.position = self.px_width/2, self.px_height/2

        self.add(bg)

class BackgroundLayer3(cocos.layer.ScrollableLayer):
    def __init__(self):
        super().__init__()

        self.px_width = 1920
        self.px_height = 600

        bg = cocos.sprite.Sprite('img/church_background.png')
        bg.position = self.px_width/2, self.px_height/2

        self.add(bg)
        
#GameLayer

class GameLayer(cocos.layer.ScrollableLayer):
    is_event_handler = True

    def on_key_press(self, k, _):
        Player.KEYS_PRESSED[k] = 1
        

    def on_key_release(self, k, _):
        Player.KEYS_PRESSED[k] = 0

    def load_animation(self, image, row, dur, loop=True):
        seq = ImageGrid(load(image), 1, row)
        return Animation.from_image_sequence(seq, dur, loop)

    def __init__(self):
        super(GameLayer, self).__init__()
        #w, h = cocos.director.director.get_window_size()
        w = 1920
        h = 600
        self.width = w
        self.height = h
        self.bgm = False
        self.enemy_list = []

        self.animation()
        self.sound()
        self.create_platform()
        self.create_player()
        self.create_heart()
        
        self.pressed = defaultdict(int)

        cell = self.player.width * 1.25
        self.collman = cm.CollisionManagerGrid(0, w, 0, h, cell, cell)

        self.schedule(self.update)
        

    def animation(self):
        self.idle_image = self.load_animation('img/Player/RedhoodIdle.png', 18, 0.1)
        self.idle_image_left = self.idle_image.get_transform(True, False, 0)
        self.jump_image =  self.load_animation('img/Player/RedhoodJump.png', 19, 0.02, False)
        self.jump_image_left = self.jump_image.get_transform(True, False, 0)
        self.run_image = self.load_animation('img/Player/RedhoodRun.png', 24, 0.02)
        self.run_image_left = self.run_image.get_transform(True, False, 0)
        self.attack1_image = self.load_animation('img/Player/Attack.png', 7, 0.09, False)
        self.attack1_image_left = self.attack1_image.get_transform(True, False, 0)
        self.attack2_image = self.load_animation('img/Player/Attack2.png', 7, 0.09, False)
        self.attack2_image_left = self.attack2_image.get_transform(True, False, 0)
        self.attack3_image = self.load_animation('img/Player/Attack3.png', 12, 0.09, False)
        self.attack3_image_left = self.attack3_image.get_transform(True, False, 0)
        self.slide_image_left = self.load_animation('img/Player/slide.png', 4, 0.03)
        self.slide_image_right = self.slide_image_left.get_transform(True, False, 0)
        self.gameover_image_left = self.load_animation('img/Player/gameover.png', 6, 0.2, False)
        self.gameover_image_right = self.gameover_image_left.get_transform(True, False, 0)

        
        self.portal_image = self.load_animation('img/GreenPortal.png', 8, 0.1).get_transform(True, False, 0)

        self.enemy_idle = self.load_animation('img/Enemy/CrabIdle.png', 6, 0.05)
        self.bat_idle = self.load_animation('img/Enemy/Bat_Fly.png', 4, 0.05)
        self.slime_idle = self.load_animation('img/Enemy/Slime_Idle.png', 4, 0.05)
        self.ghoul_run = self.load_animation('img/Enemy/burning-ghoul.png', 8, 0.05)
        self.wizard_idle = self.load_animation('img/Enemy/wizard_idle.png', 6, 0.1)
        self.wizard_attack = self.load_animation('img/Enemy/wizard_attack.png', 9, 0.1)
        self.fireworm_idle = self.load_animation('img/Enemy/fireworm_idle.png', 9, 0.1).get_transform(True, False, 0)
        self.fireworm_attack = self.load_animation('img/Enemy/fireworm_attack.png', 16, 0.1).get_transform(True, False, 0)

        self.fox_idle = self.load_animation('img/NPC/Fox_idle.png', 5, 0.1)
        self.fox_run = self.load_animation('img/NPC/Fox_run.png', 8, 0.1)
        self.fox_sleep = self.load_animation('img/NPC/Fox_sleep.png', 6, 0.1)

        self.npc1_idle = self.load_animation('img/NPC/barkeep.png', 5, 0.3)
        self.npc2_idle = self.load_animation('img/NPC/merchant.png', 5, 0.3)
        self.npc3_idle = self.load_animation('img/NPC/villager_01.png', 5, 0.3)
        self.npc4_idle = self.load_animation('img/NPC/villager_02.png', 5, 0.3)

        self.boss_idle = self.load_animation('img/Boss/Idle.png', 8, 0.1)
        self.boss_run = self.load_animation('img/Boss/Move.png', 8, 0.1)
        self.boss_attack = self.load_animation('img/Boss/Attack.png', 8, 0.1)

        self.king_idle = self.load_animation('img/Boss/king_idle.png', 8, 0.1)
        self.king_idle_left = self.king_idle.get_transform(True, False, 0)
        self.king_run = self.load_animation('img/Boss/king_run.png', 8, 0.1)
        self.king_run_left = self.king_run.get_transform(True, False, 0)
        self.king_attack1 = self.load_animation('img/Boss/king_attack1.png', 4, 0.25)
        self.king_attack1_left = self.king_attack1.get_transform(True, False, 0)
        self.king_attack2 = self.load_animation('img/Boss/king_attack2.png', 4, 0.25)
        self.king_attack2_left = self.king_attack2.get_transform(True, False, 0)
        self.king_attack3 = self.load_animation('img/Boss/king_attack3.png', 4, 0.25)
        self.king_attack3_left = self.king_attack3.get_transform(True, False, 0)
        self.king_takehit = self.load_animation('img/Boss/king_takehit.png', 4, 0.15)
        self.king_takehit_left = self.king_takehit.get_transform(True, False, 0)
        self.king_death = self.load_animation('img/Boss/king_death.png', 6, 0.1)
        self.king_death_left = self.king_death.get_transform(True, False, 0)



    def sound(self):
        self.bgm_song = pygame.mixer.Sound("sound/stage1.mp3")
        self.bgm_song.set_volume(0.05)
        
        self.king_slash_song = pygame.mixer.Sound("sound/king_slash.wav")
        self.king_slash_song.set_volume(0.3)
        

    def create_player(self):
        self.player = Player(self.idle_image, 50, 300)
        self.add(self.player)

    def create_heart(self):
        pos = self.player.get_position()
        self.heart = Heart(Heart.heart[7-self.player.lives], pos[0] + 25, pos[1] + 150)
        self.add(self.heart)


    def create_platform(self):
        for i in range(20):
            self.platform = Platform(128 * i, 20)
            self.platform.image = Platform.img5
            self.platform.image_anchor = (Platform.img5.width / 2, Platform.img5.height / 3)
            self.add(self.platform)


    def create_obstacle(self):
        self.obstacle1 = Spike(800, 80)
        self.add(self.obstacle1)
        self.obstacle2 = Spike(1000, 80)
        self.add(self.obstacle2)


    def create_enemy(self):
        self.enemy = Enemy(self.enemy_idle, 650, 300)
        self.enemy_list.append(self.enemy)
        self.add(self.enemy)

    def create_npc(self):
        self.fox = NPC(self.fox_sleep, 1300, 300)
        self.fox.chat_type = 5

        self.add(self.fox)

        self.npc1 = NPC1(self.npc1_idle, 300, 300)
        self.npc1.type = 1
        self.npc2 = NPC1(self.npc2_idle, 500, 300)
        self.npc2.type = 2
        self.npc3 = NPC1(self.npc3_idle, 700, 300)
        self.npc3.type = 3
        self.npc4 = NPC1(self.npc4_idle, 900, 300)
        self.npc4.type = 4

        self.npc_list = [self.npc1, self.npc2,self.npc3, self.npc4]

        self.add(self.npc1)
        self.add(self.npc2)
        self.add(self.npc3)
        self.add(self.npc4)

    
    def change_player_state(self):
        if self.player.state_list[3][0] != self.player.state_list[3][1]: #attack
            if self.player.state_list[3][1] == True:
                if self.player.combo_count == 0:
                    if self.player.state_list[1][1] == True:
                        self.player.change_img(self.attack1_image)
                    else:
                        self.player.change_img(self.attack1_image_left)
            else:
                if self.player.state_list[1][1] == True:
                    self.player.change_img(self.idle_image)
                else:
                    self.player.change_img(self.idle_image_left)
        


        if self.player.state_list[3][1] == True:
            if self.player.combo_count == 1:
                if self.player.state_list[1][1] == True:
                    self.player.change_img(self.attack2_image)
                else:
                    self.player.change_img(self.attack2_image_left)
            elif self.player.combo_count == 2:
                if self.player.state_list[1][1] == True:
                    self.player.change_img(self.attack3_image)
                else:
                    self.player.change_img(self.attack3_image_left)

        if self.player.state_list[4][0] != self.player.state_list[4][1]: #slide
            if self.player.state_list[4][1] == True:
                if self.player.state_list[1][1] == True:
                    self.player.change_img(self.slide_image_right)
                else:
                    self.player.change_img(self.slide_image_left)
            else:
                if self.player.state_list[1][1] == True:
                    self.player.change_img(self.run_image)
                else:
                    self.player.change_img(self.run_image_left)
            
        if self.player.state_list[2][0] != self.player.state_list[2][1]: #idle or run
            if self.player.state_list[2][1] == 1: #run
                if self.player.state_list[1][1] == True:
                    self.player.change_img(self.run_image)
                else:
                    self.player.change_img(self.run_image_left)
            else:
                if self.player.state_list[1][1] == True:
                    self.player.change_img(self.idle_image)
                else:
                    self.player.change_img(self.idle_image_left)

        if self.player.state_list[0][0] != self.player.state_list[0][1]: #jump or not
            self.player.state = 0
            self.player.update_state(self.player.state, 2)
            if self.player.state_list[0][1] == False:
                if self.player.state_list[1][1] == True:
                    self.player.change_img(self.jump_image)
                else:
                    self.player.change_img(self.jump_image_left)

    def change_fox_state(self):
        if self.fox.state_list[0][0] != self.fox.state_list[0][1]:
            if self.fox.state_list[0][1]:
                self.fox.change_img(self.fox_idle)
            else:
                self.fox.change_img(self.fox_sleep)
        
        if abs(self.fox.x - self.player.x) <= 100 : self.fox.state = True
        else : self.fox.state = False

    def change_npc_state(self):
        for i in self.npc_list:
            if abs(i.x - self.player.x) <= 100 : i.state = True
            else : i.state = False

    def change_wizard_state(self):
        if self.wizard.state[0] != self.wizard.state[1]:
            if self.wizard.state[1]:
                self.wizard.image = self.wizard_attack
            else:
                self.wizard.image = self.wizard_idle

    def change_fireworm_state(self):
        if self.fireworm.state[0] != self.fireworm.state[1]:
            if self.fireworm.state[1]:
                self.fireworm.image = self.fireworm_attack
            else:
                self.fireworm.image = self.fireworm_idle

    def change_boss_state(self):
        if abs(self.boss.x - self.player.x) <= 300:
            self.boss.is_player_around = True
        else:
            self.boss.is_player_around= False

        if self.boss.state_list[0][0] != self.boss.state_list[0][1]:
            if self.boss.state_list[0][1]:
                self.boss.change_img(self.boss_attack)
            else:
                self.boss.change_img(self.boss_idle)

    def change_king_state(self):
        if abs(self.king.x - self.player.x) <= 200:
            self.king.is_player_around = True
        else:
            self.king.is_player_around= False


        if self.king.state_list[1][0] != self.king.state_list[1][1]:
            if self.king.state_list[0][1]:
                if self.king.state_list[1][1] == 1:
                    self.king_slash_song.play()
                    self.king.change_img(self.king_attack1_left)
                elif self.king.state_list[1][1] == 2:
                    self.king_slash_song.play()
                    self.king.change_img(self.king_attack2_left)
                elif self.king.state_list[1][1] == 3:
                    self.king_slash_song.play()
                    self.king.change_img(self.king_attack3_left)
                else:
                    self.king.change_img(self.king_idle_left)
            else:
                if self.king.state_list[1][1] == 1:
                    self.king_slash_song.play()
                    self.king.change_img(self.king_attack1)
                elif self.king.state_list[1][1] == 2:
                    self.king_slash_song.play()
                    self.king.change_img(self.king_attack2)
                elif self.king.state_list[1][1] == 3:
                    self.king_slash_song.play()
                    self.king.change_img(self.king_attack3)
                else:
                    self.king.change_img(self.king_idle)

        if self.king.state_list[1][1] == 0:
            if self.king.state_list[2][0] != self.king.state_list[2][1]:
                if self.king.state_list[0][1]:
                    self.king.change_img(self.king_run_left)
                else:
                    self.king.change_img(self.king_run)


            if self.king.state_list[2][1]:
                if self.king.state_list[0][0] != self.king.state_list[0][1]:
                    if self.king.state_list[0][1]:
                        self.king.change_img(self.king_run_left)
                    else:
                        self.king.change_img(self.king_run)

                
        if not self.king.state_list[2][1]:
            if self.king.state_list[0][0] != self.king.state_list[0][1]:
                if self.king.state_list[0][1]:
                    self.king.change_img(self.king_idle_left)
                else:
                    self.king.change_img(self.king_idle)

        if self.king.state_list[3][0] != self.king.state_list[3][1]:
            if self.king.state_list[3][1]:
                if self.king.state_list[0][1]:
                    self.king.change_img(self.king_takehit_left)
                else:
                    self.king.change_img(self.king_takehit)

        if self.king.spawn:
            self.create_priest()
            self.king.spawn = False


    def update(self, dt):

        if not self.bgm:
            self.bgm_song.play(-1)
            self.bgm = True

        self.collman.clear()
        

        for _, node in self.children:
            if type(node) != Explosion:
                self.collman.add(node)
                if not self.collman.knows(node):
                    self.remove(node)

        self.heart.set_position(self.player)

        self.collide(SwordEffect.INSTANCE)
        self.collide(SpellEffect.INSTANCE)
        self.collide(BossSpellEffect.INSTANCE)
        self.collide(EnemyFireBall.INSTANCE)

        self.change_player_state()
        
        #collman update
        for _, node in self.children:
            if type(node) != Explosion:
                self.collman.add(node)
                node.update(dt)

        if self.collide(self.player):
            pass
        

    def collide_platform(self, node, obj):  #platform에 닿을 때 처리
        check_type = [Enemy, Boss, NPC, NPC1, Enemy_slime, Enemy_ghoul, King]
        if node is not None:
            for other in list(self.collman.iter_colliding(node)):
                if isinstance(obj, Player):
                    pos = obj.get_position()
                    if isinstance(other, Platform):
                        obj.is_ground = True
                        obj.update_state(self.player.is_ground, 0)
                        obj.is_jumped = False

                elif type(obj) in check_type:
                    obj.is_ground = True

    def collide_portal(self, node, layer):
        if node is not None:
            for other in list(self.collman.iter_colliding(node)): 
                if isinstance(node, Player):
                    if isinstance(other, Portal):
                        self.bgm_song.stop()
                        scene = cocos.scene.Scene()
                        scene.add(layer)
                        cocos.director.director.replace(FadeTransition(scene))

    def collide(self, node):
        obstacle_type = [Spike, Enemy, Enemy_bat, BossSpellEffect, Enemy_slime, Enemy_ghoul, EnemyFireBall, King]

        pos = self.player.get_position()

        self.collide_platform(node, self.player)

                
        if node is not None:
            for other in list(self.collman.iter_colliding(node)):  
                if isinstance(node, Player):
                    if type(other) in obstacle_type:
                        pos = self.player.get_position()
                        if not self.player.slide and not self.player.isHit:
                            self.player.isHit = True
                            self.player.position = pos[0]-70, pos[1]
                            self.player.do(Blink(3, 0.5))
                            if self.player.lives > 1:
                                self.player.lives -= 1
                                self.heart.change_img(Heart.heart[7-self.player.lives])
                            else: 
                                print('Dead')
                                self.unschedule(self.update)
                                if self.player.state_list[1][1] == True:
                                    self.player.change_img(self.gameover_image_right)
                                else:
                                    self.player.change_img(self.gameover_image_left)
                                self.player.do(FadeOut(3))
                    elif isinstance(other, Trap):
                        if other.is_able:
                            pos = self.player.get_position()
                            if not self.player.slide and not self.player.isHit:
                                self.player.isHit = True
                                self.player.position = pos[0]-70, pos[1]
                                self.player.do(Blink(3, 0.5))
                                if self.player.lives > 1:
                                    self.player.lives -= 1
                                    self.heart.change_img(Heart.heart[7-self.player.lives])
                                else: 
                                    print('Dead')
                                    self.unschedule(self.update)
                                    if self.player.state_list[1][1] == True:
                                        self.player.change_img(self.gameover_image_right)
                                    else:
                                        self.player.change_img(self.gameover_image_left)
                                    self.player.do(FadeOut(3))


        if node is not None:
            for other in list(self.collman.iter_colliding(node)):
                node.collide(other)

class GameLayer1(GameLayer):
    def __init__(self):
        super().__init__()
        self.create_enemy()
        #self.create_bat()
        #self.create_slime()
        #self.create_ghoul()
        #self.create_wizard()
        #self.create_fireworm()
        #self.create_boss()
        #self.create_king()
        self.create_npc()
        self.create_obstacle()
        self.create_portal()

    def create_portal(self):
        self.portal = Portal(self.portal_image, 1850, 80)
        self.add(self.portal)

    def create_platform(self):
        for i in range(20):
            self.platform = Platform(128 * i, 20)
            self.platform.image = Platform.img1
            self.platform.image_anchor = (Platform.img1.width / 2, Platform.img1.height / 2)
            self.add(self.platform)

    def update(self, elapsed):
        super().update(elapsed)
        self.change_npc_state()
        self.change_fox_state()
        #self.change_wizard_state()
        #self.change_fireworm_state()
        #self.change_boss_state()
        #self.change_king_state()

       

    def collide(self, node):
        super().collide(node)
        for i in self.enemy_list: self.collide_platform(node, i)
        #for i in self.slime_list:
        #    self.collide_platform(node, i)
        #self.collide_platform(node, self.ghoul)
        #self.collide_platform(node, self.boss)
        #self.collide_platform(node, self.king)
        self.collide_platform(node, self.fox)
        self.collide_platform(node, self.npc1)
        self.collide_platform(node, self.npc2)
        self.collide_platform(node, self.npc3)
        self.collide_platform(node, self.npc4)
        self.collide_portal(node, scroller2)
        
class GameLayer2(GameLayer):
    def __init__(self):
        super(GameLayer2, self).__init__()
        #w, h = cocos.director.director.get_window_size()
        w = 3840
        h = 600
        self.width = w
        self.height = h
        self.bgm = False

        self.bat_temp = True
        self.ghoul_temp = True

        self.create_enemy()
        self.create_slime()
        self.create_fireworm()
        self.create_wizard()
        self.create_portal()

        self.enemy_temp1 = 0
        self.enemy_temp2 = 0

    def create_portal(self):
        self.portal = Portal(self.portal_image, 2000, 80)
        self.add(self.portal)

    def create_platform(self):
        for i in range(30):
            self.platform = Platform(128 * i, 20)
            self.platform.image = Platform.img3
            self.platform.image_anchor = (Platform.img3.width / 2, Platform.img3.height / 3)
            self.add(self.platform)

        for i in range(3):
            self.platform = Platform(700 + 200 * 1, 200)
            self.platform.image = Platform.img3
            self.platform.image_anchor = (Platform.img3.width / 2, Platform.img3.height / 3)
            self.add(self.platform)
    
    def create_enemy(self):
        for i in range(7):
            self.enemy = Enemy(self.enemy_idle, 200 + 200 * i, 300)
            self.enemy_list.append(self.enemy)
            self.add(self.enemy)

    def create_slime(self):
        for i in range(4):
            self.slime = Enemy_slime(self.slime_idle, 200 * (3 * i), 300 - 10 * i)
            self.enemy_list.append(self.slime)
            self.add(self.slime)

    def create_bat(self, x):
        self.bat = Enemy_bat(self.bat_idle, 200 * x, 500 - (30 * random.randint(1, 6)))
        self.bat.target = self.player
        self.enemy_list.append(self.bat)
        self.add(self.bat)

    def create_ghoul(self):
        self.ghoul = Enemy_ghoul(self.ghoul_run, 1800, 120)
        self.enemy_list.append(self.ghoul)
        self.add(self.ghoul)
        self.ghoul.target = self.player

    def create_wizard(self):
        for i in range(3):
            self.wizard = Enemy_wizard(self.wizard_idle, 700 + 200 * i, 300)
            self.wizard.target = self.player
            self.enemy_list.append(self.wizard)
            self.add(self.wizard)
        
    def create_fireworm(self):
        self.fireworm = Enemy_fireworm(self.fireworm_idle, 1900, 80)
        self.enemy_list.append(self.fireworm)
        self.add(self.fireworm)

    def sound(self):
        super().sound()
        self.bgm_song = pygame.mixer.Sound("sound/stage2.mp3")
        self.bgm_song.set_volume(0.05)
        
    def update(self, elapsed):
        super().update(elapsed)

        self.change_wizard_state()
        self.change_fireworm_state()

        self.enemy_temp1 += elapsed
        self.enemy_temp2 += elapsed
        
        if self.bat_temp:
            if self.enemy_temp1 >= 1 and self.enemy_temp1 <= 1.2:
                self.create_bat(random.randint(1, 5))
                self.bat_temp = False
        if self.enemy_temp1 > 3:
            self.bat_temp = True
            self.enemy_temp1 = 0

        if self.ghoul_temp:
            if self.enemy_temp2 >= 2 and self.enemy_temp2 <= 2.2:
                self.create_ghoul()
                self.ghoul_temp = False
        if self.enemy_temp2 > 3:
            self.ghoul_temp = True
            self.enemy_temp2 = 0


    def collide(self, node):
        super().collide(node)
        for i in self.enemy_list: self.collide_platform(node, i)
        self.collide_portal(node, scroller3)

class GameLayer3(GameLayer):
    def __init__(self):
        super(GameLayer3, self).__init__()
        #w, h = cocos.director.director.get_window_size()
        w = 1920
        h = 600
        self.width = w
        self.height = h
        self.bgm = False

        self.is_not_boss = True
        self.is_not_king = True

        self.is_wing = False

        self.boss = None
        self.king = None
    
    def create_priest(self):
        self.priest1 = Priest(Priest.ANIM1, 1200, 80)
        self.priest2 = Priest(Priest.ANIM3, 1700, 80)

        self.priest1.target = self.player
        self.priest2.target = self.player

        self.enemy_list.append(self.priest1)
        self.enemy_list.append(self.priest2)

        self.add(self.priest1)
        self.add(self.priest2)

    def create_boss(self):
        self.boss = Boss(self.boss_idle, 700, 300)
        self.boss.target = self.player
        self.enemy_list.append(self.boss)
        self.add(self.boss)

    def create_king(self):
        self.king = King(self.king_idle, 1450, 100)
        self.king.target = self.player
        self.enemy_list.append(self.king)
        self.add(self.king)

    def create_wing(self):
        self.wing = Wing(Wing.ANIM1, self.player.position[0], self.player.position[1] + 30)
        self.add(self.wing)
        
    def sound(self):
        super().sound()
        self.bgm_song = pygame.mixer.Sound("sound/stage3.mp3")
        self.bgm_song.set_volume(0.05)

    def create_platform(self):
        for i in range(20):
            self.platform = Platform(128 * i, 0)
            self.platform.image = Platform.img5
            self.platform.image_anchor = (Platform.img5.width / 2, Platform.img5.height / 3)
            self.add(self.platform)

    def update(self, elapsed):
        super().update(elapsed)
        pos = self.player.position


        if pos[0] >= 450:
            if self.is_not_boss:
                self.create_boss()
                self.is_not_boss = False
                self.player.in_bossroom = True

        if self.boss is not None: 
            self.change_boss_state()
            print(self.boss.life)
            if self.boss.life == 0:
                self.player.in_bossroom = False

        if pos[0] >= 1100:
            if self.is_not_king:
                self.create_king()
                self.is_not_king = False
                self.player.in_kingroom = True

        if self.player.in_kingroom or self.player.in_bossroom:
            if self.player.in_bossroom:
                scroller3.set_focus(700, 200)
            elif self.player.in_kingroom:
                scroller3.set_focus(1450, 200)
        else:
            scroller3.set_focus(self.player.position[0], self.player.position[1])

        if self.king is not None: 
            self.change_king_state()
            print(self.king.life)
            if self.king.life == 0:
                self.player.in_kingroom = False
                if not self.is_wing:
                    self.create_wing()
                    self.is_wing = True
                    self.player.do(Delay(5))
                    self.unschedule(self.update)
                    cocos.director.director.replace(FadeTransition(scene_clear, 12))


    def collide(self, node):
        super().collide(node)
        for i in self.enemy_list: self.collide_platform(node, i)

        
class MainMenu(Menu):
    def __init__(self):
        super(MainMenu, self).__init__('')
        """self.font_title['font_name'] = 'Times New Roman'
        self.font_title['font_size'] = 60
        self.font_title['bold'] = True"""
        self.font_item['font_name'] = 'Alex Brush'
        self.font_item['font_size'] = 30
        self.font_item_selected['font_name'] = 'Alex Brush'


        items = list()
        items.append(MenuItem('New Game', self.start_game))        
        items.append(MenuItem('Quit', exit))
        self.create_menu(items, shake(), shake_back())

    def start_game(self):
        scene = cocos.scene.Scene()
        scene.add(scroller1)
        cocos.director.director.push(scene)



if __name__ == '__main__':
    cocos.director.director.init(caption='Red Hood')
    mixer.init()
    pygame.init()

    scroller1 = cocos.layer.ScrollingManager()
    bg_layer1 = BackgroundLayer1()
    game_layer1 = GameLayer1()

    scroller2 = cocos.layer.ScrollingManager()
    bg_layer2 = BackgroundLayer2()
    game_layer2 = GameLayer2()

    scroller3 = cocos.layer.ScrollingManager()
    bg_layer3 = BackgroundLayer3()
    game_layer3 = GameLayer3()

    bg_layer4 = BackgroundLayer_clear()

    scroller1.add(bg_layer1, z = 1)
    scroller1.add(game_layer1, z = 1)

    scroller2.add(bg_layer2, z = 1)
    scroller2.add(game_layer2, z = 1)

    scroller3.add(bg_layer3, z = 1)
    scroller3.add(game_layer3, z = 1)

    scene_clear = cocos.scene.Scene()
    scene_clear.add(bg_layer4)

    scene = cocos.scene.Scene()
    bg_layer_main = BackgroundLayer_main()
    scene.add(bg_layer_main)
    scene.add(MainMenu())
    cocos.director.director.run(scene)





