import pygame

from utils.settings import *


class VectorEntity:
    def __init__(self):
        self.velocity = pygame.math.Vector2(0, 0)

    def get_direction_from_velocity(self):
        vx, vy = self.velocity.x, self.velocity.y
        if abs(vx) > abs(vy):
            return "right" if vx > 0 else "left"
        elif vy != 0:
            return "down" if vy > 0 else "up"
        return getattr(self, "direction", "right")

    def move_by_velocity(self):
        self.rect.x += self.velocity.x
        self.rect.y += self.velocity.y

    def resolve_block_collision(self, blocks, speed):
        for block in blocks:
            if self.hitbox.colliderect(block.rect):
                overlap_x = min(
                    self.rect.right - block.rect.left, block.rect.right - self.rect.left
                )
                overlap_y = min(
                    self.rect.bottom - block.rect.top, block.rect.bottom - self.rect.top
                )
                if overlap_x < overlap_y:
                    if self.rect.centerx < block.rect.centerx:
                        self.rect.x -= overlap_x
                    else:
                        self.rect.x += overlap_x
                else:
                    if self.rect.centery < block.rect.centery:
                        self.rect.y -= overlap_y
                    else:
                        self.rect.y += overlap_y
                return True
        return False


class Entity(VectorEntity, pygame.sprite.Sprite):
    def __init__(self, game, x, y, layer, groups):
        self.game = game
        self._layer = layer
        self.groups = groups
        pygame.sprite.Sprite.__init__(self, self.groups)

        VectorEntity.__init__(self)

        self.x = x * TILESIZE
        self.y = y * TILESIZE
        self.width = TILESIZE
        self.height = TILESIZE

        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

        self.hitbox = pygame.Rect(0, 0, HITBOX_WIDTH, HITBOX_HEIGHT)
        self.hitbox.center = self.rect.center

    def update_hitbox(self):
        self.hitbox.center = self.rect.center


class Healthbar(pygame.sprite.Sprite):
    def __init__(self, game, x, y, entity=None):
        self.game = game
        self._layer = HEALTH_LAYER
        self.groups = game.all_sprites, game.healthbar
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * TILESIZE
        self.y = y * TILESIZE
        self.width = 30
        self.height = 10

        self.image = pygame.Surface([self.width, self.height])
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y - TILESIZE / 2

        self.entity = entity

    def move(self):
        self.rect.x = self.entity.rect.x
        self.rect.y = self.entity.rect.y - TILESIZE / 2

    def damage(self, total_health, health):
        self.image.fill(RED)
        width = self.rect.width * health / total_health
        pygame.draw.rect(self.image, GREEN, (0, 0, width, self.height), 0)

    def kill_bar(self):
        self.kill()

    def update(self):
        self.move()
