from items.base import Item
from settings import *


class Weapon(Item):
    def __init__(self, game, x, y):
        super().__init__(game, x, y, GROUND_LAYER, game.all_sprites, game.weapons)

        self.image = game.weapon_spritesheet.get_image(0, 0, self.width, self.height)
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

        self.animation_counter = 1

    def animate(self):
        animation = [self.game.weapon_spritesheet.get_image(0, 0, self.width, self.height),
                     self.game.weapon_spritesheet.get_image(27, 0, self.width, self.height),
                     self.game.weapon_spritesheet.get_image(55, 0, self.width, self.height)]
        self.image = animation[int(self.animation_counter)]

        self.animation_counter += 0.02
        if self.animation_counter >= 3:
            self.animation_counter = 0

    def update(self):
        self.animate()
