# Neuron Boxing — Contrat d'observation v1

Ce document décrit ce que le réseau perçoit du jeu et ce qu'il peut y faire.
C'est l'interface entre la simulation et tous les modèles entraînés.

Il est **gelé**. Toute modification incrémente `OBS_VERSION` ou
`ACTION_VERSION` dans `sim/constants.py` et rend inutilisables — pas dégradés,
inutilisables — tous les modèles entraînés sous la version précédente.

| Constante | Valeur |
|---|---|
| `OBS_VERSION` | 1 |
| `ACTION_VERSION` | 1 |
| `OBS_SIZE` | 20 |
| `N_ACTIONS` | 10 |

---

## 1. Les 20 entrées

Toutes les valeurs sont des `float32`. Le vecteur est produit par
`encode_observation(state, player_id)` et vu **depuis** `player_id`.

| # | Contenu | Formule | Intervalle |
|---|---|---|---|
| 0 | Ma position x | `(x - RING_SIZE/2) / (RING_SIZE/2)` | [-1, 1] |
| 1 | Ma position y | `(y - RING_SIZE/2) / (RING_SIZE/2)` | [-1, 1] |
| 2 | Direction vers l'adversaire, x | `dx / distance` | [-1, 1] |
| 3 | Direction vers l'adversaire, y | `dy / distance` | [-1, 1] |
| 4 | Distance à l'adversaire | `distance / RING_DIAGONAL` | [0, 1] |
| 5 | Mes PV | `hp / MAX_HP` | [0, 1] |
| 6 | PV adverse | `hp_adv / MAX_HP` | [0, 1] |
| 7 | Ma progression d'attaque | `punch_timer / PUNCH_CYCLE` | [0, 1] |
| 8 | Ma menace | `1.0` si armement ou active, sinon `0.0` | {0, 1} |
| 9 | Progression d'attaque adverse | `punch_timer_adv / PUNCH_CYCLE` | [0, 1] |
| 10 | Menace adverse | `1.0` si armement ou active, sinon `0.0` | {0, 1} |
| 11 | Ma vitesse x | `vx / MOVE_SPEED` | [-1, 1] |
| 12 | Ma vitesse y | `vy / MOVE_SPEED` | [-1, 1] |
| 13 | Vitesse adverse x | `vx_adv / MOVE_SPEED` | [-1, 1] |
| 14 | Vitesse adverse y | `vy_adv / MOVE_SPEED` | [-1, 1] |
| 15 | Temps restant | `(MAX_TICKS - tick) / MAX_TICKS` | [0, 1] |
| 16 | Distance au mur le plus proche | `(d_mur - BODY_RADIUS) / (RING_SIZE/2 - BODY_RADIUS)` | [0, 1] |
| 17 | Différentiel de PV | `(hp - hp_adv) / MAX_HP` | [-1, 1] |
| 18 | Réservée | `0.0` | {0} |
| 19 | Réservée | `0.0` | {0} |

### Notes par entrée

**0-1 — Position centrée.** Le zéro correspond au centre du ring, le signe
indique de quel côté se trouve le boxeur. Voir §2.3 sur le centrage.

**2-3 — Direction normalisée.** `dx` et `dy` sont les écarts bruts vers
l'adversaire, `distance` leur norme euclidienne.

⚠️ **Garde-fou obligatoire.** Si `distance < 1e-6`, retourner `(0.0, 0.0)`
plutôt que de diviser. La règle de collision garantit normalement une
séparation d'au moins `MIN_SEPARATION`, mais cette garantie vit dans
`rules.py`, pas ici. Une fonction ne doit pas dépendre d'un invariant maintenu
dans un autre fichier : une régression dans `rules.py` produirait ici un `NaN`
qui se propagerait silencieusement dans tout le réseau — sorties toutes à
`NaN`, `argmax` retournant 0, comportement figé sur « ne rien faire », et
aucun message d'erreur.

**4 — Distance.** Divisée par `RING_DIAGONAL` (≈ 11,31) et non par
`RING_SIZE`. Deux boxeurs dans des coins opposés sont séparés par la
diagonale ; diviser par 8 produirait 1,41 et sortirait des bornes.

**7 et 9 — Progression d'attaque.** `punch_timer` décompte de `PUNCH_CYCLE`
vers 0. La valeur 0 signifie « prêt à frapper » ; toute valeur non nulle
indique un cycle en cours et sa proportion restante.

**8 et 10 — Menace.** Booléen encodé en flottant : vaut 1 pendant les phases
d'armement et active, c'est-à-dire quand un coup est susceptible de porter.
C'est cette entrée qui rend l'esquive théoriquement possible, puisque
l'armement dure 5 ticks.

**16 — Distance au mur.** `d_mur` est le minimum des quatre distances aux
murs. Mesurée **depuis le bord du corps** et non depuis le centre : un boxeur
collé au mur a son centre à `BODY_RADIUS` du bord, donc une mesure centrée ne
descendrait jamais sous 0,4 et la valeur 0 — « je suis acculé » — ne serait
jamais atteinte.

Le dénominateur est ajusté en conséquence : `RING_SIZE/2 - BODY_RADIUS` = 3,6.
Numérateur et dénominateur doivent décrire la même grandeur, sinon la plage
est tronquée.

**18-19 — Réservées.** Toujours à zéro en v1. Destinées à la garde et au coup
de pied, qui arriveront ensemble en v2. Les réserver dès maintenant permet
d'ajouter ces mécaniques sans changer `OBS_SIZE`, donc sans invalider les
champions v1 — ce qui ouvre une question d'étude : un champion v1 s'adapte-t-il
aux règles v2 plus vite qu'une population repartie de zéro ?

