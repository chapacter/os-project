import pygame


class Spritesheet:
    def __init__(self, path):
        self.spritesheet = pygame.image.load(path).convert_alpha()

    def get_image(self, x, y, width, height):
        sprite = pygame.Surface([width, height])
        sprite.blit(self.spritesheet, (0, 0), (x, y, width, height))
        sprite.set_colorkey((0, 0, 0))
        return sprite

    def get_image_centered(self, col, row, sprite_cfg):
        sheet_x = col * sprite_cfg["sprite_size"][0]
        sheet_y = row * sprite_cfg["sprite_size"][1]

        sprite = pygame.Surface(sprite_cfg["sprite_size"])
        sprite.blit(
            self.spritesheet, (0, 0), (sheet_x, sheet_y, *sprite_cfg["sprite_size"])
        )
        sprite.set_colorkey((0, 0, 0))

        if sprite_cfg["sprite_size"] != sprite_cfg["target_size"]:
            sprite = pygame.transform.scale(sprite, sprite_cfg["target_size"])

        return sprite, sprite_cfg["offset"]

    def get_effect(self, effect_name, effect_cfg, frame=0):
        effect = effect_cfg["effects"][effect_name]
        row = effect["row"]
        col = effect.get("col", 0) + frame
        return self.get_image_centered(col, row, effect_cfg)
