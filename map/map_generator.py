import random


class Map:
    def __init__(self, map_width, map_height):
        self.MAP_WIDTH = map_width
        self.MAP_HEIGHT = map_height
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

    def objectsSpawn(self, obj, level):
        while self.spawn_count[f'{obj}'] > 0:
            y1 = random.randint(self.digger['padding'], self.MAP_HEIGHT - self.digger['padding'])
            x1 = random.randint(self.digger['padding'], self.MAP_WIDTH - self.digger['padding'])
            if level[y1][x1] == ' ':
                level[y1][x1] = f'{obj}'
                self.spawn_count[f'{obj}'] -= 1

    def move(self):
        roll = random.randint(1, 4)

        if roll == 1 and self.digger['x'] > self.digger['padding']:
            self.digger['x'] -= 1
        if roll == 2 and self.digger['x'] < self.MAP_WIDTH - self.digger['padding'] - 1:
            self.digger['x'] += 1
        if roll == 3 and self.digger['y'] > self.digger['padding']:
            self.digger['y'] -= 1
        if roll == 4 and self.digger['y'] < self.MAP_HEIGHT - self.digger['padding'] - 1:
            self.digger['y'] += 1

    def getLevelRow(self):
        return ['B'] * self.MAP_WIDTH

    def create(self):
        self.level = [self.getLevelRow() for _ in range(self.MAP_HEIGHT)]
        while self.digger['wallCountdown'] >= 0:
            x = self.digger['x']
            y = self.digger['y']

            self.move()

            if self.level[y][x] == 'B':
                self.level[y][x] = ' '
                self.digger['wallCountdown'] -= 1

            if self.digger['wallCountdown'] < 0:
                self.level[int(self.MAP_HEIGHT / 2)][int(self.MAP_WIDTH / 2)] = 'P'

                self.objectsSpawn('E', self.level)
                self.objectsSpawn('W', self.level)

        return self.level