---

## 2. Les principes

### 2.1 Égocentré

Chaque boxeur voit le monde depuis sa propre position : « l'adversaire est à
3 unités devant-gauche », jamais « l'adversaire est en (14, 7) ».

Conséquence directe : dans une situation parfaitement symétrique, les deux
joueurs reçoivent **exactement le même vecteur**. Un seul réseau peut donc
jouer les deux camps, ce qui divise l'espace de recherche par deux.

C'est vérifié par un test dédié : `test_symetrie_obs`.

### 2.2 Normalisé

Un neurone calcule une somme pondérée de ses entrées. Si une entrée vaut 87
pendant qu'une autre vaut 0,03, la première écrase la seconde : le réseau ne
peut pas percevoir la seconde tant qu'il n'a pas découvert, par mutations, un
poids mille fois plus petit.

Pire, une entrée de grande amplitude **sature** l'activation : `tanh(400)` et
`tanh(4000)` valent tous deux 1,0. Le neurone devient aveugle à toutes ses
autres entrées, et pour NEAT, les innovations structurelles qui passent par
lui deviennent invisibles à la sélection.

**La règle : diviser par le maximum réellement atteignable, pas par le maximum
théorique.** C'est la source d'erreur la plus fréquente ici — voir les entrées
4 et 16, où le maximum naïf est faux dans les deux cas.

Vérifié par `test_bornes` : `np.all(np.abs(obs) <= 1.0)` sur des états
aléatoires.

### 2.3 Le centrage : choix v1 et expérience prévue

Les entrées 4, 5, 6, 7, 9, 15 et 16 sortent dans [0, 1] et ne sont jamais
négatives. Une entrée toujours positive n'exploite que la moitié de la
sensibilité de `tanh`, qui est raide autour de zéro et plate aux extrêmes.
Le réseau doit compenser via son biais : deux paramètres à régler au lieu
d'un.

Les centrer serait possible : `2 × valeur - 1`.

**Décision v1 : ne pas centrer.** Le gain théorique est réel mais faible, et
il n'est pertinent que si la valeur médiane a un sens naturel — ce qui est le
cas pour le différentiel de PV (entrée 17, déjà centrée : zéro signifie
« à égalité ») mais pas pour la distance au mur, où « à mi-chemin du centre »
ne veut rien dire.

**Expérience prévue en phase 7 :** deux runs identiques, l'un centré, l'autre
non, et mesure de l'écart en nombre de générations pour atteindre un Elo
donné. Trois lignes de code pour un résultat chiffré.

### 2.4 Couplage aux constantes physiques

L'entrée 16 dépend de `BODY_RADIUS`, une constante d'équilibrage du jeu. Si le
rayon du corps change un jour, le format d'observation change avec lui.

**Conséquence : un changement d'équilibrage peut forcer un `OBS_VERSION`.**
C'est un couplage facile à oublier, et il rendrait silencieusement invalides
des champions qu'on croirait encore comparables.

Toute constante physique utilisée dans `obs.py` doit être signalée ici.
État actuel : `RING_SIZE`, `RING_DIAGONAL`, `MAX_HP`, `MOVE_SPEED`,
`PUNCH_CYCLE`, `MAX_TICKS`, `BODY_RADIUS`.

---

## 3. Les 10 actions

Espace `Discrete(10)`. Le réseau produit 10 sorties, l'action retenue est
`argmax`.

| # | Action |
|---|---|
| 0 | Ne rien faire |
| 1 | Se déplacer ↑ |
| 2 | Se déplacer ↗ |
| 3 | Se déplacer → |
| 4 | Se déplacer ↘ |
| 5 | Se déplacer ↓ |
| 6 | Se déplacer ↙ |
| 7 | Se déplacer ← |
| 8 | Se déplacer ↖ |
| 9 | Frapper |

Les diagonales sont normalisées : la vitesse est identique dans les huit
directions.

**Actions ignorées.** Une action de déplacement (1-8) demandée pendant les
phases d'armement, active ou de récupération est ignorée. Une frappe (9)
demandée pendant un cycle déjà en cours est ignorée.

### Le miroir gauche/droite

L'observation étant égocentrée, l'axe X est inversé pour le joueur 1. Il faut
alors **aussi** inverser les actions correspondantes :

| Action | Miroir |
|---|---|
| 2 ↗ | 8 ↖ |
| 3 → | 7 ← |
| 4 ↘ | 6 ↙ |

Les actions 0, 1, 5 et 9 sont inchangées.

⚠️ **Oublier cette inversion est l'un des bugs les plus coûteux du projet.**
Le réseau apprendrait deux stratégies contradictoires selon le camp joué, la
fitness stagnerait à un niveau médiocre, et rien ne signalerait la cause.

Deux tests couvrent ce risque : `test_mirror_involutif`
(`mirror_action(mirror_action(a)) == a` pour toute action) et le test
d'équilibre 50/50 entre deux agents identiques.

---

## 4. Tests d'acceptation

| Test | Vérifie |
|---|---|
| `test_symetrie_obs` | Situation symétrique → vecteurs identiques pour les deux joueurs |
| `test_bornes` | `obs.shape == (20,)` et toutes les valeurs dans [-1, 1] |
| `test_reservees_a_zero` | Les entrées 18-19 valent exactement 0 |
| `test_mirror_involutif` | Appliquer le miroir deux fois redonne l'action initiale |
| `test_pas_de_nan` | Aucun `NaN` produit, y compris aux positions limites |