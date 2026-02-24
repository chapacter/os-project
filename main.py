import sys
from sprites import *


class Map:
    def __init__(self):
        self.MAP_WIDTH = int(WIN_WIDTH / TILESIZE * 1.3) #100
        self.MAP_HEIGHT = int(WIN_HEIGHT / TILESIZE)  # 50
        self.digger = {
            'wallCountdown': int(self.MAP_WIDTH * self.MAP_HEIGHT / 2),
            'padding': 2,
            'x': int(self.MAP_WIDTH / 2),
            'y': int(self.MAP_HEIGHT / 2)
        }
        self.spawn_count = {
            'P': 1,
            'W': 1,
            'E': random.randint(10, 20)
        }

    def objectsSpawn(self, obj):
        while self.spawn_count[f'{obj}'] > 0:
            self.y1 = random.randint(self.digger['padding'], self.MAP_HEIGHT - self.digger['padding'])
            self.x1 = random.randint(self.digger['padding'], self.MAP_WIDTH - self.digger['padding'])
            if self.level[self.y1][self.x1] == ' ':
                self.level[self.y1][self.x1] = f'{obj}'
                self.spawn_count[f'{obj}'] -= 1

    def move(self):
        self.roll = random.randint(1, 4)

        if self.roll == 1 and self.x > self.digger['padding']:
            self.digger['x'] -= 1
        if self.roll == 2 and self.x < self.MAP_WIDTH - self.digger['padding'] - 1:
            self.digger['x'] += 1
        if self.roll == 3 and self.y > self.digger['padding']:
            self.digger['y'] -= 1
        if self.roll == 4 and self.y < self.MAP_HEIGHT - self.digger['padding'] - 1:
            self.digger['y'] += 1

    def getLevelRow(self):
        return ['B'] * self.MAP_WIDTH

    def create(self):
        self.level = [self.getLevelRow() for _ in range(self.MAP_HEIGHT)]
        while self.digger['wallCountdown'] >= 0:
            self.x = self.digger['x']
            self.y = self.digger['y']

            self.move()

            if self.level[self.y][self.x] == 'B':
                self.level[self.y][self.x] = ' '
                self.digger['wallCountdown'] -= 1

            if self.digger['wallCountdown'] < 0:
                self.level[int(self.MAP_HEIGHT / 2)][int(self.MAP_WIDTH / 2)] = 'P'

                self.objectsSpawn('E')
                self.objectsSpawn('W')
        # for row in self.level:
        #     print(''.join(row))


class Spritesheet:
    def __init__(self, path):
        self.spritesheet = pygame.image.load(path).convert()

    def get_image(self, x, y, width, height):
        sprite = pygame.Surface([width, height])
        sprite.blit(self.spritesheet, (0, 0), (x, y, width, height))
        sprite.set_colorkey(BLACK)
        return sprite

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

    def createTileMap(self):
        map = Map()
        map.create()
        for i, row in enumerate(map.level):
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
        self.createTileMap()

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
