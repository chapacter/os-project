from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class RoomType(str, Enum):
    LOBBY = "lobby"
    EMPTY = "empty"
    ENEMY = "enemy"
    ELITE = "elite"
    LOOT = "loot"
    BOSS = "boss"
    EVENT = "event"
    COMBAT = "combat"
    GUARDIAN = "guardian"
    JUDGE = "judge"
    SHOP = "shop"
    ALTAR = "altar"
    LORE = "lore"
    SECRET = "secret"


@dataclass
class RoomConfig:
    spawns_enemies: bool = False
    is_boss: bool = False
    seal_on_enter: bool = True
    wall_theme: str = "battle_wall"
    floor_theme: str = "battle_floor"
    decor_theme: str = "battle_decor"
    has_portal: bool = False
    spawn_count_range: tuple[int, int] = (0, 0)
    hp_multiplier: float = 1.0


ROOM_CONFIGS: dict[RoomType, RoomConfig] = {
    RoomType.LOBBY: RoomConfig(seal_on_enter=False),
    RoomType.EMPTY: RoomConfig(seal_on_enter=False),
    RoomType.ENEMY: RoomConfig(
        spawns_enemies=True, spawn_count_range=(2, 4),
    ),
    RoomType.ELITE: RoomConfig(
        spawns_enemies=True, spawn_count_range=(6, 12), hp_multiplier=1.5,
    ),
    RoomType.LOOT: RoomConfig(seal_on_enter=False),
    RoomType.BOSS: RoomConfig(
        is_boss=True, has_portal=True,
        wall_theme="boss_wall", floor_theme="boss_floor", decor_theme="boss_decor",
    ),
    RoomType.EVENT: RoomConfig(seal_on_enter=False),
    RoomType.COMBAT: RoomConfig(
        spawns_enemies=True, spawn_count_range=(2, 4),
    ),
    RoomType.GUARDIAN: RoomConfig(
        is_boss=True, has_portal=True,
        wall_theme="boss_wall", floor_theme="boss_floor", decor_theme="boss_decor",
    ),
    RoomType.JUDGE: RoomConfig(
        is_boss=True, has_portal=True,
        wall_theme="boss_wall", floor_theme="boss_floor", decor_theme="boss_decor",
    ),
    RoomType.SHOP: RoomConfig(seal_on_enter=False),
    RoomType.ALTAR: RoomConfig(seal_on_enter=False),
    RoomType.LORE: RoomConfig(seal_on_enter=False),
    RoomType.SECRET: RoomConfig(seal_on_enter=False),
}


class RoomState(str, Enum):
    INTRO = "intro"
    WAVE_1 = "wave_1"
    WAVE_2 = "wave_2"
    CLEARED = "cleared"
    REWARD_SPAWNED = "reward_spawned"


class SizeClass(str, Enum):
    LARGE = "large"
    MEDIUM = "medium"
    SMALL = "small"


class DecorCategory(str, Enum):
    STRUCTURAL = "structural"
    AMBIENT = "ambient"
    THEMATIC = "thematic"
    INTERACTIVE = "interactive"
    SET_DRESSING = "set_dressing"


@dataclass
class DecorationSlot:
    zone_name: str
    x1: int
    y1: int
    x2: int
    y2: int
    allowed_sizes: list[SizeClass] = field(default_factory=lambda: list(SizeClass))


@dataclass
class SpawnSlot:
    x: int
    y: int
    slot_type: str  # floor_a, platform_b, ceiling_c


@dataclass
class HazardZone:
    x1: int
    y1: int
    x2: int
    y2: int
    hazard_type: str  # spikes, toxic_gas, etc.


@dataclass
class PlatformRect:
    x: int
    y: int
    width: int
    height: int


@dataclass
class RoomTemplate:
    template_id: str
    realm_id: str
    room_type: RoomType
    width: int
    height: int
    tile_map: list[list[str]]  # 2D character grid
    door_sides: list[str] = field(default_factory=list)  # ["north","south","east","west"]
    spawn_slots: list[SpawnSlot] = field(default_factory=list)
    hazard_zones: list[HazardZone] = field(default_factory=list)
    platforms: list[PlatformRect] = field(default_factory=list)
    slots: dict[str, DecorationSlot] = field(default_factory=dict)
    difficulty_weight: float = 1.0


