import asyncio
import json
import os
import random
import sys

import pygame
import pygame_gui
import pytmx

from core.ecs_world import World
from core.event_bus import EventBus
from core.events import ENEMY_KILLED
from core.services import ServiceContainer
from entity.boss import Boss
from entity.enemy import Enemy
from entity.factories.effect_factory import EffectFactory
from entity.player import Player
from entity.systems.animation_system import AnimationSystem
from entity.systems.area_damage_system import AreaDamageSystem
from entity.systems.block_collision_system import BlockCollisionSystem
from entity.systems.bullet_system import BulletSystem
from entity.systems.combat_system import CombatSystem
from entity.systems.entity_collision_system import EntityCollisionSystem
from entity.systems.hit_flash_system import HitFlashSystem
from entity.systems.knockback_system import KnockbackSystem
from entity.systems.lifetime_system import LifetimeSystem
from entity.systems.movement_system import MovementSystem
from items.weapon import Weapon
from managers.dungeon_manager import DungeonManager
from map.arena_generator import ArenaGenerator
from map.combat_room.enums import RoomCombatState
from map.combat_room.transition_system import CombatRoomTransitionSystem
from map.dungeon_data import DungeonData
from map.dungeon_generator import DungeonGenerator
from map.game_mode import GameMode
from map.tilemap import Block, Ground, DungeonEntrance, Water, NPC
from map.tmx_loader import TiledLoader
from map.world_generator import WorldGenerator
from sprites import Spritesheet
from ui.dungeon_map import DungeonMap
from ui.final_menu import FinalMenu
from ui.font_manager import FONTS
from ui.game_over import GameOverMenu
from ui.hud import HUD
from ui.menu import MainMenu
from ui.pause import PauseMenu
from ui.settings import SettingsMenu
from utils.camera import Camera
from utils.perspective import PerspectiveConfig, ShearScaleStrategy
from utils.physics import PhysicsEngine
from utils.settings import *


