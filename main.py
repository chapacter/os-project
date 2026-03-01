import json
import os
import random
import sys

import pygame
import pygame_gui
import pytmx

from audio import audio_manager
from camera import Camera
from entity.enemy import Enemy
from entity.player import Player
from items.weapon import Weapon
from map import Map
from map.dungeon_generator import DungeonGenerator
from map.tilemap import Block, Ground
from map.tmx_loader import TiledLoader
from map.world_generator import WorldGenerator
from physics import PhysicsEngine
from settings import *
from sprites import Spritesheet


class GameMode:
    WORLD = "world"
    DUNGEON = "dungeon"
    TMX = "tmx"


class Game:
    def __init__(self):
        self.sc = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.terrain_spritesheet = Spritesheet("assets/tileset.png")
        self.player_spritesheet = Spritesheet("assets/player.png")
        self.enemy_spritesheet = Spritesheet("assets/enemy.png")
        self.weapon_spritesheet = Spritesheet("assets/sword.png")
        self.bullet_spritesheet = Spritesheet("assets/powerBall.png")

        self.running = True
        self.enemy_collided = False
        self.block_collided = False

        self.mode = GameMode.WORLD
        self.current_zone = (0, 0)
        self.world_generator = None
        self.dungeon_generator = None
        self.current_dungeon_floor = 1

        self.fade_surface = pygame.Surface((WIN_WIDTH, WIN_HEIGHT))
        self.fade_alpha = 0
        self.is_fading = False
        self.fade_direction = 0
        self.fade_callback = None

        self.tmx_loader = TiledLoader(self)
        self.current_tmx_map = None

        self.game_state = "menu"
        self.ui_manager = None
        self.main_menu = None
        self.pause_menu = None
        self.hud = None

        self.physics = None
        self.physics_enabled = False

        self.camera = None
        self.camera_enabled = True

        self.audio_enabled = False
        self.audio = audio_manager

    def init_ui(self):
        from ui.menu import MainMenu
        from ui.pause import PauseMenu
        from ui.hud import HUD

        self.ui_manager = pygame_gui.UIManager((WIN_WIDTH, WIN_HEIGHT))
        self.main_menu = MainMenu(self)
        self.pause_menu = PauseMenu(self)
        self.hud = HUD(self)
        self.main_menu.show()

    def init_world(self):
        zone_w = WORLD_ZONE_WIDTH
        zone_h = WORLD_ZONE_HEIGHT
        self.world_generator = WorldGenerator(zone_w, zone_h)
        self.world = self.world_generator.generate_world()

    def load_zone(self, zone_x, zone_y):
        self.clear_sprites()

        if (zone_x, zone_y) not in self.world:
            self.world[(zone_x, zone_y)] = self.world_generator.get_zone_at(
                zone_x, zone_y
            )

        level = self.world[(zone_x, zone_y)]

        for i, row in enumerate(level):
            for j, column in enumerate(row):
                if column == "P":
                    self.player = Player(self, j, i)
                elif column == "E" and self.mode == GameMode.WORLD:
                    if random.random() < 0.3:
                        Enemy(self, j, i)
                elif column == "W":
                    Weapon(self, j, i)
                elif column == "D":
                    self.create_dungeon_entrance(j, i)
                elif column == "V":
                    Ground(self, j, i)
                elif column == "H":
                    Ground(self, j, i)
                else:
                    Ground(self, j, i)
                    if column == "B" or column == "L":
                        Block(self, j, i)

    def create_dungeon_entrance(self, x, y):
        Ground(self, x, y)
        from map.tilemap import DungeonEntrance

        DungeonEntrance(self, x, y)

    def enter_dungeon(self):
        self.mode = GameMode.DUNGEON
        self.dungeon_generator = DungeonGenerator()
        self.current_dungeon_floor = 1
        self.load_dungeon_floor()

    def load_dungeon_floor(self):
        self.clear_sprites()

        level = self.dungeon_generator.generate_floor(self.current_dungeon_floor)

        for i, row in enumerate(level):
            for j, column in enumerate(row):
                Ground(self, j, i)
                if column == "B":
                    Block(self, j, i)
                elif column == "T":
                    from map.tilemap import Decoration

                    Decoration(self, j, i, "tree")

        start_x, start_y = self.dungeon_generator.get_start_position()
        self.player = Player(self, start_x, start_y)

        self.spawn_dungeon_enemies()

    def spawn_dungeon_enemies(self):
        for (gx, gy), room in self.dungeon_generator.rooms.items():
            if room.room_type.value in ["enemy", "elite", "boss"]:
                room_x = gx * 10 + 3
                room_y = gy * 8 + 2
                if room.room_type.value == "boss":
                    for _ in range(1):
                        Enemy(self, room_x, room_y, is_boss=True)
                elif room.room_type.value == "elite":
                    for _ in range(2):
                        Enemy(
                            self,
                            room_x + random.randint(-1, 1),
                            room_y + random.randint(-1, 1),
                            is_elite=True,
                        )
                else:
                    for _ in range(random.randint(1, 3)):
                        Enemy(
                            self,
                            room_x + random.randint(-2, 2),
                            room_y + random.randint(-2, 2),
                        )

    def exit_dungeon(self, go_deeper=False):
        if go_deeper and self.current_dungeon_floor < DUNGEON_FLOORS:
            self.current_dungeon_floor += 1
            self.load_dungeon_floor()
        else:
            self.mode = GameMode.WORLD
            self.load_zone(self.current_zone[0], self.current_zone[1])

    def clear_sprites(self):
        for group in [
            self.all_sprites,
            self.blocks,
            self.water,
            self.enemies,
            self.mainPlayer,
            self.weapons,
            self.bullets,
            self.healthbar,
            self.characters,
        ]:
            group.empty()

    def create_tile_map(self):
        if MAP_GENERATOR == "walker":
            map_width = int(WIN_WIDTH / TILESIZE * 1.3)
            map_height = int(WIN_HEIGHT / TILESIZE)
            map_gen = Map(map_width, map_height)
            level = map_gen.create()

            for i, row in enumerate(level):
                for j, column in enumerate(row):
                    Ground(self, j, i)
                    if column == "B":
                        Block(self, j, i)
                    if column == "P":
                        self.player = Player(self, j, i)
                    if column == "E":
                        Enemy(self, j, i)
                    if column == "W":
                        Weapon(self, j, i)
        elif MAP_GENERATOR == "tmx":
            self.mode = GameMode.TMX
        else:
            self.init_world()
            self.load_zone(0, 0)

    def load_tmx_map(self, filename):
        self.mode = GameMode.TMX
        self.current_tmx_file = filename

        layer_mapping = {
            "Ground": "ground",
            "Blocks": "block",
            "Water": "water",
            "Enemies": "enemy",
            "Player": "player",
            "Weapons": "weapon",
            "Objects": "object",
        }

        result = self.tmx_loader.load_tmx_to_sprites(filename, layer_mapping)

        if not result or not result["map"] or not result["map"].tmx_data:
            print(f"Failed to load TMX map: {filename}")
            return

        self.current_tmx_map = result["map"]

        for layer_name, tiles in result["tiles"].items():
            for tile in tiles:
                x = tile["x"]
                y = tile["y"]

                if tile["type"] == "ground":
                    Ground(self, x, y)
                elif tile["type"] == "block":
                    Block(self, x, y)
                elif tile["type"] == "water":
                    from map.tilemap import Water

                    Water(self, x, y)
                elif tile["type"] == "enemy":
                    if random.random() < 0.3:
                        Enemy(self, x, y)
                elif tile["type"] == "weapon":
                    Weapon(self, x, y)

        player_placed = False
        for obj_group in result["map"].tmx_data.visible_layers:
            if isinstance(obj_group, pytmx.TiledObjectGroup):
                for obj in obj_group:
                    if obj.name == "Player":
                        self.player = Player(
                            self, int(obj.x // TILESIZE), int(obj.y // TILESIZE)
                        )
                        player_placed = True
                        break
                if player_placed:
                    break

        if not player_placed:
            self.player = Player(self, 5, 5)

    def create(self):
        self.all_sprites = pygame.sprite.LayeredUpdates()
        self.blocks = pygame.sprite.LayeredUpdates()
        self.water = pygame.sprite.LayeredUpdates()
        self.enemies = pygame.sprite.LayeredUpdates()
        self.mainPlayer = pygame.sprite.LayeredUpdates()
        self.weapons = pygame.sprite.LayeredUpdates()
        self.bullets = pygame.sprite.LayeredUpdates()
        self.healthbar = pygame.sprite.LayeredUpdates()
        self.characters = pygame.sprite.LayeredUpdates()
        self.decorations = pygame.sprite.LayeredUpdates()
        self.dungeon_entrances = pygame.sprite.LayeredUpdates()

        if self.physics_enabled:
            self.init_physics_world()

        if self.camera_enabled:
            self.init_camera()

        self.create_tile_map()

    def init_camera(self):
        map_w = WORLD_ZONE_WIDTH * TILESIZE if self.mode == GameMode.WORLD else 2000
        map_h = WORLD_ZONE_HEIGHT * TILESIZE if self.mode == GameMode.WORLD else 2000
        self.camera = Camera(WIN_WIDTH, WIN_HEIGHT, map_w, map_h)

    def init_physics_world(self):
        if self.physics:
            del self.physics
        self.physics = PhysicsEngine()

    def create_physics_for_block(self, block):
        if self.physics and self.physics_enabled:
            self.physics.add_static_block(
                block.rect.x,
                block.rect.y,
                block.rect.width,
                block.rect.height,
                f"block_{block.rect.x}_{block.rect.y}",
            )

    def start_new_game(self):
        self.game_state = "playing"
        self.current_zone = (0, 0)
        self.current_dungeon_floor = 1
        self.main_menu.hide()
        self.create()
        self.hud.show()

    def load_game(self):
        if os.path.exists("savegame.json"):
            try:
                with open("savegame.json", "r") as f:
                    save_data = json.load(f)
                self.game_state = "playing"
                self.current_zone = tuple(save_data.get("zone", (0, 0)))
                self.current_dungeon_floor = save_data.get("floor", 1)
                self.main_menu.hide()
                self.create()
                self.hud.show()
            except Exception as e:
                print(f"Error loading save: {e}")
                self.start_new_game()
        else:
            self.start_new_game()

    def save_game(self):
        save_data = {
            "zone": self.current_zone,
            "floor": self.current_dungeon_floor,
            "mode": self.mode,
        }
        try:
            with open("savegame.json", "w") as f:
                json.dump(save_data, f)
            print("Game saved!")
        except Exception as e:
            print(f"Error saving game: {e}")

    def open_settings(self):
        print("Settings menu - coming soon!")

    def quit_game(self):
        self.running = False
        pygame.quit()
        sys.exit()

    def return_to_menu(self):
        self.game_state = "menu"
        self.main_menu.show()
        self.hud.hide()

    def pause(self):
        if self.game_state == "playing":
            self.game_state = "paused"
            self.pause_menu.show()

    def resume(self):
        if self.game_state == "paused":
            self.game_state = "playing"
            self.pause_menu.hide()

    def update(self):
        self.all_sprites.update()

        if self.physics_enabled and self.physics:
            self.physics.update(1.0 / 60.0)

        if hasattr(self, "player") and self.player:
            print(
                f"Game update: player at x={self.player.rect.x}, y={self.player.rect.y}"
            )

        if (
                self.camera_enabled
                and self.camera
                and hasattr(self, "player")
                and self.player
        ):
            self.camera.follow_sprite(self.player)
            self.camera.update(1.0 / 60.0)

    def events(self):
        time_delta = self.clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.game_state == "playing":
                        self.pause()
                    elif self.game_state == "paused":
                        self.resume()
                    else:
                        pygame.quit()
                        sys.exit()

            if self.game_state == "menu":
                self.main_menu.handle_event(event)
            elif self.game_state == "paused":
                self.pause_menu.handle_event(event)

    def draw(self):
        if self.game_state == "menu":
            self.sc.fill(BLACK)
            self.main_menu.draw(self.sc)
        elif self.game_state == "paused":
            self.sc.fill(BLACK)
            for sprite in self.all_sprites.sprites():
                self.sc.blit(sprite.image, self.camera.apply(sprite))
            self.pause_menu.draw(self.sc)
        elif self.game_state == "playing":
            self.sc.fill(BLACK)
            for sprite in self.all_sprites.sprites():
                self.sc.blit(sprite.image, self.camera.apply(sprite))
            self.hud.draw(self.sc)

        if self.is_fading:
            self.fade_surface.set_alpha(int(self.fade_alpha))
            self.sc.blit(self.fade_surface, (0, 0))

        self.clock.tick(FPS)
        pygame.display.update()

    def fade_out(self, callback=None, duration=FADE_DURATION):
        self.is_fading = True
        self.fade_direction = 1
        self.fade_alpha = 0.0
        self.fade_callback = callback
        self.fade_duration = duration

    def fade_in(self, callback=None, duration=FADE_DURATION):
        self.is_fading = True
        self.fade_direction = -1
        self.fade_alpha = 255.0
        self.fade_callback = callback
        self.fade_duration = duration

    def update_fade(self):
        if not self.is_fading:
            return

        step = 255 / (self.fade_duration / 16.67)

        if self.fade_direction == 1:
            self.fade_alpha += step
            if self.fade_alpha >= 255:
                self.fade_alpha = 255
                if self.fade_callback:
                    self.fade_callback()
                self.fade_callback = None
        else:
            self.fade_alpha -= step
            if self.fade_alpha <= 0:
                self.fade_alpha = 0
                self.is_fading = False
                if self.fade_callback:
                    self.fade_callback()
                self.fade_callback = None

    def check_zone_transition(self):
        if self.mode != GameMode.WORLD:
            return

        if not hasattr(self, "player"):
            return

        player_tile_x = int(self.player.rect.x / TILESIZE)
        player_tile_y = int(self.player.rect.y / TILESIZE)

        zone_w = WORLD_ZONE_WIDTH
        zone_h = WORLD_ZONE_HEIGHT

        new_zone = None

        if player_tile_x < 0:
            new_zone = (self.current_zone[0] - 1, self.current_zone[1])
        elif player_tile_x >= zone_w - 1:
            new_zone = (self.current_zone[0] + 1, self.current_zone[1])
        elif player_tile_y < 0:
            new_zone = (self.current_zone[0], self.current_zone[1] - 1)
        elif player_tile_y >= zone_h - 1:
            new_zone = (self.current_zone[0], self.current_zone[1] + 1)

        if new_zone and -1 <= new_zone[0] <= 1 and -1 <= new_zone[1] <= 1:

            def do_transition():
                self.current_zone = new_zone
                offset_x = 0
                offset_y = 0
                if new_zone[0] < self.current_zone[0]:
                    offset_x = -zone_w + 2
                elif new_zone[0] > self.current_zone[0]:
                    offset_x = zone_w - 2
                elif new_zone[1] < self.current_zone[1]:
                    offset_y = -zone_h + 2
                elif new_zone[1] > self.current_zone[1]:
                    offset_y = zone_h - 2

                self.load_zone(new_zone[0], new_zone[1])

                self.player.rect.x += offset_x * TILESIZE
                self.player.rect.y += offset_y * TILESIZE

                self.fade_in()

            self.fade_out(do_transition)

    def handle_camera_movement(self):
        pass

    def main(self):
        while self.running:
            time_delta = self.clock.tick(60) / 1000.0

            self.events()

            if self.game_state == "menu":
                self.main_menu.update(time_delta)
            elif self.game_state == "paused":
                self.pause_menu.update(time_delta)
            elif self.game_state == "playing":
                self.update_fade()
                if not self.is_fading or self.fade_direction == -1:
                    self.check_zone_transition()
                    self.handle_camera_movement()
                    self.update()
                    if self.camera:
                        self.camera.follow_sprite(self.player)
                        self.camera.update(1.0 / 60.0)
                self.hud.update(time_delta)

            self.draw()


if __name__ == "__main__":
    pygame.init()
    game = Game()
    game.init_ui()

    while game.running:
        game.main()

    pygame.quit()
    sys.exit()
