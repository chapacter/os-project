import sys

import pygame

from entity.enemy import Enemy
from entity.player import Player
from items.weapon import Weapon
from map import Map
from map.tilemap import Block, Ground
from settings import *
from sprites import Spritesheet


class Game:
    def __init__(self):
        self.sc = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.terrain_spritesheet = Spritesheet('assets/tileset.png')
        self.player_spritesheet = Spritesheet('assets/player.png')
        self.enemy_spritesheet = Spritesheet('assets/enemy.png')
        self.weapon_spritesheet = Spritesheet('assets/sword.png')
        self.bullet_spritesheet = Spritesheet('assets/powerBall.png')

        self.running = True
        self.enemy_collided = False
        self.block_collided = False

    def create_tile_map(self):
        map_width = int(WIN_WIDTH / TILESIZE * 1.3)
        map_height = int(WIN_HEIGHT / TILESIZE)

        map_gen = Map(map_width, map_height)
        level = map_gen.create()

        for i, row in enumerate(level):
            for j, column in enumerate(row):
                Ground(self, j, i)
                if column == 'B':
                    Block(self, j, i)
                if column == 'P':
                    self.player = Player(self, j, i)
                if column == "E":
                    Enemy(self, j, i)
                if column == "W":
                    Weapon(self, j, i)


    def create(self):
        self.all_sprites = pygame.sprite.LayeredUpdates()
        self.blocks = pygame.sprite.LayeredUpdates()
        self.water = pygame.sprite.LayeredUpdates()
        self.enemies = pygame.sprite.LayeredUpdates()
        self.mainPlayer = pygame.sprite.LayeredUpdates()
        self.weapons = pygame.sprite.LayeredUpdates()
        self.bullets = pygame.sprite.LayeredUpdates()
        self.healthbar = pygame.sprite.LayeredUpdates()
        self.characters = pygame.sprite.LayeredUpdates()
        # self.explosion = pygame.sprite.LayeredUpdates()
        # self.tree = pygame.sprite.LayeredUpdates()
        self.create_tile_map()

    def update(self):
        self.all_sprites.update()

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

    def draw(self):
        self.sc.fill(BLACK)
        self.all_sprites.draw(self.sc)
        self.clock.tick(FPS)
        pygame.display.update()

    def camera(self):
        if self.enemy_collided == False and self.block_collided == False:
            pressed = pygame.key.get_pressed()


            if pressed[pygame.K_LEFT] or pressed[pygame.K_a]:
                for i, sprite in enumerate(self.all_sprites):
                    sprite.rect.x += PLAYER_SPEED

            elif pressed[pygame.K_RIGHT] or pressed[pygame.K_d]:
                for i, sprite in enumerate(self.all_sprites):
                    sprite.rect.x -= PLAYER_SPEED

            # if pressed[pygame.K_UP] or pressed[pygame.K_w]:
            #     for i, sprite in enumerate(self.all_sprites):
            #         sprite.rect.y += PLAYER_SPEED
            #
            # elif pressed[pygame.K_DOWN] or pressed[pygame.K_s]:
            #     for i, sprite in enumerate(self.all_sprites):
            #         sprite.rect.y -= PLAYER_SPEED

    def main(self):
        while self.running:
            self.events()
            self.camera()
            self.update()
            self.draw()


game = Game()
game.create()

while game.running:
    game.main()

pygame.quit()
sys.exit()
