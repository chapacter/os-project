import os

import pygame

from utils.settings import GREEN, RED, YELLOW


class HUD:
    def __init__(self, game):
        self.game = game
        self.is_active = True

        self.health_bar_width = 200
        self.health_bar_height = 20

        self.health_bar_bg = pygame.Surface(
            (self.health_bar_width, self.health_bar_height)
        )
        self.health_bar_bg.fill((50, 50, 50))

        self.health_bar = pygame.Surface(
            (self.health_bar_width - 4, self.health_bar_height - 4)
        )
        self.health_bar.fill(GREEN)

        self._weapon_icons = {}
        for name in ["double_weapon", "cone_weapon", "pierce_weapon", "explode_weapon", "boomerang_weapon"]:
            path = f"assets/{name}.png"
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                self._weapon_icons[name] = pygame.transform.scale2x(img)

    def update(self, time_delta):
        if hasattr(self.game, "player") and self.game.player:
            health = self.game.player.health
            max_health = 10
            health_percent = max(0, min(1, health / max_health))

            self.health_bar = pygame.Surface((int((196) * health_percent), 16))
            if health_percent > 0.5:
                self.health_bar.fill(GREEN)
            elif health_percent > 0.25:
                self.health_bar.fill(YELLOW)
            else:
                self.health_bar.fill(RED)

    def draw(self, surface):
        surface.blit(self.health_bar_bg, (80, 22))
        surface.blit(self.health_bar, (82, 24))

        if hasattr(self.game, "player") and self.game.player:
            p = self.game.player

            font = pygame.font.Font(None, 22)
            gold = (255, 215, 0)
            coin_text = font.render(f"Coins: {getattr(p, 'coins', 0)}", True, gold)
            surface.blit(coin_text, (80, 85))

            mapping = [
                ("double_weapon", "double_attack_unlocked"),
                ("cone_weapon", "cone_attack_unlocked"),
                ("pierce_weapon", "pierce_unlocked"),
                ("explode_weapon", "explode_unlocked"),
                ("boomerang_weapon", "boomerang_unlocked"),
            ]
            x, y = 80, 50
            for icon_name, flag in mapping:
                if getattr(p, flag, False) and icon_name in self._weapon_icons:
                    surface.blit(self._weapon_icons[icon_name], (x, y))
                    x += 36

    def show(self):
        self.is_active = True

    def hide(self):
        self.is_active = False

    def update_texts(self):
        pass
