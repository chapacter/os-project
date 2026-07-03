import pygame

from map.door_physics import DoorPhysics
from map.door_state import DoorStateMachine
from utils.settings import *


class Door(pygame.sprite.Sprite):
    def __init__(self, game, x, y, direction, from_room_coord, to_room_coord, transform=None):
        self.game = game
        self._layer = GROUND_LAYER
        self.groups = game.all_sprites, game.doors
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.render_mode = "perspective"

        self.x = x * TILESIZE
        self.y = y * TILESIZE
        self.width = TILESIZE
        self.height = TILESIZE

        self.direction = direction
        self.from_room_coord = from_room_coord
        self.to_room_coord = to_room_coord
        self.transform = transform

        self.state_machine = DoorStateMachine()
        self.physics = DoorPhysics(game)
        self.frames = self._load_frames()
        self.image = self.frames[-1]
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

    @property
    def state(self):
        return self.state_machine.state

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
        if not self.state_machine.start_closing(len(self.frames)):
            return

    def open(self):
        if not self.state_machine.start_opening():
            return
        self.physics.remove(self.rect)
        self._layer = GROUND_LAYER
        if self in self.game.blocks:
            self.game.blocks.remove(self)

    def _register_physics(self):
        self.physics.register(self.rect)

    def _remove_physics(self):
        self.physics.remove(self.rect)

    def update(self):
        result = self.state_machine.update(len(self.frames))
        if result == "closed":
            self._register_physics()
            self._layer = BLOCKS_LAYER
            self.game.blocks.add(self)
        if result in ("closed", "animating", "opened"):
            self.image = self.frames[self.state_machine.anim_frame]
