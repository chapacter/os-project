import random

from items.loot import LootItem
from utils.audio import audio_manager


class WeaponLoot(LootItem):
    def __init__(self, game, x, y):
        super().__init__(game, x, y)

        cols = [0, 27, 55]
        col = random.choice(cols)
        self.image = game.weapon_spritesheet.get_image(col, 0, 27, 27)
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

    def on_pickup(self, player):
        player.sword_equipped = True
        audio_manager.play_sound("menu_select")
        self.kill()
