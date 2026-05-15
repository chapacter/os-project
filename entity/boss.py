import math
import random

import pygame

from effects.effect import Effect
from effects.particle import AreaDamageParticle
from effects.particle import Particle
from entity.base import Healthbar, VectorEntity
from entity.enemy import Enemy
from projectiles.bullet import Enemy_Bullet
from sprites import Spritesheet
from utils.audio import audio_manager
from utils.physics import COLLISION_ENTITY
from utils.settings import *


class BossAI:
    CHASE = "chase"
    MELEE = "melee"
    AREA = "area_damage"
    TELEPORT = "teleport"
    SUMMON = "summon"
    RANGED = "ranged"
    WAIT = "wait"


class BossHealthbar(Healthbar):
    def __init__(self, game, x, y, boss):
        self.boss = boss
        self.width = 80
        self.height = 12
        self._layer = HEALTH_LAYER - 1
        self.groups = game.all_sprites, game.healthbar
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * TILESIZE
        self.y = y * TILESIZE

        self.image = pygame.Surface([self.width, self.height])
        self.rect = self.image.get_rect()
        self.rect.x = self.x - 20
        self.rect.y = self.y - TILESIZE - 10

    def move(self):
        self.rect.x = self.boss.rect.centerx - 40
        self.rect.y = self.boss.rect.top - 20

    def damage(self, total_health, health):
        self.image.fill((40, 0, 0))

        hp_percent = health / total_health
        current_width = self.width * hp_percent

        if hp_percent > BOSS_CONFIG["phase_thresholds"][0]:
            color = (0, 200, 0)
        elif hp_percent > BOSS_CONFIG["phase_thresholds"][1]:
            color = (200, 200, 0)
        else:
            color = (200, 0, 0)

        pygame.draw.rect(self.image, color, (0, 0, current_width, self.height), 0)

        pygame.draw.rect(self.image, (80, 80, 80), (0, 0, self.width, self.height), 1)

    def kill_bar(self):
        self.kill()


