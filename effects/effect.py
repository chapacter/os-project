import pygame

from utils.settings import *


class Effect(pygame.sprite.Sprite):
    def __init__(self, game, x, y, effect_name):
        self.game = game
        self._layer = HEALTH_LAYER
        self.groups = game.all_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.effect_cfg = SPRITE_EFFECTS
        self.effect_info = self.effect_cfg["effects"][effect_name]
        self.frames_count = self.effect_info["frames"]
        self.effect_name = effect_name

        # Предварительная загрузка всех кадров
        self.frames = []
        for i in range(self.frames_count):
            frame, _ = game.effects_spritesheet.get_effect(
                effect_name, self.effect_cfg, frame=i
            )
            self.frames.append(frame)

        self.frame_index = 0
        self.image = self.frames[0]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def update(self):
        self.frame_index += 1
        if self.frame_index >= self.frames_count:
            self.kill()
        else:
            self.image = self.frames[self.frame_index]
