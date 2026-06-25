import math

import pygame

from entity.base import VectorEntity
from entity.components.tags import EnemyMarker
from entity.factories.effect_factory import EffectFactory
from projectiles.bullet import Enemy_Bullet
from utils.physics import COLLISION_ENTITY
from utils.settings import *


class UpgradableLoot(Enemy):
    """Upgradable enemy that drops weapon upgrades."""

    def __init__(self, game, x, y, enemy_type=None, hp_multiplier=1.0):
        self.game = game
        self._layer = PLAYER_LAYER
        self.groups = game.all_sprites, game.enemies
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * TILESIZE
        self.y = y * TILESIZE

        # Enemy type selection
        type_weights = {k: v["weight"] for k, v in ENEMY_TYPES.items()}
        self.enemy_type = (
            enemy_type if enemy_type is not None else weighted_choice(type_weights)
        )

        cfg = ENEMY_TYPES[self.enemy_type]
        self.width = cfg["sprite_size"][0]
        self.height = cfg["sprite_size"][1]

        # Initialize all enemy parameters
        self.speed_mod = cfg["speed_mod"]
        self.detection_range = cfg["detection_range"]
        self.attack_range = cfg["attack_range"]
        self.retreat_range = cfg["retreat_range"]
        self.retreat_distance = cfg["retreat_distance"]
        self.melee_range = cfg["melee_range"]
        self.attack_damage = cfg["damage"]
        self.shoot_cooldown = cfg["shoot_cooldown"]
        self.melee_cooldown = cfg["melee_cooldown"]
        self.always_chase = cfg["always_chase"]
        self.has_blink = cfg["has_blink"]
        self.blink_interval = cfg.get("blink_interval", 8)

        self.burst_shot = cfg.get("burst_shot", False)
        self.death_explosion = cfg.get("death_explosion", False)

        self.enrage_threshold = cfg.get("enrage_threshold", 0.0)
        self.enrage_speed_mult = cfg.get("enrage_speed_mult", 1.0)
        self.enrage_damage_mult = cfg.get("enrage_damage_mult", 1.0)
        self.enraged = False
        self._base_speed_mod = self.speed_mod
        self._base_damage = self.attack_damage

        self.healthbar = Enemy_Healthbar(game, self, x, y)

        self.frame_move = cfg.get("frame_move", 3)
        self.animations = {}
        direction_map = cfg.get("direction_map", {"down": 0, "left": 1, "right": 2, "up": 3})

        spritesheet = game.enemy_spritesheets[self.enemy_type]
        sprite_w, sprite_h = cfg["sprite_size"]

        for direction, row in direction_map.items():
            frames = []
            for col in range(self.frame_move):
                sprite = spritesheet.get_image(
                    col * sprite_w, row * sprite_h, self.width, self.height
                )
                frames.append(sprite)
            self.animations[direction] = frames

        self.image = self.animations["down"][0]
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

        self.hitbox = pygame.Rect(0, 0, HITBOX_WIDTH, HITBOX_HEIGHT)
        self.hitbox.center = self.rect.center

        self.direction = random.choice(["left", "right", "up", "down"])
        self.ai_state = "patrol"
        self.has_seen_player = False

        self.shoot_counter = 0
        self.shoot_state = "halt"
        self.melee_timer = 0

        self.retreat_progress = 0
        self.wait_after_retreat = 0

        self.patrol_timer = 0
        self.patrol_target_x = 0
        self.patrol_target_y = 0

        self._retreat_vector = pygame.math.Vector2(0, 0)

        # Apply health and knockback settings
        self.health_comp.max_health = int(cfg["hp"] * hp_multiplier)
        self.health_comp.health = self.health_comp.max_health

        self.physics_name = f"enemy_{id(self)}"
        VectorEntity.__init__(
            self, game, self.physics_name, collision_type=COLLISION_ENTITY, max_health=self.health_comp.max_health
        )
        self.knockback_comp.decay = ENEMY_KNOCKBACK_DECAY
        self.block_collider_comp.use_float_pos = True
        self.block_collider_comp.pos_x = float(self.hitbox.x)
        self.block_collider_comp.pos_y = float(self.hitbox.y)
        self.anim_comp = AnimationComponent(
            frames=self.animations[self.direction],
            frame_count=self.frame_move,
            speed=0.2,
            looping=True,
        )

        self.weapon_upgrades = WeaponUpgrades(self.game)

        # Spawn effect
        EffectFactory.create_ecs_effect(self.game.ecs_world, self.rect.centerx, self.rect.centery, "death",
                                        groups=[self.game.all_sprites], )

        tile_x = int(self.rect.x / TILESIZE)
        tile_y = int(self.rect.y / TILESIZE)
        room_tile_width = self.game.dungeon_generator.room_tile_width
        room_tile_height = self.game.dungeon_generator.room_tile_height
        wall_thickness = self.game.dungeon_generator.wall_thickness
        room_unit_width = room_tile_width + wall_thickness * 2
        room_unit_height = room_tile_height + wall_thickness * 2
        self.home_room = (tile_x // room_unit_width, tile_y // room_unit_height)
        self._set_patrol_target()

        if self.game and self.game.ecs_world:
            self.game.ecs_world.add_component(self, self.anim_comp)
            self.game.ecs_world.add_component(self, EnemyMarker())

    def damage(self, amount):
        """Take damage and update healthbar."""
        super().damage(amount)
        self.healthbar.damage(self.health_comp.max_health, self.health_comp.health)

    def update(self):
        """Update enemy position and animations."""
        self.move()
        self.animation()

        # Home room management
        if not self._is_inside_home_room():
            self._snap_to_home_room()

        self.collide_player()
        self.shoot()

    def collide_player(self):
        """Handle player collision."""
        collide = pygame.sprite.spritecollide(self, self.game.mainPlayer, False)
        if collide:
            pass

        anim = self.anim_comp
        if self.velocity.length() == 0:
            anim.frame_index = 0.0
        else:
            anim.frame_index += anim.speed
            if anim.frame_index >= anim.frame_count:
                anim.frame_index = 0.0

        self.image = anim.current_frame

        self.image = self.anim_comp.current_frame

    def animation(self):
        """Update enemy animations."""
        if self.has_blink and not self.visible:
            return

        anim = self.anim_comp
        anim.frames = self.animations[self.direction]
        anim.frame_count = self.frame_move

        if self.velocity.length() == 0:
            anim.frame_index = 0.0
        else:
            anim.frame_index += anim.speed
            if anim.frame_index >= anim.frame_count:
                anim.frame_index = 0.0

        self.image = anim.current_frame

        if self.enraged:
            tinted = self.image.copy()
            tinted.blit((100, 50, 50), (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            self.image = tinted

        if self.has_blink:
            self.image.set_alpha(255 if self.visible else 0)

    def _get_distance_to_player(self):
        """Get distance to player in pixels."""
        if not self.game.player:
            return float("inf")
        return math.hypot(self.game.player.rect.centerx - self.rect.centerx,
                          self.game.player.rect.centery - self.rect.centery)

    def _get_direction_to_player(self):
        """Get direction to player as string."""
        if not self.game.player:
            return self.direction
        return get_direction_from_velocity(self.game.player, self)

    def move(self):
        """Handle enemy AI and movement."""
        distance = self._get_distance_to_player()
        if distance <= self.detection_range:
            self.has_seen_player = True

        # Enrage mechanics
        if self.enrage_threshold > 0 and distance <= self.enrage_threshold:
            if self.health_comp.health / self.health_comp.max_health <= self.enrage_threshold:
                if not self.enraged:
                    self.enraged = True
                    self.speed_mod = self._base_speed_mod * self.enrage_speed_mult
                    self.attack_damage = int(self._base_damage * self.enrage_damage_mult)

        # Retreat mechanics
        if not self.has_seen_player:
            state = "patrol"
        elif self.retreat_range > 0 and self.health_comp.health / self.health_comp.max_health > self.enrage_threshold and self.retreat_range > distance:
            state = "retreat"
        else:
            state = "chase"

        # State timers
        if self.melee_timer > 0:
            self.melee_timer -= 1
        if self.patrol_timer > 0:
            self.patrol_timer -= 1

        # Movement logic
        if self.enraged:
            self.move_velocity = self.velocity
        else:
            if state == "patrol":
                if self.patrol_timer <= 0:
                    self._set_patrol_target()
                self.patrol_timer = random.randint(4, 8)
            else:
                self.velocity = self._get_direction_to_player() * self.speed_mod

        self.block_collider_comp.pos_x = float(self.rect.x)
        self.block_collider_comp.pos_y = float(self.rect.y)
        self.move(self.velocity)

    def _set_patrol_target(self):
        """Set new patrol target."""
        room_min_x, room_min_y, room_max_x, room_max_y = self._get_room_bounds()
        self.patrol_target_x = random.randint(room_min_x + 5, room_max_x - 5)
        self.patrol_target_y = random.randint(room_min_y + 5, room_max_y - 5)

    def _get_room_bounds(self):
        """Get room boundaries in pixels."""
        room_min_x = int(self.rect.x) - 100
        room_min_y = int(self.rect.y) - 100
        room_max_x = int(self.rect.x) + 100
        room_max_y = int(self.rect.y) + 100
        return room_min_x, room_min_y, room_max_x, room_max_y

    def _is_inside_home_room(self):
        """Check if enemy is inside home room."""
        room_min_x, room_min_y, room_max_x, room_max_y = self._get_room_bounds()
        return (room_min_x <= self.x <= room_max_x and room_min_y <= self.y <= room_max_y)

    def _snap_to_home_room(self):
        """Snap enemy to home room."""
        room_min_x, room_min_y, room_max_x, room_max_y = self._get_room_bounds()
        self.x = random.randint(room_min_x + 5, room_max_x - 5)
        self.y = random.randint(room_min_y + 5, room_max_y - 5)
        self.rect.x = self.x
        self.rect.y = self.y
        self._set_patrol_target()

    def shoot(self):
        """Handle shooting."""
        player = self.game.player
        if not player:
            return

        dist = self._get_distance_to_player()
        if player.rect.x >= self.rect.x:
            direction = "right"
        elif player.rect.x < self.rect.x:
            direction = "left"
        elif player.rect.y >= self.rect.y:
            direction = "down"
        else:
            direction = "up"

        if player.rect.x >= self.rect.x:
            direction = "right"

        dist = self._get_distance_to_player()
        if player.rect.x >= self.rect.x:
            direction = "right"
        elif player.rect.x < self.rect.x:
            direction = "left"
        elif player.rect.y >= self.rect.y:
            direction = "down"
        else:
            direction = "up"

        if self.shoot_counter >= self.shoot_cooldown:
            self.shoot_counter = 0
            if dist <= self.attack_range:
                Enemy_Bullet(self.game, self.rect.centerx, self.rect.centery,
                             self._get_direction_to_player() * 200, self.rect.centery + 200,
                             damage=self.attack_damage,
                             pierce=1,
                             )

    def on_death(self):
        """Called when enemy dies, drops weapon upgrade loot."""
        self.healthbar.kill_bar()
        self.game.items.add(self)
        weapon_type = random.choice(list(ENEMY_TYPES.keys()))
        upgrade_stats = {
            "damage": self.attack_damage + random.randint(1, 3),
            "speed": random.randint(1, 2),
            "knockback": random.randint(3, 6),
            "pierce": random.randint(2, 4),
            "type": weapon_type,
        }

        upgrade = WeaponUpgradeLoot(
            self.game,
            self.rect.centerx,
            self.rect.centery,
            upgrade_stats=upgrade_stats,
        )
        self.game.items.add(upgrade)