class Boss(VectorEntity, pygame.sprite.Sprite):
    def __init__(self, game, x, y, floor=1):
        self.game = game
        self._layer = PLAYER_LAYER - 1
        self.groups = game.all_sprites, game.enemies
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.floor = floor
        self.cfg = BOSS_CONFIG
        self.boss_cfg = FLOOR_BOSS_CONFIG[floor]
        self.attack_speed_mult = self.boss_cfg["attack_speed_mult"]
        self.summon_types = self.boss_cfg["summon_enemy_types"]

        self.x = x * TILESIZE
        self.y = y * TILESIZE

        self.width = self.cfg["sprite_size"][0]
        self.height = self.cfg["sprite_size"][1]

        if floor not in game.boss_spritesheets:
            game.boss_spritesheets[floor] = Spritesheet(self.boss_cfg["sheet"])
        spritesheet = game.boss_spritesheets[floor]
        sprite_w, sprite_h = self.boss_cfg["frame_size"]

        self.frame_move = self.boss_cfg["frame_move"]
        self.animation_counter = 0
        self.animations = {}
        direction_map = self.boss_cfg["direction_map"]

        for direction, row in direction_map.items():
            frames = []
            for col in range(self.frame_move):
                sprite = spritesheet.get_image(col * sprite_w, row * sprite_h, sprite_w, sprite_h)
                scaled = pygame.transform.scale(sprite, (self.width, self.height))
                frames.append(scaled)
            self.animations[direction] = frames

        self.image = self.animations["down"][0]
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

        self.hitbox = pygame.Rect(0, 0, self.cfg["hitbox_size"], self.cfg["hitbox_size"])
        self.hitbox.center = self.rect.center

        self.max_health = self.cfg["hp"]
        self.health = self.max_health
        self.current_phase = 1

        self.healthbar = BossHealthbar(game, x, y, self)

        self.ai_state = BossAI.CHASE
        self.state_timer = 0
        self.state_duration = 60

        self.teleport_timer = 0
        self.attack_timer = 0
        self.summon_timer = 0
        self.phase_transition_timer = 0
        self.melee_timer = 0
        self.area_timer = 0
        self.ranged_timer = 0

        self.previous_direction = "down"
        self.animation_counter = 0

        self._pos_x = float(self.rect.x)
        self._pos_y = float(self.rect.y)

        self.minions = pygame.sprite.Group()

        self.in_transition = False
        self.transition_effect_timer = 0

        self.phase_color_overlays = {
            1: None,
            2: pygame.Color(255, 100, 100),
            3: pygame.Color(255, 0, 0),
        }

        Effect(self.game, self.rect.centerx, self.rect.centery, "death")

        self.physics_name = f"boss_{id(self)}"
        VectorEntity.__init__(
            self, self.game, self.physics_name, collision_type=COLLISION_ENTITY, max_health=self.max_health
        )

        if self.body:
            game.physics.remove_body(self.physics_name)
        self.body, self.shape = game.physics.add_entity_body(
            self.rect.x,
            self.rect.y,
            self.hitbox.width,
            self.hitbox.height,
            name=self.physics_name,
        )

    def get_phase(self):
        hp_percent = self.health / self.max_health
        if hp_percent > self.cfg["phase_thresholds"][0]:
            return 1
        elif hp_percent > self.cfg["phase_thresholds"][1]:
            return 2
        return 3

    def _get_distance_to_player(self):
        if not self.game.player:
            return float("inf")
        dx = self.game.player.rect.centerx - self.rect.centerx
        dy = self.game.player.rect.centery - self.rect.centery
        return (dx ** 2 + dy ** 2) ** 0.5

    def _get_direction_to_player(self):
        if not self.game.player:
            return self.previous_direction
        dx = self.game.player.rect.centerx - self.rect.centerx
        dy = self.game.player.rect.centery - self.rect.centery
        if abs(dx) > abs(dy):
            return "right" if dx > 0 else "left"
        return "down" if dy > 0 else "up"

    def _get_room_bounds(self):
        room_tile_width = self.game.dungeon_generator.room_tile_width
        room_tile_height = self.game.dungeon_generator.room_tile_height
        wall_thickness = self.game.dungeon_generator.wall_thickness
        room_unit_width = room_tile_width + wall_thickness * 2
        room_unit_height = room_tile_height + wall_thickness * 2

        tile_x = int(self.rect.x / TILESIZE)
        tile_y = int(self.rect.y / TILESIZE)
        room_x = tile_x // room_unit_width
        room_y = tile_y // room_unit_height

        min_x = room_x * room_unit_width + wall_thickness + 2
        min_y = room_y * room_unit_height + wall_thickness + 2
        max_x = min_x + room_tile_width - 4
        max_y = min_y + room_tile_height - 4

        return min_x, min_y, max_x, max_y

    def _get_phase_config(self):
        return self.cfg[f"phase{self.current_phase}"]

    def _chase(self):
        if not self.game.player:
            return
        dx = self.game.player.rect.centerx - self.rect.centerx
        dy = self.game.player.rect.centery - self.rect.centery
        vec = pygame.math.Vector2(dx, dy)
        if vec.length() > 0:
            vec = vec.normalize()
        speed = self._get_phase_config()["speed"]
        self.velocity = vec * speed
        self.previous_direction = self.get_direction_from_velocity()

    def _melee_attack(self):
        if not self.game.player:
            return
        if self.melee_timer > 0:
            return
        dist = self._get_distance_to_player()
        if dist < self.cfg["hitbox_size"] + 20:
            self.game.player.damage(self.cfg["damage"])
            self.melee_timer = int(60 / self.attack_speed_mult)

    def _teleport(self):
        if not self.game.player:
            return
        player = self.game.player
        angle = random.uniform(0, 360)
        distance = random.randint(100, 150)
        offset_x = math.cos(math.radians(angle)) * distance
        offset_y = math.sin(math.radians(angle)) * distance

        new_x = player.rect.centerx + offset_x - self.hitbox.width // 2
        new_y = player.rect.centery + offset_y - self.hitbox.height // 2

        min_x, min_y, max_x, max_y = self._get_room_bounds()
        min_pixel_x = min_x * TILESIZE
        max_pixel_x = max_x * TILESIZE
        min_pixel_y = min_y * TILESIZE
        max_pixel_y = max_y * TILESIZE

        new_x = max(min_pixel_x, min(max_pixel_x, new_x))
        new_y = max(min_pixel_y, min(max_pixel_y, new_y))

        Effect(self.game, self.rect.centerx, self.rect.centery, "death")
        self._pos_x = float(new_x)
        self._pos_y = float(new_y)
        self.rect.x = int(self._pos_x)
        self.rect.y = int(self._pos_y)
        self.hitbox.center = self.rect.center
        Effect(self.game, self.rect.centerx, self.rect.centery, "death")

    def _area_damage(self):
        config = self._get_phase_config()
        radius = config["area_radius"]
        particle_count = config.get("area_particle_count", 16)
        damage_per_hit = 0.1

        for i in range(particle_count):
            angle = (i / particle_count) * 360
            x = self.rect.centerx + math.cos(math.radians(angle)) * radius * 0.7
            y = self.rect.centery + math.sin(math.radians(angle)) * radius * 0.7
            AreaDamageParticle(self.game, x, y, damage_per_hit)

    def _ranged_attack(self):
        if not self.game.player:
            return
        player = self.game.player
        start_x = self.hitbox.centerx
        start_y = self.hitbox.centery
        target_x = player.hitbox.centerx + random.randint(-20, 20)
        target_y = player.hitbox.centery + random.randint(-20, 20)

        dx = target_x - start_x
        dy = target_y - start_y
        base_angle = math.atan2(dy, dx)

        bullets_per_row = [4, 4, 4, 4]
        row_offsets = [0, 15, 30, 45]

        for row_idx, count in enumerate(bullets_per_row):
            row_angle = base_angle + math.radians(row_offsets[row_idx])
            for j in range(count):
                offset = (j - (count - 1) / 2) * math.radians(12)
                angle = row_angle + offset
                end_x = start_x + math.cos(angle) * 500
                end_y = start_y + math.sin(angle) * 500
                Enemy_Bullet(self.game, start_x, start_y, end_x, end_y)

    def _summon(self):
        config = self._get_phase_config()
        count = config.get("summon_count", 5)
        min_x, min_y, max_x, max_y = self._get_room_bounds()

        for _ in range(count):
            spawn_x = random.randint(min_x, max_x)
            spawn_y = random.randint(min_y, max_y)
            minion = Enemy(self.game, spawn_x, spawn_y, enemy_type=random.choice(self.summon_types))
            self.minions.add(minion)

    def _summon_on_phase_change(self):
        min_x, min_y, max_x, max_y = self._get_room_bounds()
        available_types = self.summon_types
        num_to_spawn = random.randint(3, 5)
        selected_types = random.sample(available_types, min(num_to_spawn, len(available_types)))

        for enemy_type in selected_types:
            spawn_x = random.randint(min_x, max_x)
            spawn_y = random.randint(min_y, max_y)
            minion = Enemy(self.game, spawn_x, spawn_y, enemy_type=enemy_type)
            self.minions.add(minion)

    def _handle_phase_transition(self):
        if self.in_transition:
            self.transition_effect_timer -= 1
            if self.transition_effect_timer <= 0:
                self.in_transition = False
            return

        new_phase = self.get_phase()
        if new_phase != self.current_phase:
            self.current_phase = new_phase
            self.in_transition = True
            self.transition_effect_timer = 30

            color = self.phase_color_overlays[self.current_phase]
            if color:
                scaled = pygame.transform.scale(
                    self.image, (self.width + 10, self.height + 10)
                )
                self.image = scaled
                self.rect = self.image.get_rect(center=self.rect.center)

            Effect(self.game, self.rect.centerx, self.rect.centery, "death")

            for _ in range(10):
                Particle(self.game, self.rect.centerx, self.rect.centery)

            if new_phase == 3:
                self._summon_on_phase_change()

    def move(self):
        if self.get_phase() != self.current_phase:
            self._handle_phase_transition()

        if self.state_timer > 0:
            self.state_timer -= 1

        if self.melee_timer > 0:
            self.melee_timer -= 1

        config = self._get_phase_config()
        attacks = config["attacks"]
        player_dist = self._get_distance_to_player()

        self.teleport_timer += 1
        self.area_timer += 1
        self.ranged_timer += 1
        self.summon_timer += 1

        teleport_interval = int(config.get("teleport_interval", 300) / self.attack_speed_mult)
        area_cooldown = int(config.get("area_cooldown", 180) / self.attack_speed_mult)
        ranged_cooldown = int(config.get("ranged_cooldown", 240) / self.attack_speed_mult)
        summon_cooldown = int(config.get("summon_cooldown", 420) / self.attack_speed_mult)
        max_minions = config.get("summon_count", 5)

        attack_performed = False

        if "area_damage" in attacks and self.area_timer >= area_cooldown:
            self._area_damage()
            self.area_timer = 0
            attack_performed = True

        if "ranged" in attacks and self.ranged_timer >= ranged_cooldown:
            self._ranged_attack()
            self.ranged_timer = 0
            attack_performed = True

        if "teleport" in attacks and self.teleport_timer >= teleport_interval:
            self._teleport()
            self.teleport_timer = 0
            attack_performed = True

        if "summon" in attacks and self.summon_timer >= summon_cooldown:
            if len(self.minions) < max_minions:
                self._summon()
                self.summon_timer = 0
                attack_performed = True

        if player_dist < self.cfg["hitbox_size"] + 20:
            self.ai_state = BossAI.MELEE
            self.state_duration = 30
            self._melee_attack()
        elif player_dist < 200:
            self.ai_state = BossAI.CHASE
            self._chase()
        else:
            self.ai_state = BossAI.CHASE
            self._chase()

    def animation(self):
        anim_dir = (
            self.get_direction_from_velocity()
            if self.velocity.length() > 0
            else self.previous_direction
        )

        if self.velocity.length() == 0:
            self.image = self.animations[anim_dir][0]
        else:
            frame_index = int(self.animation_counter) % self.frame_move
            self.image = self.animations[anim_dir][frame_index]
            self.animation_counter += 0.2
            if self.animation_counter >= self.frame_move:
                self.animation_counter = 0

        self.rect = self.image.get_rect(center=self.rect.center)

        if self.current_phase > 1:
            color = self.phase_color_overlays[self.current_phase]
            if color:
                tinted = self.image.copy()
                tinted.fill(color, special_flags=pygame.BLEND_RGB_MULT)
                self.image = tinted

    def apply_movement(self):
        if self.knockback_velocity.length() > 0:
            self._pos_x += self.knockback_velocity.x
            self.hitbox.x = int(self._pos_x)
            self._resolve_collision_x("knockback_velocity")
            self._pos_y += self.knockback_velocity.y
            self.hitbox.y = int(self._pos_y)
            self._resolve_collision_y("knockback_velocity")
            self.knockback_velocity *= ENEMY_KNOCKBACK_DECAY
            if self.knockback_velocity.length() < 0.1:
                self.knockback_velocity = pygame.math.Vector2(0, 0)

        self._pos_x += self.velocity.x
        self.hitbox.x = int(self._pos_x)
        self._resolve_collision_x("velocity")
        self._pos_y += self.velocity.y
        self.hitbox.y = int(self._pos_y)
        self._resolve_collision_y("velocity")

        self.rect.center = self.hitbox.center
        self.sync_physics()

    def update(self):
        self.move()
        self.animation()

        self.apply_hit_effect()

        self.apply_movement()

        self.collide_player()

        if self.healthbar:
            self.healthbar.move()
            self.healthbar.damage(self.max_health, self.health)

    def collide_player(self):
        pass

    def damage(self, amount):
        super().damage(amount)
        if self.healthbar:
            self.healthbar.damage(self.max_health, self.health)

    def _on_death(self):
        Effect(self.game, self.rect.centerx, self.rect.centery, "death")
        for _ in range(20):
            Particle(self.game, self.rect.centerx, self.rect.centery)
        if self.healthbar:
            self.healthbar.kill_bar()
        self.kill()
        if self.game.physics and hasattr(self, "physics_name"):
            self.game.physics.remove_body(self.physics_name)

        audio_manager.load_music("assets/sounds/Music.mp3")
        audio_manager.play_music()

    def _get_current_room_coord(self):
        tile_x = int(self.rect.x / TILESIZE)
        tile_y = int(self.rect.y / TILESIZE)
        room_tile_width = self.game.dungeon_generator.room_tile_width
        room_tile_height = self.game.dungeon_generator.room_tile_height
        wall_thickness = self.game.dungeon_generator.wall_thickness
        room_unit_width = room_tile_width + wall_thickness * 2
        room_unit_height = room_tile_height + wall_thickness * 2
        return (tile_x // room_unit_width, tile_y // room_unit_height)