class Game:
    def __init__(self):
        self.clock = pygame.time.Clock()
        self.services = ServiceContainer()
        self.services.config.init()
        self.services.font.init(self.services.config.get_language(), self.services.config.get_font())
        self.services.audio.set_config(self.services.config)
        self.services.audio.sync_from_config()
        self.services.save.init()
        self.scale = self.services.config.get_scale()
        self.sc = self.create_window()
        self.clock = pygame.time.Clock()

        self.running = True
        self.enemy_collided = False
        self.block_collided = False

        self.mode = GameMode.WORLD
        self.current_zone = (0, 0)
        self.world_seed = None
        self.dungeon_seed = None
        self.world_generator = None
        self.dungeon_generator: DungeonData | None = None
        self.current_dungeon_floor = 1
        self._bosses_defeated: set[int] = set()
        self._run_enemies_killed = 0
        self._run_bosses_killed = 0
        self.total_coins = 0
        self._last_run_coins = 0
        self._last_run_enemies = 0
        self._last_run_bosses = 0
        self._dungeon_built_rooms = set()
        self.double_attack_unlocked = False
        self.cone_attack_unlocked = False
        self.pierce_unlocked = False
        self.explode_unlocked = False
        self.boomerang_unlocked = False
        self._door_frame_counter = 0
        self._pending_room_for_enemies = None
        self._sealed_rooms = {}
        self.dungeon_manager = None
        self._tile_map_cache = None

        self.fade_surface = pygame.Surface((1, 1))
        self.fade_alpha = 0
        self.is_fading = False
        self.fade_direction = 0
        self.fade_callback = None

        self.current_tmx_map = None

        self.game_state = "menu"
        self.ui_manager = None
        self.main_menu = None
        self.pause_menu = None
        self.settings_menu = None
        self.dungeon_map = None
        self.hud = None
        self.final_menu = None
        self._prev_game_state = None

        self.game_mode = "standard"
        self.arena_generator = None
        self.arena_map = None
        self.arena_rooms = None
        self.arena_spawn_timer = 0
        self.arena_max_enemies = 30

        self.physics = None
        self.physics_enabled = True

        self.camera = None
        self.camera_enabled = True

        self.audio_enabled = False
        self.audio = self.services.audio

        self.render_surface = None
        self.target_scale = self.scale
        self.current_scale = self.scale
        self.scale_speed = 0.1
        self.total_coins = self.services.save.total_coins

        initial_angle = self.services.config.get_perspective_angle()
        self.perspective_config = PerspectiveConfig(angle_deg=initial_angle)
        self.target_angle = initial_angle
        self.current_angle = initial_angle
        self.angle_speed = 0.1
        self.perspective_strategy = None

    async def async_init(self):
        self.terrain_spritesheet = Spritesheet("assets/blocs.png")
        self.player_spritesheet = Spritesheet(SPRITE_PLAYER["sheet"])
        self.enemy_spritesheets = {
            enemy_type: Spritesheet(cfg["sheet"])
            for enemy_type, cfg in ENEMY_TYPES.items()
        }
        self.weapon_spritesheet = Spritesheet("assets/sword.png")
        self.effects_spritesheet = Spritesheet("assets/effects.png")

        self.services.audio.init()
        self.services.audio.sync_from_config()
        pygame.key.set_repeat(200, 15)
        self.services.audio.load_sound("hit", "assets/sounds/Hit.ogg")
        self.services.audio.load_sound("swipe", "assets/sounds/Swipe.ogg")
        self.services.audio.load_sound("evade", "assets/sounds/Evade.ogg")
        self.services.audio.load_sound("pause", "assets/sounds/Pause.ogg")
        self.services.audio.load_sound("unpause", "assets/sounds/Unpause.ogg")
        self.services.audio.load_sound("menu_select", "assets/sounds/Menu Select.ogg")
        self.services.audio.load_sound("menu_move", "assets/sounds/Menu Move.ogg")
        self.services.audio.load_music("assets/sounds/Menu_beholder.ogg")
        self.services.audio.play_music(context="menu", volume_multiplier=2.0)
        print(f"[DEBUG] Audio initialized: {self.services.audio.initialized}")
        print(f"[DEBUG] Loaded sounds: {list(self.services.audio.sounds.keys())}")

        self.tmx_loader = TiledLoader(self)

    def create_window(self):
        mode = self.services.config.get_window_mode()
        display_index = self.services.config.get_display()

        try:
            screen_w, screen_h = self.services.config.get_display_resolution(display_index)
        except Exception:
            screen_w, screen_h = self.services.config.get_screen_size()
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
            width, height = self.services.config.get_window_size()
        else:
            width, height = screen_w, screen_h

        self.sc = pygame.display.set_mode((width, height), flags, display=display_index)
        self.render_surface = pygame.Surface(
            (int(width / self.scale), int(height / self.scale))
        )
        self.fade_surface = pygame.Surface((width, height))
        return self.sc

    def toggle_fullscreen(self):
        next_mode = self.services.config.get_next_window_mode()
        self.services.config.set_window_mode(next_mode)
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
        self._init_perspective()
        if hasattr(self, "ui_manager"):
            self.ui_manager = pygame_gui.UIManager(
                (self.sc.get_width(), self.sc.get_height())
            )

    def init_ui(self):
        self.ui_manager = pygame_gui.UIManager(self.sc.get_size())
        self.main_menu = MainMenu(self)
        self.pause_menu = PauseMenu(self)
        self.settings_menu = SettingsMenu(self)
        self.game_over_menu = GameOverMenu(self)
        self.final_menu = FinalMenu(self)
        self.dungeon_map = DungeonMap(self)
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
            self.world[(zone_x, zone_y)] = self.world_generator.get_zone_at(zone_x, zone_y)

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
                f"[DEBUG] Camera: pos=({self.camera.scroll_x}, {self.camera.scroll_y}), map_size=({self.camera.map_width}, {self.camera.map_height})")

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
        self._bosses_defeated.clear()
        self.dungeon_generator = DungeonGenerator(seed=self.dungeon_seed, placement="organic")
        self.dungeon_manager = DungeonManager(self)
        self.load_dungeon_floor()

    def load_dungeon_floor(self):
        if self.dungeon_map:
            self.dungeon_map.visible = False
        saved_coins = getattr(self.player, 'coins', 0) if hasattr(self, 'player') and self.player else 0
        self.clear_sprites()
        self._dungeon_built_rooms = set()
        self._sealed_rooms = {}
        self._transition_entries = set()

        level = self.dungeon_generator.generate_floor(self.current_dungeon_floor)
        self._tile_map_cache = level

        bg_music, _ = FLOOR_MUSIC_MAP.get(self.current_dungeon_floor,
                                          ("assets/sounds/Music.ogg", "assets/sounds/Boss.ogg"))
        self.services.audio.load_music(bg_music)
        mult = 1.5 if self.current_dungeon_floor == 3 else 1.0
        self.services.audio.play_music(context="dungeon", volume_multiplier=mult)

        self.dungeon_generator.set_start_room_visible()

        self._rebuild_visible_rooms()

        self.spawn_dungeon_enemies()

        start_x, start_y = self.dungeon_generator.get_start_position()
        # print(f"[DEBUG] Player spawn position: {start_x}, {start_y}, map_size: {self.dungeon_generator.map_width}x{self.dungeon_generator.map_height}")
        self.player = Player(self, start_x, start_y,
                             coins=saved_coins,
                             double_attack_unlocked=self.double_attack_unlocked,
                             cone_attack_unlocked=self.cone_attack_unlocked,
                             pierce_unlocked=self.pierce_unlocked,
                             explode_unlocked=self.explode_unlocked,
                             boomerang_unlocked=self.boomerang_unlocked)
        # print(f"[DEBUG] Player created at: {self.player.rect.x}, {self.player.rect.y}")

        if hasattr(self, "camera"):
            self.camera.set_map_size(self.dungeon_generator.map_width * TILESIZE,
                                     self.dungeon_generator.map_height * TILESIZE, )
            # print(f"[DEBUG] Camera map_size set to: {self.camera.map_width}x{self.camera.map_height}")
            self.camera.center_on(self.player.rect.x, self.player.rect.y)
            # print(f"[DEBUG] Camera centered: scroll={self.camera.scroll_x},{self.camera.scroll_y}")

    def _on_enemy_killed(self, entity) -> None:
        if isinstance(entity, Boss):
            self._run_bosses_killed += 1
            self._bosses_defeated.add(self.current_dungeon_floor)
            bg_music, _ = FLOOR_MUSIC_MAP.get(self.current_dungeon_floor,
                                              ("assets/sounds/Music.ogg", "assets/sounds/Boss.ogg"))
            self.services.audio.load_music(bg_music)
            mult = 1.5 if self.current_dungeon_floor == 3 else 1.0
            self.services.audio.play_music(context="dungeon", volume_multiplier=mult)
        else:
            self._run_enemies_killed += 1
        if hasattr(self, "dungeon_generator"):
            room_coord = entity._get_current_room_coord()
            room = self.dungeon_generator.rooms.get(room_coord)
            if room and room.enemy_count > 0:
                room.enemy_count -= 1

    def _on_enemy_killed_effects(self, entity) -> None:
        ecs_world = self.ecs_world
        cx, cy = entity.rect.centerx, entity.rect.centery
        EffectFactory.create_ecs_effect(ecs_world, cx, cy, "death", groups=[self.all_sprites])
        if hasattr(entity, "cfg"):
            for _ in range(20):
                EffectFactory.create_spark_particle(ecs_world, cx, cy, groups=[self.all_sprites])

    def _on_enemy_killed_physics(self, entity) -> None:
        if self.physics and hasattr(entity, "physics_name"):
            self.physics.remove_body(entity.physics_name)

    def spawn_dungeon_enemies(self, room_coord=None):
        if self.dungeon_manager:
            self.dungeon_manager.spawn_enemies(room_coord)

        # print(f"[DEBUG] Spawned {total_enemies} enemies")

    def _get_room_tile_bounds(self, room_coord):
        gx, gy = room_coord
        ruw = self.dungeon_generator.room_tile_width + self.dungeon_generator.wall_thickness * 2
        ruh = self.dungeon_generator.room_tile_height + self.dungeon_generator.wall_thickness * 2
        return gx * ruw, gy * ruh, gx * ruw + ruw, gy * ruh + ruh

    def _is_sprite_in_room_bounds(self, sprite, x1, y1, x2, y2):
        tx = int(sprite.rect.x / TILESIZE)
        ty = int(sprite.rect.y / TILESIZE)
        return x1 <= tx < x2 and y1 <= ty < y2

    def seal_room_for_battle(self, room_coord):
        if self.dungeon_manager:
            self.dungeon_manager.seal_room(room_coord)

    def unseal_room(self, room_coord):
        if self.dungeon_manager:
            self.dungeon_manager.unseal_room(room_coord)

    def exit_dungeon(self, go_deeper=False):
        if self.dungeon_map:
            self.dungeon_map.visible = False
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
        elif self.game_mode == "standard":
            self._last_run_coins = getattr(self.player, 'coins', 0) if hasattr(self, 'player') and self.player else 0
            self._last_run_enemies = self._run_enemies_killed
            self._last_run_bosses = self._run_bosses_killed
            self.total_coins += self._last_run_coins
            self.services.save.save_stats(self.total_coins)
            self.game_state = "final_menu"
            self.final_menu.show()
        else:
            self.exit_dungeon()

    def _reload_dungeon_floor(self):
        if self.dungeon_map:
            self.dungeon_map.visible = False
        saved_coins = getattr(self.player, 'coins', 0) if hasattr(self, 'player') and self.player else 0
        self.clear_sprites()
        self._dungeon_built_rooms = set()
        self._sealed_rooms = {}
        self._tile_map_cache = None
        bg_music, _ = FLOOR_MUSIC_MAP.get(self.current_dungeon_floor,
                                          ("assets/sounds/Music.ogg", "assets/sounds/Boss.ogg"))
        self.services.audio.load_music(bg_music)
        mult = 1.5 if self.current_dungeon_floor == 3 else 1.0
        self.services.audio.play_music(context="dungeon", volume_multiplier=mult)
        self._tile_map_cache = self.dungeon_generator.generate_floor(
            self.current_dungeon_floor
        )
        self.dungeon_generator.set_start_room_visible()
        self._rebuild_visible_rooms()
        self.spawn_dungeon_enemies()
        start_x, start_y = self.dungeon_generator.get_start_position()
        self.player = Player(self, start_x, start_y,
                             coins=saved_coins,
                             double_attack_unlocked=self.double_attack_unlocked,
                             cone_attack_unlocked=self.cone_attack_unlocked,
                             pierce_unlocked=self.pierce_unlocked,
                             explode_unlocked=self.explode_unlocked,
                             boomerang_unlocked=self.boomerang_unlocked)
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

        if self.ecs_world:
            self.ecs_world.clear()

    def create_tile_map(self):
        if self.game_mode == "arena":
            self.arena_generator = ArenaGenerator()
            self.arena_map, self.arena_rooms = self.arena_generator.generate()
            self._load_arena_level()
            return

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
        self.boss_spritesheets = {}

        if self.physics_enabled:
            self.init_physics_world()

        if self.camera_enabled:
            self.init_camera()

        self.ecs_world = World()
        self.event_bus = EventBus()
        self.ecs_world.add_service(self.event_bus)
        self.event_bus.on(ENEMY_KILLED, self._on_enemy_killed)
        self.event_bus.on(ENEMY_KILLED, self._on_enemy_killed_effects)
        self.event_bus.on(ENEMY_KILLED, self._on_enemy_killed_physics)
        EffectFactory.preload(self.effects_spritesheet)
        self.ecs_world.add_system(AnimationSystem(self.ecs_world))
        self.ecs_world.add_system(LifetimeSystem(self.ecs_world))
        self.ecs_world.add_system(MovementSystem(self.ecs_world))
        self.ecs_world.add_system(BulletSystem(self.ecs_world, get_player_fn=lambda: getattr(self, "player", None),
                                               all_sprites=self.all_sprites))
        self.ecs_world.add_system(AreaDamageSystem(self.ecs_world, lambda: getattr(self, "player", None)))
        self.ecs_world.add_system(CombatSystem(self.ecs_world))
        self.ecs_world.add_system(HitFlashSystem(self.ecs_world))
        self.ecs_world.add_system(BlockCollisionSystem(self.ecs_world, lambda: self.blocks))
        self.ecs_world.add_system(
            EntityCollisionSystem(self.ecs_world, lambda: self.blocks, all_sprites=self.all_sprites))
        self.ecs_world.add_system(KnockbackSystem(self.ecs_world))
        self.ecs_world.add_system(CombatRoomTransitionSystem(self.ecs_world, lambda: self.dungeon_manager))

        self.create_tile_map()

    def init_camera(self):
        map_w = WORLD_ZONE_WIDTH * TILESIZE if self.mode == GameMode.WORLD else 2000
        map_h = WORLD_ZONE_HEIGHT * TILESIZE if self.mode == GameMode.WORLD else 2000
        camera_w = self.render_surface.get_width()
        camera_h = self.render_surface.get_height()
        self.camera = Camera(self, camera_w, camera_h, map_w, map_h)
        self._init_perspective()

    def _init_perspective(self):
        if not self.render_surface:
            return
        w = self.render_surface.get_width()
        h = self.render_surface.get_height()
        self.perspective_strategy = ShearScaleStrategy(self.perspective_config, w, h)
        if self.camera:
            self.camera.set_perspective(self.perspective_strategy)

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

    def start_standard(self):
        self.game_state = "playing"
        self.game_mode = "standard"
        self.current_zone = (0, 0)
        self.current_dungeon_floor = 1
        self.world_seed = random.randint(0, 1000000)
        self.dungeon_seed = random.randint(0, 1000000)
        self.double_attack_unlocked = False
        self._run_enemies_killed = 0
        self._run_bosses_killed = 0
        self.cone_attack_unlocked = False
        self.pierce_unlocked = False
        self.explode_unlocked = False
        self.boomerang_unlocked = False
        self.player = None
        self.main_menu.hide()
        self.create()
        self.hud.show()

    def start_arena(self):
        self.game_state = "playing"
        self.game_mode = "arena"
        self.current_dungeon_floor = 0
        self.arena_spawn_timer = 0
        self._run_enemies_killed = 0
        self._run_bosses_killed = 0
        self.main_menu.hide()
        self.create()
        self.hud.show()

    def _load_arena_level(self):
        self.clear_sprites()
        level = self.arena_map

        for i, row in enumerate(level):
            for j, column in enumerate(row):
                if column == " ":
                    Ground(self, j, i)
                elif column == "B":
                    Ground(self, j, i)
                    Block(self, j, i)
                elif column == "P":
                    Ground(self, j, i)
                    self.player = Player(self, j, i)
                elif column == "E":
                    Ground(self, j, i)

        if hasattr(self, "camera"):
            self.camera.set_map_size(
                self.arena_generator.width * TILESIZE,
                self.arena_generator.height * TILESIZE,
            )
            self.camera.center_on(self.player.rect.x, self.player.rect.y)

    def _update_arena(self):
        if self.game_mode != "arena":
            return
        if not hasattr(self, "player") or not self.player:
            return
        if not self.arena_generator:
            return

        self.arena_spawn_timer += 1
        if self.arena_spawn_timer >= 120:
            self.arena_spawn_timer = 0
            current_enemy_count = len(self.enemies)
            if current_enemy_count < self.arena_max_enemies:
                to_spawn = min(3, self.arena_max_enemies - current_enemy_count)
                player_tile_x = int(self.player.rect.x // TILESIZE)
                player_tile_y = int(self.player.rect.y // TILESIZE)
                positions = self.arena_generator.get_enemy_spawn_positions(
                    self.arena_map, player_tile_x, player_tile_y,
                    min_distance=200, count=to_spawn,
                )
                for pos in positions:
                    Enemy(self, pos[0], pos[1])

    def _on_final_continue(self):
        self.final_menu.hide()
        self.start_arena()

    def load_game(self):
        if os.path.exists("savegame.json"):
            try:
                with open("savegame.json", "r") as f:
                    save_data = json.load(f)
                if not save_data.get("save_valid", False):
                    return False
                self.current_zone = tuple(save_data.get("zone", (0, 0)))
                self.current_dungeon_floor = save_data.get("floor", 1)
                self.world_seed = save_data.get(
                    "world_seed", random.randint(0, 1000000)
                )
                self.dungeon_seed = save_data.get(
                    "dungeon_seed", random.randint(0, 1000000)
                )
                self.game_mode = "standard"
                self.double_attack_unlocked = save_data.get("double_attack_unlocked", False)
                self.cone_attack_unlocked = save_data.get("cone_attack_unlocked", False)
                self.pierce_unlocked = save_data.get("pierce_unlocked", False)
                self.explode_unlocked = save_data.get("explode_unlocked", False)
                self.boomerang_unlocked = save_data.get("boomerang_unlocked", False)
                self.main_menu.hide()
                self.create()
                if hasattr(self, "player") and self.player:
                    self.player.coins = save_data.get("coins", 0)
                self.hud.show()
                self.game_state = "playing"
                return True
            except Exception as e:
                return False
        return False

    def _has_save_file(self):
        if not os.path.exists("savegame.json"):
            return False
        try:
            with open("savegame.json", "r") as f:
                save_data = json.load(f)
            return save_data.get("save_valid", False)
        except Exception:
            return False

    def clear_save(self):
        if os.path.exists("savegame.json"):
            try:
                os.remove("savegame.json")
            except Exception as e:
                print(f"Error removing save: {e}")

    def save_game(self):
        save_data = {
            "save_valid": True,
            "zone": self.current_zone,
            "floor": self.current_dungeon_floor,
            "mode": self.mode,
            "world_seed": self.world_seed,
            "dungeon_seed": self.dungeon_seed,
            "coins": getattr(self.player, "coins", 0) if hasattr(self, "player") and self.player else 0,
            "double_attack_unlocked": self.double_attack_unlocked,
            "cone_attack_unlocked": self.cone_attack_unlocked,
            "pierce_unlocked": self.pierce_unlocked,
            "explode_unlocked": self.explode_unlocked,
            "boomerang_unlocked": self.boomerang_unlocked,
        }
        try:
            with open("savegame.json", "w") as f:
                json.dump(save_data, f)
        except Exception as e:
            print(f"Error saving game: {e}")

    def game_over(self):
        self._last_run_coins = getattr(self.player, 'coins', 0) if hasattr(self, 'player') and self.player else 0
        self._last_run_enemies = self._run_enemies_killed
        self._last_run_bosses = self._run_bosses_killed
        self.total_coins += self._last_run_coins
        self.services.save.save_stats(self.total_coins)
        self.services.save.invalidate_save()

        if self.dungeon_map:
            self.dungeon_map.visible = False
        self.game_state = "game_over"
        self.game_over_menu.show()

    def open_settings(self):
        self.main_menu.reset_story()
        self._prev_game_state = self.game_state
        self.game_state = "settings"
        self.settings_menu.show()

    def settings_back(self):
        self.main_menu.reset_story()
        self.settings_menu.hide()
        self.game_state = self._prev_game_state
        self._prev_game_state = None

    def quit_game(self):
        self.running = False

    def return_to_menu(self):
        self.game_state = "menu"
        self.services.audio.load_music("assets/sounds/Menu_beholder.ogg")
        self.services.audio.play_music(context="menu", volume_multiplier=2.0)
        self.main_menu.show()
        self.hud.hide()

    def pause(self):
        if self.game_state == "playing":
            if self.dungeon_map:
                self.dungeon_map.visible = False
            self.game_state = "paused"
            self.pause_menu.show()
            self.services.audio.play_sound("pause")

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

    def update_perspective_angle(self):
        if not self.perspective_strategy:
            return
        if abs(self.current_angle - self.target_angle) > 0.05:
            self.current_angle += (
                                          self.target_angle - self.current_angle
                                  ) * self.angle_speed
            self.perspective_config.set_angle(self.current_angle)
            self.perspective_strategy.sync_config()
        elif self.current_angle != self.target_angle:
            self.current_angle = self.target_angle
            self.perspective_config.set_angle(self.current_angle)
            self.perspective_strategy.sync_config()

    def update(self):
        self.update_scale()
        self.update_perspective_angle()
        self.all_sprites.update()

        if self.ecs_world:
            self.ecs_world.update(1.0 / 60.0)
            EffectFactory.update(self.ecs_world)

        pygame.display.set_caption(f'{self.clock.get_fps() : .1f}')

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

        if self.game_mode == "arena":
            self._update_arena()

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.game_state == "playing":
                        self.pause()
                    elif self.game_state == "paused":
                        self.resume()
                    elif self.game_state == "settings":
                        self.settings_back()
                    else:
                        self.running = False
                elif event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                elif event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:
                    self.target_angle = max(-360, min(360, self.target_angle - 5))
                    self.services.config.set_perspective_angle(self.target_angle)
                elif event.key == pygame.K_EQUALS or event.key == pygame.K_KP_PLUS:
                    self.target_angle = max(-360, min(360, self.target_angle + 5))
                    self.services.config.set_perspective_angle(self.target_angle)
                elif event.key == pygame.K_e:
                    if self.game_state == "playing" and hasattr(self, "player"):
                        self.player.interact()
                elif event.key == pygame.K_o:
                    current = self.services.font.get_locale()
                    supported = self.services.font.get_supported_locales()
                    if current in supported:
                        idx = supported.index(current)
                        new_locale = supported[(idx + 1) % len(supported)]
                    else:
                        new_locale = supported[0] if supported else "en"
                    self.services.font.set_locale(new_locale)
                    self.services.audio.play_sound("menu_select")
                    if self.game_state == "menu" and self.main_menu:
                        self.main_menu.update_texts()
                    elif self.game_state == "paused" and self.pause_menu:
                        self.pause_menu.update_texts()
                    elif self.game_state == "playing" and self.hud:
                        self.hud.update_texts()
                elif event.key == pygame.K_p:
                    current_font_key = self.services.font.get_font_key()
                    if current_font_key.isdigit():
                        current_idx = int(current_font_key)
                        new_idx = (current_idx + 1) % len(FONTS)
                    else:
                        new_idx = 0
                    self.services.font.set_font(str(new_idx))
                    self.services.audio.play_sound("menu_select")
                    if self.game_state == "menu" and self.main_menu:
                        self.main_menu.update_texts()
                    elif self.game_state == "paused" and self.pause_menu:
                        self.pause_menu.update_texts()
                    elif self.game_state == "playing" and self.hud:
                        self.hud.update_texts()
                elif event.key == pygame.K_m:
                    if self.game_state == "playing" and self.dungeon_map:
                        self.dungeon_map.toggle()

            if event.type == pygame.VIDEORESIZE:
                if self.services.config.get_window_mode() == "windowed":
                    self.services.config.set_window_size(event.w, event.h)
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
                self.services.config.set_scale(self.target_scale)

            if self.game_state == "menu":
                self.main_menu.handle_event(event)
            elif self.game_state == "paused":
                self.pause_menu.handle_event(event)
            elif self.game_state == "settings":
                self.settings_menu.handle_event(event)
            elif self.game_state == "game_over":
                self.game_over_menu.handle_event(event)
            elif self.game_state == "final_menu":
                self.final_menu.handle_event(event)

    def _draw_sprites(self, surface):
        center_x = surface.get_width() / 2
        perspective = self.perspective_strategy
        camera = self.camera
        scroll_x = camera.scroll_x
        scroll_y = camera.scroll_y

        visible = []
        for sprite in self.all_sprites.sprites():
            if not self.is_sprite_in_active_zone(sprite):
                continue
            cx = sprite.rect.x - scroll_x
            cy = sprite.rect.y - scroll_y

            if perspective:
                sx, sy, scale = perspective.transform_point(cx, cy, center_x)
            else:
                sx, sy, scale = cx, cy, 1.0

            visible.append((sprite, cx, cy, sx, sy, scale))

        visible.sort(key=lambda item: (item[0]._layer, item[4]))

        sw, sh = surface.get_width(), surface.get_height()
        for sprite, cx, cy, sx, sy, scale in visible:
            if not (-128 < sx < sw + 128 and -128 < sy < sh + 128):
                continue

            if perspective and getattr(sprite, 'render_mode', 'orthogonal') == 'perspective':
                img, dx, dy = perspective.transform_image(sprite.image, cx, cy, center_x)
            else:
                img, dx, dy = sprite.image, 0, 0
            surface.blit(img, (int(sx) + dx, int(sy) + dy))

    def _draw_game_frame(self):
        self.render_surface.fill(BLACK)
        self._draw_sprites(self.render_surface)

        if self.game_state == "playing":
            self._draw_interact_hints()

        scaled = pygame.transform.scale(
            self.render_surface, (self.sc.get_width(), self.sc.get_height())
        )
        self.sc.blit(scaled, (0, 0))

    def draw(self):
        if self.game_state == "menu":
            self.sc.fill(BLACK)
            self.main_menu.draw(self.sc)
        elif self.game_state == "settings":
            self.sc.fill(BLACK)
            self.settings_menu.draw(self.sc)
        elif self.game_state == "game_over":
            self._draw_game_frame()
            self.game_over_menu.draw(self.sc)
        elif self.game_state == "paused":
            self._draw_game_frame()
            self.pause_menu.draw(self.sc)
        elif self.game_state == "final_menu":
            self._draw_game_frame()
            self.final_menu.draw(self.sc)
        elif self.game_state == "playing":
            self._draw_game_frame()
            if self.hud:
                self.hud.draw(self.sc)

            if hasattr(self, "_debug_show_zones") and self._debug_show_zones:
                self._draw_transition_zones()

        if self.dungeon_map and hasattr(self.dungeon_map, 'draw'):
            self.dungeon_map.draw(self.sc)

        if self.is_fading:
            self.fade_surface.set_alpha(int(self.fade_alpha))
            self.sc.blit(self.fade_surface, (0, 0))

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

        center_x = self.render_surface.get_width() / 2
        perspective = self.perspective_strategy
        scroll_x = self.camera.scroll_x
        scroll_y = self.camera.scroll_y

        hint_rect = closest.visual_rect if hasattr(closest, "visual_rect") else closest.rect

        outline = hint_rect.copy()
        outline.inflate_ip(4, 4)
        if perspective:
            cx = outline.centerx - scroll_x
            cy = outline.centery - scroll_y
            sx, sy, scale = perspective.transform_point(cx, cy, center_x)
            scaled_w = int(outline.width * scale)
            scaled_h = int(outline.height * scale)
            screen_outline = pygame.Rect(int(sx - scaled_w / 2), int(sy - scaled_h / 2), scaled_w, scaled_h)
        else:
            screen_outline = self.camera.apply_rect(outline)
        pygame.draw.rect(self.render_surface, WHITE, screen_outline, 2)

        e_size = 20
        e_box = pygame.Rect(0, 0, e_size, e_size)
        e_box.centerx = hint_rect.centerx
        e_box.bottom = hint_rect.top - 8
        if perspective:
            cx = e_box.centerx - scroll_x
            cy = e_box.centery - scroll_y
            sx, sy, _ = perspective.transform_point(cx, cy, center_x)
            screen_e = pygame.Rect(int(sx - e_size / 2), int(sy - e_size / 2), e_size, e_size)
        else:
            screen_e = self.camera.apply_rect(e_box)

        pygame.draw.rect(self.render_surface, BLACK, screen_e)
        pygame.draw.rect(self.render_surface, WHITE, screen_e, 1)

        text = self.services.font.get_font(16).render("E", True, WHITE)
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

        for sealed_coord in list(self._sealed_rooms.keys()):
            room = self.dungeon_generator.rooms.get(sealed_coord)
            if room and room.enemy_count == 0:
                tr = self.dungeon_manager.get_transition(sealed_coord)
                if tr and tr.state in (
                        RoomCombatState.CLEARING_COMBAT, RoomCombatState.RECOVERED,
                ):
                    continue
                self.dungeon_manager.start_room_clear(sealed_coord)

        player_tile_x = int(self.player.hitbox.centerx / TILESIZE)
        player_tile_y = int(self.player.hitbox.centery / TILESIZE)
        room_tile_width = self.dungeon_generator.room_tile_width
        room_tile_height = self.dungeon_generator.room_tile_height
        wall_thickness = self.dungeon_generator.wall_thickness
        room_unit_width = room_tile_width + wall_thickness * 2
        room_unit_height = room_tile_height + wall_thickness * 2

        player_room_x = player_tile_x // room_unit_width
        player_room_y = player_tile_y // room_unit_height
        player_room_coord = (player_room_x, player_room_y)

        dg = self.dungeon_generator
        player_room = dg.rooms.get(player_room_coord)

        if player_room and player_room.enemy_count > 0:
            return

        # ---- Entry trigger: player at door threshold of current room ----
        if player_room:
            local_x = player_tile_x - player_room_x * room_unit_width
            local_y = player_tile_y - player_room_y * room_unit_height

            for direction, has_door in player_room.doors.items():
                if not has_door:
                    continue
                neighbor = None
                if direction == "east":
                    neighbor = (player_room_x + 1, player_room_y)
                elif direction == "west":
                    neighbor = (player_room_x - 1, player_room_y)
                elif direction == "south":
                    neighbor = (player_room_x, player_room_y + 1)
                elif direction == "north":
                    neighbor = (player_room_x, player_room_y - 1)
                if neighbor is None or neighbor not in dg.rooms:
                    continue

                entered = False
                if direction == "east":
                    entered = local_x == 16
                elif direction == "west":
                    entered = local_x == 1
                elif direction == "south":
                    entered = local_y == 16
                elif direction == "north":
                    entered = local_y == 1

                if entered:
                    if (neighbor, direction) not in self._transition_entries:
                        self._transition_entries.add((neighbor, direction))
                        self.transition_to_room(neighbor, direction)

        # ---- Completion trigger: player 2+ tiles into a pending room ----
        for entry in list(self._transition_entries):
            entry_room, entry_dir = entry
            if player_room_coord != entry_room:
                continue

            local_x = player_tile_x - entry_room[0] * room_unit_width
            local_y = player_tile_y - entry_room[1] * room_unit_height

            completed = False
            if entry_dir in ("east", "south"):
                coord = local_x if entry_dir == "east" else local_y
                completed = coord >= 2
            else:
                coord = local_x if entry_dir == "west" else local_y
                completed = coord <= room_tile_width - 3

            if completed:
                self._transition_entries.discard(entry)
                room = dg.rooms.get(entry_room)
                if room and room.enemy_count == 0:
                    self.spawn_dungeon_enemies(entry_room)

    def _draw_transition_zones(self):
        if self.mode != GameMode.DUNGEON or not hasattr(self, 'dungeon_generator'):
            return
        dg = self.dungeon_generator
        rw = dg.room_tile_width + dg.wall_thickness * 2
        rh = dg.room_tile_height + dg.wall_thickness * 2

        for (gx, gy), room in dg.rooms.items():
            if not room.visible:
                continue
            for direction, has_door in room.doors.items():
                if not has_door:
                    continue
                color = (0, 255, 0, 80)
                nx, ny = gx, gy
                if direction == "east":
                    x = gx * rw + 16
                    y = gy * rh
                    w, h = 1, rh
                    nx = gx + 1
                elif direction == "west":
                    x = gx * rw + 1
                    y = gy * rh
                    w, h = 1, rh
                    nx = gx - 1
                elif direction == "south":
                    x = gx * rw
                    y = gy * rh + 16
                    w, h = rw, 1
                    ny = gy + 1
                elif direction == "north":
                    x = gx * rw
                    y = gy * rh + 1
                    w, h = rw, 1
                    ny = gy - 1
                else:
                    continue

                entry_rect = pygame.Rect(x * TILESIZE, y * TILESIZE, w * TILESIZE, h * TILESIZE)
                entry_rect = self.camera.apply_to_rect(entry_rect)
                pygame.draw.rect(self.sc, color, entry_rect, 2)

                nx, ny = nx, ny
                if (nx, ny) in dg.rooms and dg.rooms[(nx, ny)].visible:
                    comp_x = nx * rw
                    comp_y = ny * rh
                    color2 = (255, 255, 0, 80)
                    if direction in ("east", "west"):
                        cx = comp_x + 2 if direction == "east" else comp_x + rw - 3
                        comp_rect = pygame.Rect(cx * TILESIZE, comp_y * TILESIZE, 1 * TILESIZE, rh * TILESIZE)
                    else:
                        cy = comp_y + 2 if direction == "south" else comp_y + rh - 3
                        comp_rect = pygame.Rect(comp_x * TILESIZE, cy * TILESIZE, rw * TILESIZE, 1 * TILESIZE)
                    comp_rect = self.camera.apply_to_rect(comp_rect)
                    pygame.draw.rect(self.sc, color2, comp_rect, 2)

    def _is_player_fully_inside_room(self):
        if self.dungeon_manager:
            return self.dungeon_manager.is_player_fully_inside_room()
        return False

    def transition_to_room(self, room_coord, direction):
        if self.dungeon_manager:
            self.dungeon_manager.transition_to_room(room_coord, direction)

    def _show_room(self, room_coord):
        if self.dungeon_manager:
            self.dungeon_manager.show_room(room_coord)

    def _rebuild_visible_rooms(self):
        if self.dungeon_manager:
            self.dungeon_manager.rebuild_visible_rooms()

    def handle_camera_movement(self):
        pass

    async def run_frame(self):
        time_delta = self.clock.tick(60) / 1000.0
        self.events()
        await self._update(time_delta)
        self.draw()

    async def _update(self, dt):
        if self.game_state == "menu":
            self.main_menu.update(dt)
        elif self.game_state == "settings":
            self.settings_menu.update(dt)
        elif self.game_state == "game_over":
            self.game_over_menu.update(dt)
        elif self.game_state == "paused":
            self.pause_menu.update(dt)
        elif self.game_state == "final_menu":
            self.final_menu.update(dt)
        elif self.game_state == "playing":
            self.update_fade()
            if not self.is_fading or self.fade_direction == -1:
                if self.game_mode != "arena":
                    self.check_zone_transition()
                    self.check_dungeon_transition()
                self.handle_camera_movement()
                self.update()
            if self.camera:
                self.camera.follow_sprite(self.player)
                self.camera.update(1.0 / 60.0)
            self.hud.update(dt)

    async def _game_loop(self):
        while self.running:
            await self.run_frame()
            await asyncio.sleep(0)


async def main_game_loop():
    pygame.init()
    game = Game()
    await game.async_init()
    game.init_ui()

    async with asyncio.TaskGroup() as tg:
        tg.create_task(game._game_loop())

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    asyncio.run(main_game_loop())
