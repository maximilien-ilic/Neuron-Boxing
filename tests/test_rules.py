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
    return (state.tick, state.result, f0.hp, f0.touches_scored, f0.x, f0.y,f1.hp, f1.touches_scored, f1.x, f1.y)


def test_determinisme():
    actions = [(i % 10, (i * 7) % 10) for i in range(500)]
    assert simuler(43,actions) == simuler(43,actions)