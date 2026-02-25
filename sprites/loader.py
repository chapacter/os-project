import pygame


class Spritesheet:
    def __init__(self, path):
        self.spritesheet = pygame.image.load(path).convert()

    def get_image(self, x, y, width, height):
        sprite = pygame.Surface([width, height])
        sprite.blit(self.spritesheet, (0, 0), (x, y, width, height))
        sprite.set_colorkey((0, 0, 0))
        return sprite
