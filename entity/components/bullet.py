from dataclasses import dataclass, field


@dataclass
class BulletComponent:
    damage: int = 3
    knockback_force: float = 4.0
    distance_traveled: float = 0.0
    max_distance: float = 500.0
    pos_x: float = 0.0
    pos_y: float = 0.0
    piercing: bool = False
    explosive: bool = False
    boomerang: bool = False
    hit_dir_x: float = 1.0
    hit_dir_y: float = 0.0
    returning: bool = False
    hits_enemies: bool = True
    hits_player: bool = False
    hit_enemies: list = field(default_factory=list)
