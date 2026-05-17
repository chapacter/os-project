from dataclasses import dataclass


@dataclass
class LifetimeComponent:
    remaining: int = 0
