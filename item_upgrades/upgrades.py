import pygame


class WeaponUpgrades(pygame.sprite.Group):
    def __init__(self, game):
        self.game = game
        self.damage = 1
        self.speed = 1
        self.knockback = 2
        self.pierce = 2
        self.area = 0
        self.area_count = 1
        self.explosion = False
        self.boomerang = False
        self.double_attack = False
        self.cone_attack = False

        self.upgrade_groups = {}
        self._init_groups()

    def _init_groups(self):
        self.damage_group = pygame.sprite.Group()
        self.speed_group = pygame.sprite.Group()
        self.knockback_group = pygame.sprite.Group()
        self.pierce_group = pygame.sprite.Group()
        self.area_group = pygame.sprite.Group()
        self.explosion_group = pygame.sprite.Group()
        self.boomerang_group = pygame.sprite.Group()
        self.double_group = pygame.sprite.Group()
        self.cone_group = pygame.sprite.Group()
        self.upgrade_all_group = pygame.sprite.Group(
            self.damage_group,
            self.speed_group,
            self.knockback_group,
            self.pierce_group,
            self.area_group,
            self.explosion_group,
            self.boomerang_group,
            self.double_group,
            self.cone_group,
        )

    def get_group(self, upgrade_type):
        return getattr(self, f"{upgrade_type}_group")

    def damage(self, game, x, y, player=None):
        from item_upgrades.visuals import UpgradeVisual
        visual = UpgradeVisual(self.game, x, y, "damage", self.game.ecs_world)
        self.damage_group.add(visual)
        self.upgrade_all_group.add(visual)

    def speed(self, game, x, y, player=None):
        from item_upgrades.visuals import UpgradeVisual
        visual = UpgradeVisual(self.game, x, y, "speed", self.game.ecs_world)
        self.speed_group.add(visual)
        self.upgrade_all_group.add(visual)

    def knockback(self, game, x, y, player=None):
        from item_upgrades.visuals import UpgradeVisual
        visual = UpgradeVisual(self.game, x, y, "knockback", self.game.ecs_world)
        self.knockback_group.add(visual)
        self.upgrade_all_group.add(visual)

    def pierce(self, game, x, y, player=None):
        from item_upgrades.visuals import UpgradeVisual
        visual = UpgradeVisual(self.game, x, y, "pierce", self.game.ecs_world)
        self.pierce_group.add(visual)
        self.upgrade_all_group.add(visual)

    def area(self, game, x, y, player=None):
        from item_upgrades.visuals import UpgradeVisual
        visual = UpgradeVisual(self.game, x, y, "area", self.game.ecs_world)
        self.area_group.add(visual)
        self.upgrade_all_group.add(visual)

    def explosion(self, game, x, y, player=None):
        from item_upgrades.visuals import UpgradeVisual
        visual = UpgradeVisual(self.game, x, y, "explosion", self.game.ecs_world)
        self.explosion_group.add(visual)
        self.upgrade_all_group.add(visual)

    def boomerang(self, game, x, y, player=None):
        from item_upgrades.visuals import UpgradeVisual
        visual = UpgradeVisual(self.game, x, y, "boomerang", self.game.ecs_world)
        self.boomerang_group.add(visual)
        self.upgrade_all_group.add(visual)

    def double_attack(self, game, x, y, player=None):
        from item_upgrades.visuals import UpgradeVisual
        visual = UpgradeVisual(self.game, x, y, "double_attack", self.game.ecs_world)
        self.double_group.add(visual)
        self.upgrade_all_group.add(visual)

    def cone_attack(self, game, x, y, player=None):
        from item_upgrades.visuals import UpgradeVisual
        visual = UpgradeVisual(self.game, x, y, "cone_attack", self.game.ecs_world)
        self.cone_group.add(visual)
        self.upgrade_all_group.add(visual)

    def update(self):
        for upgrade in self.upgrade_all_group:
            upgrade.update()

    def kill(self):
        self.upgrade_all_group.kill()
