import pygame

from utils.settings import *


class DoorState:
    OPEN = "open"
    CLOSING = "closing"
    CLOSED = "closed"
    OPENING = "opening"


class Door(pygame.sprite.Sprite):
    ANIMATION_SPEED = 3

    def __init__(self, game, x, y, direction, from_room_coord, to_room_coord, transform=None):
        self.game = game
        self._layer = GROUND_LAYER
        self.groups = game.all_sprites, game.doors
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * TILESIZE
        self.y = y * TILESIZE
        self.width = TILESIZE
        self.height = TILESIZE

        self.direction = direction
        self.from_room_coord = from_room_coord
        self.to_room_coord = to_room_coord
        self.transform = transform

        self.state = DoorState.OPEN
        self.frames = self._load_frames()
        self.anim_frame = 0
        self.anim_counter = 0

        self.image = self.frames[-1]
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

    def _load_frames(self):
        frames = []
        sheet = self.game.terrain_spritesheet
        sprite_row = 4
        for col in range(4):
            sx = col * TILESIZE
            sy = sprite_row * TILESIZE
            tile = sheet.get_image(sx, sy, TILESIZE, TILESIZE)
            if self.transform == "flip_h":
                tile = pygame.transform.flip(tile, True, False)
            elif self.transform == "rotate_90":
                tile = pygame.transform.rotate(tile, 90)
            elif self.transform == "rotate_270":
                tile = pygame.transform.rotate(tile, 270)
            frames.append(tile)
        return frames

    def close(self):
        if self.state == DoorState.CLOSED:
            return
        self.state = DoorState.CLOSING
        self.anim_frame = len(self.frames) - 1
        self.anim_counter = 0

    def open(self):
        if self.state == DoorState.OPEN:
            return
        self.state = DoorState.OPENING
        self.anim_frame = 0
        self.anim_counter = 0
        self._remove_physics()
        self._layer = GROUND_LAYER
        if self in self.game.blocks:
            self.game.blocks.remove(self)

    def _register_physics(self):
        if self.game.physics_enabled and self.game.physics:
            self.game.physics.add_static_block(
                self.rect.x, self.rect.y,
                self.rect.width, self.rect.height,
                f"door_{self.rect.x}_{self.rect.y}",
            )

    def _remove_physics(self):
        if self.game.physics:
            self.game.physics.remove_shape(f"door_{self.rect.x}_{self.rect.y}")

    def update(self):
        if self.state == DoorState.CLOSING:
            self.anim_counter += 1
            if self.anim_counter >= self.ANIMATION_SPEED:
                self.anim_counter = 0
                self.anim_frame -= 1
                if self.anim_frame <= 0:
                    self.anim_frame = 0
                    self.state = DoorState.CLOSED
                    self._register_physics()
                    self._layer = BLOCKS_LAYER
                    self.game.blocks.add(self)
                self.image = self.frames[self.anim_frame]

        elif self.state == DoorState.OPENING:
            self.anim_counter += 1
            if self.anim_counter >= self.ANIMATION_SPEED:
                self.anim_counter = 0
                self.anim_frame += 1
                if self.anim_frame >= len(self.frames) - 1:
                    self.anim_frame = len(self.frames) - 1
                    self.state = DoorState.OPEN
                self.image = self.frames[self.anim_frame]
