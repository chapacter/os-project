import pygame

from utils.settings import TILESIZE


class TileSprite(pygame.sprite.Sprite):
    def __init__(self, game, x, y, layer, groups, width=TILESIZE, height=TILESIZE):
        super().__init__()
        self.game = game
        self._layer = layer
        if hasattr(game, 'all_sprites'):
            sprite_groups = [g for g in groups if hasattr(game, g)]
            actual_groups = [getattr(game, g) for g in sprite_groups if hasattr(game, g)]
            if game.all_sprites not in actual_groups:
                actual_groups.insert(0, game.all_sprites)
            pygame.sprite.Sprite.__init__(self, actual_groups)
        else:
            pygame.sprite.Sprite.__init__(self)

        self.x = x * TILESIZE if width == TILESIZE else x
        self.y = y * TILESIZE if height == TILESIZE else y
        self.width = width
        self.height = height

        self.image = pygame.Surface((self.width, self.height))
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y
