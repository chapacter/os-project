import pygame

from core.ecs_world import System, World
from entity.components.bullet import BulletComponent
from entity.components.collision.block_collider import BlockColliderComponent
from entity.components.tags import BulletMarker, EnemyMarker, PlayerMarker
from entity.factories.effect_factory import EffectFactory
from entity.systems.bullet_system import explode_bullet
from utils.settings import CONTACT_KNOCKBACK_FORCE, CONTACT_KNOCKBACK_INTERVAL, KNOCKBACK_DURATION


class EntityCollisionSystem(System):
    def __init__(self, world: World, get_blocks_fn, all_sprites=None):
        super().__init__(world)
        self._get_blocks = get_blocks_fn
        self._all_sprites = all_sprites

    def update(self, dt: float) -> None:
        blocks = self._get_blocks()
        bullets = self.world.query(BulletMarker)
        enemies = self.world.query(EnemyMarker, BlockColliderComponent)
        players = self.world.query(PlayerMarker)

        for bullet in bullets:
            self._bullet_vs_block(bullet, blocks)
            self._bullet_vs_enemy(bullet, enemies)
            self._bullet_vs_player(bullet, players)

        for player in players:
            self._player_vs_enemy(player, enemies)

    # ── Bullet collision helpers ──────────────────────────────────

    def _bullet_vs_block(self, bullet, blocks):
        if not blocks:
            return
        if not hasattr(bullet, "rect"):
            return
        bc = self.world.get_component(bullet, BulletComponent)
        for block in blocks:
            if bullet.rect.colliderect(block.rect):
                if bc and bc.explosive:
                    explode_bullet(self.world, bc, bullet.rect.centerx, bullet.rect.centery, self._all_sprites)
                bullet.kill()
                return

    def _bullet_vs_enemy(self, bullet, enemies):
        if not hasattr(bullet, "rect"):
            return
        bc = self.world.get_component(bullet, BulletComponent)
        if bc is None or not bc.hits_enemies:
            return
        for enemy in enemies:
            ec = self.world.get_component(enemy, BlockColliderComponent)
            if ec is None:
                continue
            if bullet.rect.colliderect(ec.hitbox) and enemy not in bc.hit_enemies:
                bc.hit_enemies.append(enemy)

                knockback_dir = pygame.math.Vector2(
                    enemy.rect.centerx - bullet.rect.centerx,
                    enemy.rect.centery - bullet.rect.centery,
                )
                if knockback_dir.length() > 0:
                    knockback_dir = knockback_dir.normalize()
                else:
                    knockback_dir = pygame.math.Vector2(bc.hit_dir_x, bc.hit_dir_y)

                EffectFactory.create_ecs_effect(
                    self.world, bullet.rect.centerx, bullet.rect.centery, "hit",
                    groups=[self._all_sprites] if self._all_sprites else None,
                )

                enemy.take_knockback(knockback_dir, bc.knockback_force)
                enemy.damage(bc.damage)

                if bc.explosive:
                    explode_bullet(self.world, bc, bullet.rect.centerx, bullet.rect.centery, self._all_sprites)
                    if not bc.piercing:
                        bullet.kill()
                        return
                elif not bc.piercing:
                    bullet.kill()
                    return

    def _bullet_vs_player(self, bullet, players):
        bc = self.world.get_component(bullet, BulletComponent)
        if bc is None or not bc.hits_player:
            return
        if not hasattr(bullet, "rect"):
            return
        for player in players:
            if not hasattr(player, "hitbox"):
                continue
            if not bullet.rect.colliderect(player.hitbox):
                continue
            EffectFactory.create_ecs_effect(
                self.world, bullet.rect.centerx, bullet.rect.centery, "hit",
                groups=[self._all_sprites] if self._all_sprites else None,
            )
            player.damage(bc.damage)
            bullet.kill()
            return

    # ── Player collision helpers ──────────────────────────────────

    def _player_vs_enemy(self, player, enemies):
        if not hasattr(player, "hitbox"):
            return
        player_hitbox = player.hitbox
        enemy_collided = False
        for enemy in enemies:
            bc = self.world.get_component(enemy, BlockColliderComponent)
            if bc is None:
                continue
            if not player_hitbox.colliderect(bc.hitbox):
                continue
            enemy_collided = True

            if getattr(player, "contact_knockback_cooldown", 0) <= 0:
                contact_dir = pygame.math.Vector2(
                    player.rect.centerx - enemy.rect.centerx,
                    player.rect.centery - enemy.rect.centery,
                )
                if contact_dir.length() > 0:
                    contact_dir = contact_dir.normalize()

                enemy_type = getattr(enemy, "enemy_type", None)
                if enemy_type in [2, 3]:
                    player.knockback_type = "strong"
                    force = CONTACT_KNOCKBACK_FORCE
                    duration = KNOCKBACK_DURATION
                else:
                    player.knockback_type = "weak"
                    force = 4
                    duration = 8

                player.knockback_frame = 0
                vel_along = max(0, player.velocity.dot(contact_dir))
                player.knockback_comp.velocity = contact_dir * force + contact_dir * vel_along * 0.3
                player.knockback_comp.duration_remaining = duration
                if player.action_state != "dodge":
                    player.action_state = "knockback"
                player.contact_knockback_cooldown = CONTACT_KNOCKBACK_INTERVAL

            overlap_x = min(
                player.rect.right - enemy.rect.left,
                enemy.rect.right - player.rect.left,
            )
            overlap_y = min(
                player.rect.bottom - enemy.rect.top,
                enemy.rect.bottom - player.rect.top,
            )
            MAX_PUSH = 3
            if overlap_x < overlap_y:
                push = min(overlap_x, MAX_PUSH)
                if player.rect.centerx < enemy.rect.centerx:
                    player.rect.x -= push
                else:
                    player.rect.x += push
            else:
                push = min(overlap_y, MAX_PUSH)
                if player.rect.centery < enemy.rect.centery:
                    player.rect.y -= push
                else:
                    player.rect.y += push

        if hasattr(player.game, "enemy_collided"):
            player.game.enemy_collided = enemy_collided
