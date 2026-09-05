from sim import rules as r
from sim import constants as c

limite = c.MAX_TICKS + 100

def simuler(seed,actions):
    state = r.initial_state(seed)
    compteur = 0
    while state.result is None :
        act0 , act1 = actions[compteur % len(actions)]
        r.step(state,act0,act1)
        compteur += 1
        assert compteur < limite
    f0 = state.fighters[0]
    f1 = state.fighters[1]
    return (state.tick, state.result, f0.hp, f0.touches_scored,f1.hp, f1.touches_scored)


def test_determinisme():
    actions = [(i % 10, (i * 7) % 10) for i in range(500)]
    assert simuler(43,actions) == simuler(43,actions)


MIRROR = (
    0,
    1,
    8,
    7,
    6,
    5,
    4,
    3,
    2,
    9
)

def mirror_action(action: int) -> int:
    return MIRROR[action]

def test_involution():
    for a in range(c.N_ACTIONS):
        assert mirror_action(mirror_action(a)) == a

def mirror_result(result):
    if result == c.RESULT_P0_WINS :
        return c.RESULT_P1_WINS
    elif result == c.RESULT_P1_WINS :
        return c.RESULT_P0_WINS
    else:
        return result

def test_symetrie():
    actions = [(i % 10, (i * 7) % 10) for i in range(500)]
    actions_sym = [(mirror_action(a1),mirror_action(a0))for a0, a1 in actions]
    r1 = simuler(43, actions)
    r2 = simuler(43, actions_sym)
    tick1, res1, hp0_1, tou0_1, hp1_1, tou1_1 = r1
    tick2, res2, hp0_2, tou0_2, hp1_2, tou1_2 = r2
    assert hp0_1 == hp1_2
    assert hp1_1 == hp0_2
    assert tou0_1 == tou1_2
    assert tou1_1 == tou0_2
    assert res1 == mirror_result(res2)

