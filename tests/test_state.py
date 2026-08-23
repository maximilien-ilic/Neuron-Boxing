
from sim.constants import PUNCH_CYCLE, PUNCH_WINDUP, PUNCH_ACTIVE, PUNCH_RECOVERY
from sim.state import FighterState

def test_ready_uniquement_a_zero():
    n = sum(
        FighterState(0.0, 0.0, 0.0, 0.0, t, 100.0, 0).is_ready
        for t in range(PUNCH_CYCLE + 1)
    )
    assert n == 1


def test_immobile_a_zero():
    n = sum(
        FighterState(0.0, 0.0, 0.0, 0.0, t, 100.0, 0).is_immobile
        for t in range(PUNCH_CYCLE + 1)
    )
    assert n == PUNCH_WINDUP + PUNCH_ACTIVE + PUNCH_RECOVERY


def test_threatening_a_zero():
    n = sum(
        FighterState(0.0, 0.0, 0.0, 0.0, t, 100.0, 0).is_threatening
        for t in range(PUNCH_CYCLE + 1)
    )
    assert n == PUNCH_WINDUP + PUNCH_ACTIVE
