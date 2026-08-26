import math
import random

from sim import constants as c
from sim.state import FighterState, GameState

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

MIN_POS = c.BODY_RADIUS
MAX_POS = c.RING_SIZE - c.BODY_RADIUS




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
    f0.x = max(MIN_POS, min(f0.x + move_x0,MAX_POS ))
    f0.y = max(MIN_POS, min(f0.y + move_y0, MAX_POS))
    f1.x = max(MIN_POS, min(f1.x + move_x1, MAX_POS))
    f1.y = max(MIN_POS, min(f1.y + move_y1, MAX_POS))
    f0.vx = f0.x - before_f0_x
    f0.vy = f0.y - before_f0_y
    f1.vx = f1.x - before_f1_x
    f1.vy = f1.y - before_f1_y
    # 4. Résoudre la collision entre les deux corps
    ecart_x = f0.x - f1.x
    ecart_y = f0.y - f1.y
    hypo = math.hypot(ecart_x,ecart_y)
    if  hypo < c.MIN_SEPARATION and hypo > 1e-9:
        repoussement = (c.MIN_SEPARATION - hypo) / 2
        f0.x = f0.x + (ecart_x / hypo) * repoussement
        f1.x = f1.x - (ecart_x / hypo) * repoussement
        f0.y = f0.y + (ecart_y / hypo) * repoussement
        f1.y = f1.y - (ecart_y / hypo) * repoussement
        f0.x = max(MIN_POS, min(f0.x, MAX_POS))
        f0.y = max(MIN_POS, min(f0.y, MAX_POS))
        f1.x = max(MIN_POS, min(f1.x, MAX_POS))
        f1.y = max(MIN_POS, min(f1.y, MAX_POS))
    # 5. Déclencher les nouveaux coups
    if action0 == c.ACTION_PUNCH and f0.is_ready:
        f0.punch_timer = c.PUNCH_CYCLE
    if action1 == c.ACTION_PUNCH and f1.is_ready:
        f1.punch_timer = c.PUNCH_CYCLE
    # 6. Résoudre les dégâts
    ecart_x_coli = f0.x - f1.x
    ecart_y_coli = f0.y - f1.y
    hypo = math.hypot(ecart_x_coli, ecart_y_coli)
    f0_touch = f0.punch_timer == c.WINDUP_END and hypo <= c.PUNCH_RANGE
    f1_touch = f1.punch_timer == c.WINDUP_END and hypo <= c.PUNCH_RANGE
    if f0_touch:
        f1.hp = f1.hp - c.PUNCH_DAMAGE
        f0.touches_scored = f0.touches_scored + 1
    if f1_touch:
        f0.hp = f0.hp - c.PUNCH_DAMAGE
        f1.touches_scored = f1.touches_scored + 1
    # 7. Vérifier les conditions de fin
    if f0.hp <= 0 and f1.hp <= 0:
        state.result = c.RESULT_DRAW
    elif f0.hp <= 0 and f1.hp > 0:
        state.result = c.RESULT_P1_WINS
    elif f1.hp <= 0 and f0.hp > 0:
        state.result = c.RESULT_P0_WINS
    elif c.MAX_TICKS <= state.tick :
        if f0.touches_scored > f1.touches_scored:
            state.result = c.RESULT_P0_WINS
        elif f1.touches_scored > f0.touches_scored:
            state.result = c.RESULT_P1_WINS
        else:
            state.result = c.RESULT_DRAW
    # 8. Avancer le tick
    state.tick = state.tick + 1

    return state

