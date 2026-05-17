from dataclasses import dataclass


@dataclass
class HealthComponent:
    health: int = 5
    max_health: int = 5
    died: bool = False
