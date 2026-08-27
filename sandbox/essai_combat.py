from sim import rules as r


def essai_combat():
    state = r.initial_state(42)
    state.fighters[0].x = 1
    state.fighters[1].x = 2
    state.fighters[0].y = 1
    state.fighters[1].y = 1
    while state.result is None :
        r.step(state,9,9)
    print(state)

essai_combat()