@dataclass
class RoomVariant:
    variant_id: str
    template_id: str
    palette_override: Optional[dict[str, list[str]]] = None
    decor_overrides: list[dict] = field(default_factory=list)
    lighting_profile: str = "default"
    particle_profile: str = "default"


@dataclass
class RoomInstance:
    template_id: str
    variant_id: str
    room_type: RoomType
    grid_x: int
    grid_y: int
    seed_offset: int = 0
    state: RoomState = RoomState.INTRO
    cleared: bool = False
    enemies: list[dict] = field(default_factory=list)
    decor: list[str] = field(default_factory=list)
    wave_index: int = 0


@dataclass
class DecorObject:
    object_id: str
    size_class: SizeClass = SizeClass.SMALL
    category: DecorCategory = DecorCategory.STRUCTURAL
    allowed_zones: list[str] = field(default_factory=list)
    spawn_weight: float = 1.0
    duplicate_limit: int = 2
    allowed_room_types: list[RoomType] = field(default_factory=lambda: [RoomType.COMBAT, RoomType.GUARDIAN])
    variation: list[str] = field(default_factory=list)
    animation_enabled: bool = False
    fallback_color: tuple[int, int, int, int] = (128, 128, 128, 255)


@dataclass
class VisualBudget:
    large_props: int = 3
    medium_props: int = 5
    small_props: int = 10
    animated_props: int = 2
    particle_density: float = 0.45


@dataclass
class SlotRules:
    center_lane_forbidden: bool = True
    edge_priority: float = 0.8
    background_priority: float = 0.9


@dataclass
class RealmPalette:
    base: list[str] = field(default_factory=lambda: ["#101423", "#1b2b44"])
    mid: list[str] = field(default_factory=lambda: ["#556b8a", "#7e8fa6"])
    accent: list[str] = field(default_factory=lambda: ["#d28f3e", "#f1d27a"])


@dataclass
class RealmConfig:
    realm_id: str
    display_name: str
    description: str = ""
    palette: RealmPalette = field(default_factory=RealmPalette)
    enemy_pool: list[int] = field(default_factory=lambda: [0, 1, 2, 3])
    guardian_pool: list[str] = field(default_factory=list)
    judge_id: str = ""
    music_background: str = ""
    music_boss: str = ""
    min_combat_rooms: int = 2
    max_combat_rooms: int = 4
    guardian_count: int = 1
    has_shop: bool = True
    has_altar: bool = True
    visual_budget: VisualBudget = field(default_factory=VisualBudget)
    slot_rules: SlotRules = field(default_factory=SlotRules)
    budget_multiplier: float = 1.0


@dataclass
class WaveDefinition:
    wave_index: int = 0
    budget_percent: float = 0.5
    spawn_delay_frames: int = 30
    min_enemies: int = 1
    max_enemies: int = 8


@dataclass
class EnemyBudgetEntry:
    enemy_type_id: int = 0
    cost: int = 10


@dataclass
class RoomBudgetConfig:
    base_budget: int = 100
    min_waves: int = 1
    max_waves: int = 2
    wave_definitions: list[WaveDefinition] = field(default_factory=lambda: [
        WaveDefinition(wave_index=0, budget_percent=0.4, spawn_delay_frames=30),
        WaveDefinition(wave_index=1, budget_percent=0.6, spawn_delay_frames=60),
    ])


@dataclass
class EnemyBudgetConfig:
    enemies: dict[int, int] = field(default_factory=lambda: {
        0: 10, 1: 12, 2: 15, 3: 20,
        4: 15, 5: 25, 6: 25, 7: 25,
        8: 30, 9: 35, 10: 30,
        11: 40, 12: 40, 13: 45, 14: 45,
    })
    rooms: dict[str, RoomBudgetConfig] = field(default_factory=lambda: {
        "combat": RoomBudgetConfig(base_budget=100),
        "elite": RoomBudgetConfig(base_budget=180, max_waves=2),
        "guardian": RoomBudgetConfig(base_budget=60, max_waves=1),
    })
    realm_multipliers: dict[str, float] = field(default_factory=lambda: {
        "entangled_ingress": 1.0,
        "still_bastion": 1.1,
        "wasted_pit": 1.2,
        "living_walls": 1.3,
        "the_old_world": 1.5,
    })
