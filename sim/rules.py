from sim.state import FighterState, GameState
from sim import constants as c
import random
import math

#TUPLE STEP DEPLACEMENT

r2 = math.sqrt(2)
MOVES = (
    (0.0, 0.0),                                      # 0 : rien
    (0.0, c.MOVE_SPEED),                             # 1 : ↑
    (c.MOVE_SPEED / r2, c.MOVE_SPEED / r2),          # 2 : ↗
    (c.MOVE_SPEED, 0.0),                             # 3 : →
    (c.MOVE_SPEED / r2, -c.MOVE_SPEED / r2),         # 4 : ↘
    (0.0, -c.MOVE_SPEED),                            # 5 : ↓
    (-c.MOVE_SPEED / r2, -c.MOVE_SPEED / r2),        # 6 : ↙
    (-c.MOVE_SPEED, 0.0),                            # 7 : ←
    (-c.MOVE_SPEED / r2, c.MOVE_SPEED / r2),         # 8 : ↖
    (0.0, 0.0),                                      # 9 : frapper
)





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


def step(state: GameState, action0: int, action1: int) -> GameState:
    """ step fait avancer le jeu d'un seul tick, soit 1/30 de seconde """
    f0 = state.fighters[0]
    f1 = state.fighters[1]
    # 1. Décrémenter les timers
    move_x0 = move_y0 = move_x1 = move_y1 = 0.0
    if not f0.is_ready:
        f0.punch_timer -= 1
    if not f1.is_ready :
        f1.punch_timer -= 1
    # 2. Calculer les intentions
    if not f0.is_immobile :
        move_x0, move_y0 = MOVES[action0]
    if not f1.is_immobile :
        move_x1, move_y1 = MOVES[action1]
    # 3. Appliquer les déplacements
    before_f0_x = f0.x
    before_f0_y = f0.y
    before_f1_x = f1.x
    before_f1_y = f1.y
    f0.x = max(c.BODY_RADIUS, min(f0.x + move_x0, c.RING_SIZE - c.BODY_RADIUS))
    f0.y = max(c.BODY_RADIUS, min(f0.y + move_y0, c.RING_SIZE - c.BODY_RADIUS))
    f1.x = max(c.BODY_RADIUS, min(f1.x + move_x1, c.RING_SIZE - c.BODY_RADIUS))
    f1.y = max(c.BODY_RADIUS, min(f1.y + move_y1, c.RING_SIZE - c.BODY_RADIUS))
    f0.vx = f0.x - before_f0_x
    f0.vy = f0.y - before_f0_y
    f1.vx = f1.x - before_f1_x
    f1.vy = f1.y - before_f1_y
    return state

