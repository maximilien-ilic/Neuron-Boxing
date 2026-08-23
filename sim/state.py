import random
from dataclasses import dataclass

from sim.constants import ACTIVE_END, RECOVERY_END


@dataclass
class FighterState:
    x: float
    y: float
    vx: float
    vy: float
    punch_timer: int
    hp: float
    touches_scored: int

    @property
    def is_ready(self) -> bool:
        return self.punch_timer == 0

    @property
    def is_threatening(self) -> bool:
        return self.punch_timer > ACTIVE_END

    @property
    def is_immobile(self) -> bool:
        return self.punch_timer > RECOVERY_END


@dataclass
class GameState:
    tick: int
    fighters: tuple[FighterState, FighterState]
    rng: random.Random
    result: None | int
