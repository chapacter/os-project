from core.ecs_world import System, World
from entity.components.collision.block_collider import BlockColliderComponent
from entity.components.combat.knockback import KnockbackComponent


def resolve_x(hitbox, blocks, vel):
    if vel.x == 0:
        return
    for block in blocks:
        if hitbox.colliderect(block.rect):
            if vel.x > 0:
                hitbox.right = block.rect.left
            else:
                hitbox.left = block.rect.right
            vel.x = 0


def resolve_y(hitbox, blocks, vel):
    if vel.y == 0:
        return
    for block in blocks:
        if hitbox.colliderect(block.rect):
            if vel.y > 0:
                hitbox.bottom = block.rect.top
            else:
                hitbox.top = block.rect.bottom
            vel.y = 0


class BlockCollisionSystem(System):
    def __init__(self, world: World, get_blocks_fn):
        super().__init__(world)
        self._get_blocks = get_blocks_fn

    def update(self, dt: float) -> None:
        blocks = self._get_blocks()
        if not blocks:
            return

        for entity in self.world.query(BlockColliderComponent):
            bc = self.world.get_component(entity, BlockColliderComponent)
            if bc is None:
                continue

            kb = self.world.get_component(entity, KnockbackComponent)
            if kb and kb.velocity.length() > 0:
                self._apply_vector(entity, bc, blocks, kb.velocity)

            v = getattr(entity, "velocity", None)
            if v and v.length() > 0:
                self._apply_vector(entity, bc, blocks, v)

            if hasattr(entity, "rect") and entity.rect:
                entity.rect.center = bc.hitbox.center
            if hasattr(entity, "sync_physics"):
                entity.sync_physics()

    def _apply_vector(self, entity, bc, blocks, vel):
        if bc.use_float_pos:
            bc.pos_x += vel.x
            bc.hitbox.x = int(bc.pos_x)
        else:
            bc.hitbox.x += vel.x

        if not bc.noclip:
            resolve_x(bc.hitbox, blocks, vel)

        if bc.use_float_pos:
            bc.pos_y += vel.y
            bc.hitbox.y = int(bc.pos_y)
        else:
            bc.hitbox.y += vel.y

        if not bc.noclip:
            resolve_y(bc.hitbox, blocks, vel)
