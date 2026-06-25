class DoorPhysics:
    def __init__(self, game):
        self.game = game

    def register(self, rect, block_id=None):
        if self.game.physics_enabled and self.game.physics:
            if block_id is None:
                block_id = f"door_{rect.x}_{rect.y}"
            self.game.physics.add_static_block(
                rect.x, rect.y,
                rect.width, rect.height,
                block_id,
            )

    def remove(self, rect):
        if self.game.physics:
            block_id = f"door_{rect.x}_{rect.y}"
            self.game.physics.remove_shape(block_id)
