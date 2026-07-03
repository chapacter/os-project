from dataclasses import dataclass


@dataclass
class PenetrationComponent:
    remaining: float = 13.0
    penetrating: bool = False
