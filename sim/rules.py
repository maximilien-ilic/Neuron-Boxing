from sim.state import FighterState, GameState
from sim import constants as c
import random


def initial_state(seed: int) -> GameState:
    """Construit l'état initial d'un match, reproductible à partir de la graine"""
    boxer1 = FighterState(
        c.RING_SIZE / 2 - c.START_DISTANCE / 2, c.RING_SIZE / 2, 0, 0, 0, c.MAX_HP, 0
    )
    boxer2 = FighterState(
        c.RING_SIZE / 2 + c.START_DISTANCE / 2, c.RING_SIZE / 2, 0, 0, 0, c.MAX_HP, 0
    )
    partie = GameState(0, (boxer1, boxer2), random.Random(seed), c.RESULT_ONGOING)
    return partie
