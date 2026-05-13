import json
import os
import random
import sys

import pygame
import pygame_gui
import pytmx

from entity.boss import Boss
from entity.enemy import Enemy
from entity.player import Player
from items.chest import Chest
from items.weapon import Weapon
from map.door import Door
from map.dungeon_generator import DungeonGenerator
from map.tilemap import Block, Ground, DungeonEntrance, Decoration, Water, NPC
from map.tmx_loader import TiledLoader
from map.world_generator import WorldGenerator
from sprites import Spritesheet
from ui.font_manager import font_manager, FONTS
from ui.hud import HUD
from ui.menu import MainMenu
from ui.pause import PauseMenu
from utils import config, weighted_choice
from utils.audio import audio_manager
from utils.camera import Camera
from utils.config import get_language, get_font
from utils.physics import PhysicsEngine
from utils.settings import *


class GameMode:
    WORLD = "world"
    DUNGEON = "dungeon"
    TMX = "tmx"


class Game:
    def __init__(self):
        config.load_config()
        font_manager.init(get_language(), get_font())
        audio_manager.sync_from_config()
        self.scale = config.get_scale()
        self.sc = self.create_window()
        self.clock = pygame.time.Clock()
        self.terrain_spritesheet = Spritesheet("assets/blocs.png")
        self.player_spritesheet = Spritesheet(SPRITE_PLAYER["sheet"])
        self.enemy_spritesheets = {
            enemy_type: Spritesheet(cfg["sheet"])
            for enemy_type, cfg in ENEMY_TYPES.items()
        }
        self.weapon_spritesheet = Spritesheet("assets/sword.png")
        self.effects_spritesheet = Spritesheet("assets/effects.png")

        audio_manager.init()
        audio_manager.load_sound("hit", "assets/sounds/Hit.wav")
        audio_manager.load_sound("swipe", "assets/sounds/Swipe.wav")
        audio_manager.load_sound("evade", "assets/sounds/Evade.wav")
        audio_manager.load_sound("pause", "assets/sounds/Pause.wav")
        audio_manager.load_sound("unpause", "assets/sounds/Unpause.wav")
        audio_manager.load_sound("menu_select", "assets/sounds/Menu Select.wav")
        audio_manager.load_sound("menu_move", "assets/sounds/Menu Move.wav")
        audio_manager.load_music("assets/sounds/New_Menu_Music.mp3")
        audio_manager.play_music()
        print(f"[DEBUG] Audio initialized: {audio_manager.initialized}")
        print(f"[DEBUG] Loaded sounds: {list(audio_manager.sounds.keys())}")

        self.running = True
        self.enemy_collided = False
        self.block_collided = False

        self.mode = GameMode.WORLD
        self.current_zone = (0, 0)
        self.world_seed = None
        self.dungeon_seed = None
        self.world_generator = None
        self.dungeon_generator = None
        self.current_dungeon_floor = 1
        self._dungeon_built_rooms = set()
        self._door_frame_counter = 0
        self._pending_room_for_enemies = None

        self.fade_surface = pygame.Surface((1, 1))
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
        self.physics_enabled = True

        self.camera = None
        self.camera_enabled = True

        self.audio_enabled = False
        self.audio = audio_manager

        self.render_surface = None
        self.target_scale = self.scale
        self.current_scale = self.scale
        self.scale_speed = 0.1

    def create_window(self):
        mode = config.get_window_mode()
        display_index = config.get_display()

        try:
            screen_w, screen_h = config.get_display_resolution(display_index)
        except Exception:
            screen_w, screen_h = config.get_screen_size()
            print(
                f"[WARNING] Display {display_index} unavailable, falling back to primary"
            )

        flags = 0

        if mode == "fullscreen":
            flags = pygame.FULLSCREEN
            width = screen_w
            height = screen_h
        elif mode == "borderless":
            flags = pygame.NOFRAME
            width = screen_w
            height = screen_h
        elif mode == "windowed":
            width, height = config.get_window_size()
        else:
            width, height = screen_w, screen_h

        self.sc = pygame.display.set_mode((width, height), flags, display=display_index)
        self.render_surface = pygame.Surface(
            (int(width / self.scale), int(height / self.scale))
        )
        self.fade_surface = pygame.Surface((width, height))
        return self.sc

    def toggle_fullscreen(self):
        next_mode = config.get_next_window_mode()
        config.set_window_mode(next_mode)
        self.sc = self.create_window()
        self.render_surface = pygame.Surface(
            (
                int(self.sc.get_width() / self.current_scale),
                int(self.sc.get_height() / self.current_scale),
            )
        )
        self.fade_surface = pygame.Surface((self.sc.get_width(), self.sc.get_height()))
        if hasattr(self, "camera"):
            self.camera.screen_width = self.render_surface.get_width()
            self.camera.screen_height = self.render_surface.get_height()
        if hasattr(self, "ui_manager"):
            self.ui_manager = pygame_gui.UIManager(
                (self.sc.get_width(), self.sc.get_height())
            )

    def init_ui(self):
        self.ui_manager = pygame_gui.UIManager(self.sc.get_size())
        self.main_menu = MainMenu(self)
        self.pause_menu = PauseMenu(self)
        self.hud = HUD(self)
        self.main_menu.show()

    def init_world(self):
        zone_w = WORLD_ZONE_WIDTH
        zone_h = WORLD_ZONE_HEIGHT
        self.world_generator = WorldGenerator(zone_w, zone_h, self.world_seed)
        self.world = self.world_generator.pregenerate_all_zones()

    def load_zone(self, zone_x, zone_y):
        # print(f"[DEBUG] load_zone called: ({zone_x}, {zone_y})")
        self.clear_sprites()
        # print(f"[DEBUG] After clear_sprites: {len(self.all_sprites)} sprites")

        zone_w = WORLD_ZONE_WIDTH
        zone_h = WORLD_ZONE_HEIGHT

        if (zone_x, zone_y) not in self.world:
            # print(f"[DEBUG] Generating new zone ({zone_x}, {zone_y})")
            self.world[(zone_x, zone_y)] = self.world_generator.get_zone_at(
                zone_x, zone_y
            )

        level = self.world[(zone_x, zone_y)]
        # print(f"[DEBUG] Zone size: {len(level)} rows x {len(level[0]) if level else 0} cols")

        sprite_count = 0
        ground_count = 0
        for i, row in enumerate(level):
            for j, column in enumerate(row):
                if column == "P":
                    self.player = Player(self, j, i)
                    sprite_count += 1
                elif column == "E" and self.mode == GameMode.WORLD:
                    if random.random() < 0.3:
                        Enemy(self, j, i)
                        sprite_count += 1
                elif column == "W":
                    Weapon(self, j, i)
                    sprite_count += 1
                elif column == "D":
                    self.create_dungeon_entrance(j, i)
                    sprite_count += 1
                elif column == "X":
                    self.create_portal(j, i)
                    sprite_count += 1
                elif column == "V":
                    Ground(self, j, i, "V")
                    sprite_count += 1
                    ground_count += 1
                elif column == "H":
                    Ground(self, j, i, "H")
                    sprite_count += 1
                    ground_count += 1
                elif column == "N":
                    Ground(self, j, i, "N")
                    self.create_npc(j, i)
                    sprite_count += 1
                    ground_count += 1
                else:
                    Ground(self, j, i, column)
                    sprite_count += 1
                    ground_count += 1
                    if column == "B" or column == "L":
                        Block(self, j, i)
                        sprite_count += 1

        in_sprites = hasattr(self.player, "rect") and self.player in self.all_sprites
        if not in_sprites:
            self.player = Player(self, 2, 2)

        # print(f"[DEBUG] Created {sprite_count} sprites ({ground_count} ground), total: {len(self.all_sprites)}, player_in_sprites: {in_sprites}")
        # print(f"[DEBUG] Player rect after load: {self.player.rect}")
        if hasattr(self, "camera"):
            print(
                f"[DEBUG] Camera: pos=({self.camera.scroll_x}, {self.camera.scroll_y}), map_size=({self.camera.map_width}, {self.camera.map_height})"
            )

    def create_dungeon_entrance(self, x, y):
        Ground(self, x, y, "B")
        DungeonEntrance(self, x, y)

    def create_portal(self, x, y):
        Ground(self, x, y, "B")
        DungeonEntrance(self, x, y)

    def create_npc(self, x, y):
        Ground(self, x, y, "N")

        NPC(self, x, y)

    def enter_dungeon(self):
        self.mode = GameMode.DUNGEON
        self.dungeon_generator = DungeonGenerator()
        self.current_dungeon_floor = 1
        self.load_dungeon_floor()

    def load_dungeon_floor(self):
        self.clear_sprites()
        self._dungeon_built_rooms = set()

        level = self.dungeon_generator.generate_floor(self.current_dungeon_floor)
        self._tile_map_cache = level

        audio_manager.load_music("assets/sounds/Music.mp3")
        audio_manager.play_music()

        self.dungeon_generator.set_start_room_visible()

        self._rebuild_visible_rooms()

        self.create_dungeon_doors()

        self.spawn_dungeon_enemies()

        start_x, start_y = self.dungeon_generator.get_start_position()
        # print(f"[DEBUG] Player spawn position: {start_x}, {start_y}, map_size: {self.dungeon_generator.map_width}x{self.dungeon_generator.map_height}")
        self.player = Player(self, start_x, start_y)
        # print(f"[DEBUG] Player created at: {self.player.rect.x}, {self.player.rect.y}")

        if hasattr(self, "camera"):
            self.camera.set_map_size(
                self.dungeon_generator.map_width * TILESIZE,
                self.dungeon_generator.map_height * TILESIZE,
            )
            # print(f"[DEBUG] Camera map_size set to: {self.camera.map_width}x{self.camera.map_height}")
            self.camera.center_on(self.player.rect.x, self.player.rect.y)
            # print(f"[DEBUG] Camera centered: scroll={self.camera.scroll_x},{self.camera.scroll_y}")

    def create_dungeon_doors(self):
        for door_info in self.dungeon_generator.get_doors():
            Door(
                self,
                door_info["x"],
                door_info["y"],
                door_info["direction"],
                door_info["from_room"],
                door_info["to_room"],
            )

    def spawn_dungeon_enemies(self, room_coord=None):
        room_tile_width = self.dungeon_generator.room_tile_width
        room_tile_height = self.dungeon_generator.room_tile_height
        wall_thickness = self.dungeon_generator.wall_thickness
        room_unit_width = room_tile_width + wall_thickness * 2
        room_unit_height = room_tile_height + wall_thickness * 2

        rooms_to_spawn = []
        if room_coord:
            if room_coord in self.dungeon_generator.rooms:
                rooms_to_spawn = [room_coord]
        else:
            rooms_to_spawn = [
                (gx, gy)
                for (gx, gy), room in self.dungeon_generator.rooms.items()
                if room.visible
            ]

        total_enemies = 0
        for gx, gy in rooms_to_spawn:
            room = self.dungeon_generator.rooms.get((gx, gy))
            if not room:
                continue
            if room.enemy_count > 0:
                # print(f"[DEBUG] Room {gx},{gy} already has {room.enemy_count} enemies, skipping spawn")
                continue
            if room.enemies_spawned:
                # print(f"[DEBUG] Room {gx},{gy} already spawned enemies, skipping")
                continue
            room.enemy_count = 0
            print(f"[DEBUG] Room {gx},{gy} spawning enemies, type: {room.room_type.value}")
            # Skip START rooms - no enemies here
            if room.room_type.value == "start":
                room.enemies_spawned = True
                continue
            if room.room_type.value == "boss":
                room.enemies_spawned = True
                boss_pos = self.dungeon_generator.get_boss_position()
                if boss_pos:
                    Boss(self, boss_pos[0], boss_pos[1])
                    room.enemy_count = 1
                    total_enemies += 1
            elif room.room_type.value in ["enemy", "elite"]:
                room.enemies_spawned = True
                room_x = gx * room_unit_width + wall_thickness + 3
                room_y = gy * room_unit_height + wall_thickness + 2
                for _ in range(random.randint(2, 4)):
                    if self.current_dungeon_floor == 2:
                        enemy_type = random.choice([5, 6, 7])
                    elif self.current_dungeon_floor == 3:
                        enemy_type = random.choice([8, 9, 10])
                    else:
                        type_weights = {k: v["weight"] for k, v in ENEMY_TYPES.items() if k < 5}
                        enemy_type = weighted_choice(type_weights)
                    Enemy(
                        self,
                        room_x + random.randint(-2, 2),
                        room_y + random.randint(-2, 2),
                        enemy_type=enemy_type,
                    )
                    room.enemy_count += 1
                    total_enemies += 1

        # print(f"[DEBUG] Spawned {total_enemies} enemies")

    def exit_dungeon(self, go_deeper=False):
        if go_deeper and self.current_dungeon_floor < DUNGEON_FLOORS:
            self.current_dungeon_floor += 1
            self.load_dungeon_floor()
        else:
            self.mode = GameMode.WORLD
            self.load_zone(self.current_zone[0], self.current_zone[1])

    def go_deeper(self):
        if self.current_dungeon_floor < DUNGEON_FLOORS:
            self.current_dungeon_floor += 1
            self.fade_out(lambda: self._reload_dungeon_floor())
        else:
            self.exit_dungeon()

    def _reload_dungeon_floor(self):
        self.clear_sprites()
        self._dungeon_built_rooms = set()
        self._tile_map_cache = None
        self._tile_map_cache = self.dungeon_generator.generate_floor(
            self.current_dungeon_floor
        )
        self.dungeon_generator.set_start_room_visible()
        self._rebuild_visible_rooms()
        self.create_dungeon_doors()
        self.spawn_dungeon_enemies()
        start_x, start_y = self.dungeon_generator.get_start_position()
        self.player = Player(self, start_x, start_y)
        self.camera.set_map_size(
            self.dungeon_generator.map_width * TILESIZE,
            self.dungeon_generator.map_height * TILESIZE,
        )
        self.camera.center_on(self.player.rect.x, self.player.rect.y)
        self.fade_in()

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
            self.decorations,
            self.dungeon_entrances,
            self.doors,
            self.npcs,
            self.chests,
            self.items,
            self.interactables,
        ]:
            group.empty()
        if self.physics:
            for name in list(self.physics.bodies.keys()):
                self.physics.remove_body(name)
            self.physics.clear_collision_flags()

    def create_tile_map(self):
        map_width_tiles = 0
        map_height_tiles = 0

        if MAP_GENERATOR == "walker":
            self.init_world()
            self.load_zone(0, 0)
            map_width_tiles = WORLD_ZONE_WIDTH
            map_height_tiles = WORLD_ZONE_HEIGHT
        elif MAP_GENERATOR == "tmx":
            self.mode = GameMode.TMX
        elif MAP_GENERATOR == "dungeon":
            self.enter_dungeon()
            map_width_tiles = self.dungeon_generator.map_width
            map_height_tiles = self.dungeon_generator.map_height
        else:
            self.init_world()
            self.load_zone(0, 0)
            map_width_tiles = WORLD_ZONE_WIDTH
            map_height_tiles = WORLD_ZONE_HEIGHT

        if (
                self.camera_enabled
                and hasattr(self, "camera")
                and (map_width_tiles > 0 or map_height_tiles > 0)
        ):
            map_w = map_width_tiles * TILESIZE
            map_h = map_height_tiles * TILESIZE
            self.camera.set_map_size(map_w, map_h)

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
            # return

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
        self.render_surface = pygame.Surface(
            (
                int(self.sc.get_width() / self.current_scale),
                int(self.sc.get_height() / self.current_scale),
            )
        )
        self.fade_surface = pygame.Surface((self.sc.get_width(), self.sc.get_height()))

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
        self.doors = pygame.sprite.LayeredUpdates()
        self.area_particles = pygame.sprite.LayeredUpdates()
        self.npcs = pygame.sprite.LayeredUpdates()
        self.chests = pygame.sprite.LayeredUpdates()
        self.items = pygame.sprite.LayeredUpdates()
        self.interactables = pygame.sprite.LayeredUpdates()

        if self.physics_enabled:
            self.init_physics_world()

        if self.camera_enabled:
            self.init_camera()

        self.create_tile_map()

    def init_camera(self):
        map_w = WORLD_ZONE_WIDTH * TILESIZE if self.mode == GameMode.WORLD else 2000
        map_h = WORLD_ZONE_HEIGHT * TILESIZE if self.mode == GameMode.WORLD else 2000
        camera_w = self.render_surface.get_width()
        camera_h = self.render_surface.get_height()
        self.camera = Camera(self, camera_w, camera_h, map_w, map_h)

    def init_physics_world(self):
        if self.physics:
            del self.physics
        self.physics = PhysicsEngine()
        self.physics.setup_entity_block_handler()
        self.physics.setup_entity_entity_handler()

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
        self.world_seed = random.randint(0, 1000000)
        self.dungeon_seed = random.randint(0, 1000000)
        self.main_menu.hide()
        self.create()
        self.hud.show()

    def load_game(self):
        if os.path.exists("savegame.json"):
            try:
                with open("savegame.json", "r") as f:
                    save_data = json.load(f)
                if not save_data.get("save_valid", False):
                    return False
                self.game_state = "playing"
                self.current_zone = tuple(save_data.get("zone", (0, 0)))
                self.current_dungeon_floor = save_data.get("floor", 1)
                self.world_seed = save_data.get(
                    "world_seed", random.randint(0, 1000000)
                )
                self.dungeon_seed = save_data.get(
                    "dungeon_seed", random.randint(0, 1000000)
                )
                self.main_menu.hide()
                self.create()
                self.hud.show()
                return True
            except Exception as e:
                # print(f"Error loading save: {e}")
                return False
        return False

    def save_game(self):
        save_data = {
            "save_valid": True,
            "zone": self.current_zone,
            "floor": self.current_dungeon_floor,
            "mode": self.mode,
            "world_seed": self.world_seed,
            "dungeon_seed": self.dungeon_seed,
        }
        try:
            with open("savegame.json", "w") as f:
                json.dump(save_data, f)
            # print("Game saved!")
        except Exception as e:
            print(f"Error saving game: {e}")

    def game_over(self):
        if os.path.exists("savegame.json"):
            try:
                with open("savegame.json", "r") as f:
                    save_data = json.load(f)
                save_data["save_valid"] = False
                with open("savegame.json", "w") as f:
                    json.dump(save_data, f)
            except Exception as e:
                print(f"Error invalidating save: {e}")

        self.game_state = "game_over"
        self.game_over_timer = 300

    def open_settings(self):
        print("Settings menu - coming soon!")

    def quit_game(self):
        self.running = False
        pygame.quit()
        sys.exit()

    def return_to_menu(self):
        self.game_state = "menu"
        audio_manager.load_music("assets/sounds/New_Menu_Music.mp3")
        audio_manager.play_music()
        self.main_menu.show()
        self.hud.hide()

    def pause(self):
        if self.game_state == "playing":
            self.game_state = "paused"
            self.pause_menu.show()
            audio_manager.play_sound("pause")

    def resume(self):
        if self.game_state == "paused":
            self.game_state = "playing"
            self.pause_menu.hide()

    def update_scale(self):
        if abs(self.current_scale - self.target_scale) > 0.005:
            self.current_scale += (
                                          self.target_scale - self.current_scale
                                  ) * self.scale_speed

            self.render_surface = pygame.Surface(
                (
                    int(self.sc.get_width() / self.current_scale),
                    int(self.sc.get_height() / self.current_scale),
                )
            )
            if hasattr(self, "camera"):
                self.camera.screen_width = self.render_surface.get_width()
                self.camera.screen_height = self.render_surface.get_height()

    def update(self):
        self.update_scale()
        self.all_sprites.update()

        if self.physics_enabled and self.physics:
            self.physics.step()
            self.physics.clear_collision_flags()

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
                elif event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                elif event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:
                    audio_manager.adjust_sfx_volume(-0.05)
                elif event.key == pygame.K_EQUALS or event.key == pygame.K_KP_PLUS:
                    audio_manager.adjust_sfx_volume(0.05)
                elif event.key == pygame.K_e:
                    if self.game_state == "playing" and hasattr(self, "player"):
                        self.player.interact()
                elif event.key == pygame.K_o:
                    current = font_manager.get_locale()
                    supported = font_manager.get_supported_locales()
                    if current in supported:
                        idx = supported.index(current)
                        new_locale = supported[(idx + 1) % len(supported)]
                    else:
                        new_locale = supported[0] if supported else "en"
                    font_manager.set_locale(new_locale)
                    audio_manager.play_sound("menu_select")
                    if self.game_state == "menu" and self.main_menu:
                        self.main_menu.update_texts()
                    elif self.game_state == "paused" and self.pause_menu:
                        self.pause_menu.update_texts()
                    elif self.game_state == "playing" and self.hud:
                        self.hud.update_texts()
                elif event.key == pygame.K_p:
                    current_font_key = font_manager.get_font_key()
                    if current_font_key.isdigit():
                        current_idx = int(current_font_key)
                        new_idx = (current_idx + 1) % len(FONTS)
                    else:
                        new_idx = 0
                    font_manager.set_font(str(new_idx))
                    audio_manager.play_sound("menu_select")
                    if self.game_state == "menu" and self.main_menu:
                        self.main_menu.update_texts()
                    elif self.game_state == "paused" and self.pause_menu:
                        self.pause_menu.update_texts()
                    elif self.game_state == "playing" and self.hud:
                        self.hud.update_texts()

            if event.type == pygame.VIDEORESIZE:
                if config.get_window_mode() == "windowed":
                    config.set_window_size(event.w, event.h)
                    self.sc = self.create_window()
                    self.render_surface = pygame.Surface(
                        (
                            int(self.sc.get_width() / self.current_scale),
                            int(self.sc.get_height() / self.current_scale),
                        )
                    )
                    self.fade_surface = pygame.Surface(
                        (self.sc.get_width(), self.sc.get_height())
                    )
                    if hasattr(self, "camera"):
                        self.camera.screen_width = self.render_surface.get_width()
                        self.camera.screen_height = self.render_surface.get_height()
                    if hasattr(self, "ui_manager"):
                        self.ui_manager = pygame_gui.UIManager(
                            (self.sc.get_width(), self.sc.get_height())
                        )

            if event.type == pygame.MOUSEWHEEL:
                new_target = max(0.25, min(4.0, self.target_scale + event.y * 0.1))
                self.target_scale = round(new_target, 1)
                config.set_scale(self.target_scale)

            if self.game_state == "menu":
                self.main_menu.handle_event(event)
            elif self.game_state == "paused":
                self.pause_menu.handle_event(event)

    def draw(self):
        if self.game_state == "menu":
            self.sc.fill(BLACK)
            self.main_menu.draw(self.sc)
        elif self.game_state == "game_over":
            self.sc.fill(BLACK)
            text = font_manager.render("GAME OVER", 48, (255, 0, 0), shadow=BLACK)
            rect = text.get_rect(center=(self.sc.get_width() // 2, self.sc.get_height() // 2))
            self.sc.blit(text, rect)
        elif self.game_state == "paused":
            self.render_surface.fill(BLACK)
            for sprite in self.all_sprites.sprites():
                if self.is_sprite_in_active_zone(sprite):
                    self.render_surface.blit(sprite.image, self.camera.apply(sprite))
            scaled = pygame.transform.scale(
                self.render_surface, (self.sc.get_width(), self.sc.get_height())
            )
            self.sc.blit(scaled, (0, 0))
            self.pause_menu.draw(self.sc)
        elif self.game_state == "playing":
            self.render_surface.fill(BLACK)
            drawn = 0
            for sprite in self.all_sprites.sprites():
                if self.is_sprite_in_active_zone(sprite):
                    self.render_surface.blit(sprite.image, self.camera.apply(sprite))
                    drawn += 1
            self._draw_interact_hints()
            scaled = pygame.transform.scale(
                self.render_surface, (self.sc.get_width(), self.sc.get_height())
            )
            self.sc.blit(scaled, (0, 0))
            if not hasattr(self, "_debug_drawn") or drawn > 0:
                # print(f"[DEBUG] Drawn sprites: {drawn}")
                self._debug_drawn = True
            self.hud.draw(self.sc)

        if self.is_fading:
            self.fade_surface.set_alpha(int(self.fade_alpha))
            self.sc.blit(self.fade_surface, (0, 0))

        self.clock.tick(FPS)
        pygame.display.update()

    def _draw_interact_hints(self):
        if not hasattr(self, "player") or not self.player:
            return
        if not self.interactables:
            return

        player = self.player
        closest = None
        closest_dist = TILESIZE * 1.5
        for obj in self.interactables:
            dist = (
                           (obj.rect.centerx - player.rect.centerx) ** 2
                           + (obj.rect.centery - player.rect.centery) ** 2
                   ) ** 0.5
            if dist < closest_dist:
                closest_dist = dist
                closest = obj
        if not closest:
            return

        outline = closest.rect.copy()
        outline.inflate_ip(4, 4)
        screen_outline = self.camera.apply_rect(outline)
        pygame.draw.rect(self.render_surface, WHITE, screen_outline, 2)

        e_size = 20
        e_box = pygame.Rect(0, 0, e_size, e_size)
        e_box.centerx = closest.rect.centerx
        e_box.bottom = closest.rect.top - 8
        screen_e = self.camera.apply_rect(e_box)

        pygame.draw.rect(self.render_surface, BLACK, screen_e)
        pygame.draw.rect(self.render_surface, WHITE, screen_e, 1)

        text = font_manager.get_font(16).render("E", True, WHITE)
        text_rect = text.get_rect(center=screen_e.center)
        self.render_surface.blit(text, text_rect)

    def is_sprite_in_active_zone(self, sprite):
        if not hasattr(sprite, "rect"):
            return True
        if not hasattr(self, "current_zone"):
            return True

        if self.mode == GameMode.DUNGEON:
            map_w = getattr(self.dungeon_generator, "map_width", 100)
            map_h = getattr(self.dungeon_generator, "map_height", 100)
            sprite_tile_x = sprite.rect.x // TILESIZE
            sprite_tile_y = sprite.rect.y // TILESIZE
            return 0 <= sprite_tile_x < map_w and 0 <= sprite_tile_y < map_h
        else:
            sprite_tile_x = sprite.rect.x // TILESIZE
            sprite_tile_y = sprite.rect.y // TILESIZE

            return (
                    0 <= sprite_tile_x < WORLD_ZONE_WIDTH
                    and 0 <= sprite_tile_y < WORLD_ZONE_HEIGHT
            )

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

        # print(f"[DEBUG] check_zone_transition: player_tile=({player_tile_x}, {player_tile_y}), current_zone={self.current_zone}, zone_size=({zone_w}, {zone_h})")

        new_zone = None

        if player_tile_x < 1:
            new_zone = (self.current_zone[0] - 1, self.current_zone[1])
            # print(f"[DEBUG] Transition left to {new_zone}")
        elif player_tile_x >= zone_w - 2:
            new_zone = (self.current_zone[0] + 1, self.current_zone[1])
            # print(f"[DEBUG] Transition right to {new_zone}")
        elif player_tile_y < 1:
            new_zone = (self.current_zone[0], self.current_zone[1] - 1)
            # print(f"[DEBUG] Transition up to {new_zone}")
        elif player_tile_y >= zone_h - 2:
            new_zone = (self.current_zone[0], self.current_zone[1] + 1)
            # print(f"[DEBUG] Transition down to {new_zone}")

        if new_zone and -1 <= new_zone[0] <= 1 and -1 <= new_zone[1] <= 1:

            def do_transition():
                old_zone = self.current_zone
                old_tile_x = int(self.player.rect.x / TILESIZE)
                old_tile_y = int(self.player.rect.y / TILESIZE)

                self.current_zone = new_zone
                self.load_zone(new_zone[0], new_zone[1])

                spawn_x = 2
                spawn_y = 2
                if new_zone[0] > old_zone[0]:
                    spawn_x = 2
                    spawn_y = max(2, min(old_tile_y, zone_h - 3))
                elif new_zone[0] < old_zone[0]:
                    spawn_x = zone_w - 3
                    spawn_y = max(2, min(old_tile_y, zone_h - 3))
                elif new_zone[1] > old_zone[1]:
                    spawn_y = 2
                    spawn_x = max(2, min(old_tile_x, zone_w - 3))
                elif new_zone[1] < old_zone[1]:
                    spawn_y = zone_h - 3
                    spawn_x = max(2, min(old_tile_x, zone_w - 3))

                self.player.rect.x = spawn_x * TILESIZE
                self.player.rect.y = spawn_y * TILESIZE

                if self.camera_enabled and hasattr(self, "camera"):
                    self.camera.set_map_size(
                        (zone_w + 4) * TILESIZE, (zone_h + 4) * TILESIZE
                    )

                self.fade_in()

            self.fade_out(do_transition)

    def check_dungeon_transition(self):
        if self.mode != GameMode.DUNGEON:
            return

        if not hasattr(self, "player") or not hasattr(self, "doors"):
            return

        self._door_frame_counter += 1

        player_tile_x = int(self.player.rect.x / TILESIZE)
        player_tile_y = int(self.player.rect.y / TILESIZE)
        room_tile_width = self.dungeon_generator.room_tile_width
        room_tile_height = self.dungeon_generator.room_tile_height
        wall_thickness = self.dungeon_generator.wall_thickness
        room_unit_width = room_tile_width + wall_thickness * 2
        room_unit_height = room_tile_height + wall_thickness * 2

        player_room_x = player_tile_x // room_unit_width
        player_room_y = player_tile_y // room_unit_height
        player_room_coord = (player_room_x, player_room_y)

        if self._door_frame_counter % 2 == 0:
            if self._is_player_fully_inside_room():
                room = self.dungeon_generator.rooms.get(player_room_coord)
                if room and room.enemy_count == 0:
                    # print( f"[DEBUG] Spawning enemies in current room {player_room_coord}")
                    self.spawn_dungeon_enemies(player_room_coord)

        player_room = self.dungeon_generator.rooms.get(player_room_coord)
        if player_room and player_room.enemy_count > 0:
            return

        player_center = self.player.rect.center
        for door in self.doors:
            door_center = door.rect.center
            distance = (
                               (player_center[0] - door_center[0]) ** 2
                               + (player_center[1] - door_center[1]) ** 2
                       ) ** 0.5
            if distance < TILESIZE * 2:
                self.transition_to_room(door.to_room_coord, door.direction)
                break

    def _is_player_fully_inside_room(self):
        if not hasattr(self, "player") or not self.player:
            return False

        player_tile_x = int(self.player.rect.x / TILESIZE)
        player_tile_y = int(self.player.rect.y / TILESIZE)

        room_tile_width = self.dungeon_generator.room_tile_width
        room_tile_height = self.dungeon_generator.room_tile_height
        wall_thickness = self.dungeon_generator.wall_thickness
        room_unit_width = room_tile_width + wall_thickness * 2
        room_unit_height = room_tile_height + wall_thickness * 2

        player_room_x = player_tile_x // room_unit_width
        player_room_y = player_tile_y // room_unit_height
        room_coord = (player_room_x, player_room_y)

        room = self.dungeon_generator.rooms.get(room_coord)
        if not room:
            return False

        room_start_x = room_coord[0] * room_unit_width + wall_thickness
        room_start_y = room_coord[1] * room_unit_height + wall_thickness
        room_end_x = room_start_x + room_tile_width
        room_end_y = room_start_y + room_tile_height

        door_zone = 1

        is_inside = (
                player_tile_x >= room_start_x + door_zone
                and player_tile_x < room_end_x - door_zone
                and player_tile_y >= room_start_y + door_zone
                and player_tile_y < room_end_y - door_zone
        )
        return is_inside

    def transition_to_room(self, room_coord, direction):
        # print(f"[DEBUG] transition_to_room: {room_coord}, direction: {direction}")
        if room_coord not in self.dungeon_generator.rooms:
            # print(f"[DEBUG] Room {room_coord} not in dungeon_generator.rooms")
            return

        room = self.dungeon_generator.rooms[room_coord]

        if room.room_type.value == "boss":
            audio_manager.load_music("assets/sounds/Boss.mp3")
            audio_manager.play_music()

        self._show_room(room_coord)
        self._rebuild_visible_rooms()

        room_tile_width = self.dungeon_generator.room_tile_width
        room_tile_height = self.dungeon_generator.room_tile_height
        wall_thickness = self.dungeon_generator.wall_thickness
        room_unit_width = room_tile_width + wall_thickness * 2
        room_unit_height = room_tile_height + wall_thickness * 2

        # print(f"[DEBUG] Transitioned to room {room_coord}, player stays at {self.player.rect.x}, {self.player.rect.y}")

    def _show_room(self, room_coord):
        if room_coord not in self.dungeon_generator.rooms:
            return

        room = self.dungeon_generator.rooms[room_coord]
        room.set_visible(True)
        room.set_visited(True)

    def _rebuild_visible_rooms(self):
        if not hasattr(self, "_tile_map_cache"):
            self._tile_map_cache = self.dungeon_generator.generate_floor(
                self.current_dungeon_floor
            )
            self._dungeon_built_rooms = set()

        level = self._tile_map_cache

        room_tile_width = self.dungeon_generator.room_tile_width
        room_tile_height = self.dungeon_generator.room_tile_height
        wall_thickness = self.dungeon_generator.wall_thickness
        room_unit_width = room_tile_width + wall_thickness * 2
        room_unit_height = room_tile_height + wall_thickness * 2

        visible_count = 0
        for (gx, gy), room in self.dungeon_generator.rooms.items():
            if not room.visible:
                continue
            if (gx, gy) in self._dungeon_built_rooms:
                continue

            visible_count += 1
            self._dungeon_built_rooms.add((gx, gy))

            room_start_x = gx * room_unit_width
            room_start_y = gy * room_unit_height
            room_end_x = room_start_x + room_unit_width
            room_end_y = room_start_y + room_unit_height

            for i, row in enumerate(level):
                if i < room_start_y or i >= room_end_y:
                    continue
                for j, column in enumerate(row):
                    if j < room_start_x or j >= room_end_x:
                        continue
                    Ground(self, j, i)
                    if column == "B":
                        Block(self, j, i)
                    elif column == "T":
                        Decoration(self, j, i, "tree")
                    elif column == "C":
                        Chest(self, j, i)

            if room.room_type.value == "boss":
                boss_pos = self.dungeon_generator.get_boss_position()
                if boss_pos:
                    DungeonEntrance(self, boss_pos[0], boss_pos[1])

        # print(f"[DEBUG] _rebuild_visible_rooms: added {visible_count} new rooms, total built: {len(self._dungeon_built_rooms)}")

    def handle_camera_movement(self):
        pass

    def main(self):
        while self.running:
            time_delta = self.clock.tick(60) / 1000.0

            self.events()

            if self.game_state == "menu":
                self.main_menu.update(time_delta)
            elif self.game_state == "game_over":
                self.game_over_timer -= 1
                if self.game_over_timer <= 0:
                    self.game_state = "menu"
                    self.main_menu.show()
                    self.hud.hide()
                    audio_manager.load_music("assets/sounds/New_Menu_Music.mp3")
                    audio_manager.play_music()
            elif self.game_state == "paused":
                self.pause_menu.update(time_delta)
            elif self.game_state == "playing":
                self.update_fade()
                if not self.is_fading or self.fade_direction == -1:
                    self.check_zone_transition()
                    self.check_dungeon_transition()
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
