# Neuron Boxing — Règles v1

Neuron Boxing est un jeu de boxe 1v1 minimaliste qui sert de terrain
d'expérience à des IA entraînées par neuroévolution : le vrai objet du
projet est d'observer comment ces réseaux de neurones se développent au
fil des générations, le jeu n'étant que le support de cette étude.

Ce document décrit les règles de la version 1. Elles sont **gelées** :
toute modification incrémente `RULESET_VERSION` dans `sim/constants.py`,
et rend incompatibles les modèles entraînés sous la version précédente.

---

## 2. Le ring et le temps

| Paramètre | Valeur | Constante |
|---|---|---|
| Forme | Carré, 8 × 8 unités | `RING_SIZE = 8.0` |
| Bords | Murs pleins, aucun obstacle interne | — |
| Fréquence logique | 30 ticks par seconde | `TICKS_PER_SECOND = 30` |
| Durée d'un round | 450 ticks, soit 15 secondes | `MAX_TICKS = 450` |

**Pourquoi un ring carré.** Les coins créent des situations d'acculement :
un boxeur poussé dans un angle voit ses options de fuite réduites. C'est une
mécanique tactique gratuite, absente d'une cage ronde. La distance au mur le
plus proche fait partie des observations précisément pour que l'IA puisse
l'apprendre.

**Pourquoi 30 ticks/s et pas 60.** La simulation coûte deux fois moins cher,
donc les entraînements vont deux fois plus vite. 33 ms de résolution
temporelle restent largement suffisants : la phase active d'un coup dure
2 ticks, ce qui laisse une fenêtre de riposte lisible. Le rendu, lui, tourne
à 60 FPS et interpole entre deux ticks.

**Pourquoi 15 secondes.** Un KO demande au minimum 7 coups propres, soit
140 ticks — environ 4,7 secondes. 450 ticks laissent donc plus de trois fois
la marge nécessaire. Allonger la durée multiplierait directement le coût de
chaque génération sans rien apporter à l'apprentissage.

---

## 3. Le boxeur

Les deux boxeurs sont strictement identiques et démarrent en position
symétrique.

| Paramètre | Valeur | Constante |
|---|---|---|
| Points de vie | 100 | `MAX_HP = 100.0` |
| Rayon du corps | 0,4 unité | `BODY_RADIUS = 0.4` |
| Écart minimal entre les corps | 0,8 unité | `MIN_SEPARATION = 0.8` |
| Vitesse | 0,12 unité par tick (3,6 u/s) | `MOVE_SPEED = 0.12` |
| Distance de départ | 3,0 unités, centrée dans le ring | `START_DISTANCE = 3.0` |

**Déplacement.** Huit directions, vitesse identique dans toutes (les
diagonales sont normalisées). Aucune inertie : un changement de direction est
instantané.

**Collision.** Si les deux corps se chevauchent après déplacement, chacun est
repoussé de la moitié du chevauchement. La résolution est symétrique : aucun
des deux boxeurs n'a la priorité.

**Symétrie stricte.** Aucune asymétrie entre les deux camps, ni dans les
stats, ni dans les positions de départ, ni dans l'ordre de résolution. C'est
ce qui permet à un seul réseau de jouer les deux côtés — et c'est vérifié par
un test dédié.

---

## 4. Le coup

La v1 ne contient qu'un seul coup. Il se déroule en quatre phases
consécutives, pour un cycle total de 20 ticks (0,67 seconde).

| Phase | Durée | Mobile ? | Peut frapper ? | Effet |
|---|---|---|---|---|
| Armement | 5 ticks | Non | Non | Aucun — le coup est visible et annoncé |
| Active | 2 ticks | Non | Non | Les dégâts s'appliquent si l'adversaire est à portée |
| Récupération | 8 ticks | Non | Non | Aucun — le boxeur reste exposé |
| Recharge | 5 ticks | **Oui** | Non | Aucun |

| Paramètre | Valeur | Constante |
|---|---|---|
| Portée | 1,4 unité entre les centres | `PUNCH_RANGE = 1.4` |
| Dégâts | 15 points | `PUNCH_DAMAGE = 15.0` |
| Cycle complet | 20 ticks | `PUNCH_CYCLE = 20` |

**Une action de déplacement demandée pendant les phases d'armement, active ou
de récupération est ignorée.** Une demande de frappe pendant un cycle déjà en
cours est ignorée également.

### Pourquoi le coup immobilise

C'est la seule mécanique qui rend ce jeu apprenable, et donc la règle la plus
importante du document.

Sans immobilisation, frapper ne coûte rien : la stratégie optimale serait de
foncer au contact et de frapper en boucle. Les deux IA convergeraient vers ce
comportement, les combats se joueraient au hasard des positions de départ, et
il n'y aurait rien à observer.

L'immobilisation crée un **engagement** : frapper, c'est parier 15 ticks
d'immobilité sur le fait que l'adversaire sera à portée au tick 6. Ce pari
peut être perdu, et il est punissable.

De cette seule règle découlent, sans qu'aucune ne soit codée :

- le maintien de distance — rester juste hors de portée est sûr
- la punition du coup manqué — 8 ticks de récupération sont une invitation
- le recul pendant la récupération adverse, puis le retour pour frapper
- la feinte — provoquer un coup dans le vide pour créer l'ouverture

Ces comportements ne sont pas programmés. Ils sont les conséquences logiques
de l'engagement, et c'est à l'évolution de les découvrir.

### Le rôle de l'armement

Les 5 ticks d'armement rendent le coup **lisible** : pendant 167 ms,
l'adversaire peut voir qu'une attaque arrive et réagir. Sans cette fenêtre,
esquiver serait impossible et le jeu se réduirait à un échange de dégâts.

C'est cette information que portent les entrées d'observation « menace
adverse » et « progression d'attaque adverse ».

### Le rôle de la recharge

Les 5 ticks de recharge sont le seul moment du cycle où le boxeur est mobile
sans pouvoir frapper. C'est ce qui rend possible un rythme
frapper / se dégager / revenir, caractéristique de la boxe. Sans cette phase,
le jeu deviendrait plus statique.

---

## 5. Score et fin de match

### Marquer

Un coup dont la phase active trouve l'adversaire à portée inflige 15 points de
dégâts et rapporte **1 point de touche**. Un coup qui n'atteint personne ne
rapporte rien.

### Fin du match

| Condition | Résultat |
|---|---|
| PV d'un boxeur ≤ 0 | KO — l'autre gagne |
| Les deux à 0 au même tick | Double KO — match nul |
| `tick >= MAX_TICKS` sans KO | Victoire au plus grand nombre de touches |
| Temps écoulé, touches égales | Match nul |

Le KO survient mécaniquement après 7 coups propres encaissés
(7 × 15 = 105 > 100).

### Pourquoi la victoire aux touches et non aux PV restants

Déclarer vainqueur celui qui a le plus de PV au temps écoulé créerait une
stratégie dominante : prendre l'avantage tôt, puis fuir pendant le reste du
round. Cette stratégie gagne, l'évolution la trouverait en une centaine de
générations, et les combats deviendraient des courses-poursuites.

Compter les touches inverse l'incitation : marquer exige de frapper, donc
d'entrer à portée, donc de s'exposer. Fuir ne rapporte jamais rien. La
condition de victoire pousse d'elle-même vers l'engagement, sans qu'aucune
règle n'ait besoin de l'imposer.

### Conséquence sur les métriques

Cette règle rend le match nul quasi impossible : deux IA n'auront pratiquement
jamais le même nombre exact de touches. Le taux de nuls ne peut donc pas servir
d'indicateur de santé de l'apprentissage.

L'indicateur à suivre est le **nombre moyen de touches par combat**. Proche de
zéro à la génération 1, il doit monter dès que l'IA apprend à engager. S'il
stagne, le problème est dans la fonction de fitness.

### Pourquoi les coups bloqués ne marqueront pas (v2)

Quand la garde sera introduite, un coup bloqué ne rapportera **aucune touche**
à l'attaquant.

Si un coup bloqué rapportait ne serait-ce qu'une fraction de point, attaquer
serait toujours rentable et bloquer ne ferait que retarder l'échéance sans
jamais faire gagner. La garde serait codée mais jamais utilisée. Une mécanique
n'existe que si le score la récompense.

---

## 6. Ce que la v1 ne contient pas

Cette section est un engagement. Chaque mécanique listée ci-dessous a été
volontairement écartée de la v1, pour une raison précise. Y revenir avant sa
version cible n'est pas une amélioration : c'est une régression
méthodologique.

**Le principe d'ordonnancement :** une mécanique ne s'apprend que si la
précédente est maîtrisée. Bloquer n'a aucun sens tant que l'IA ne sait pas
toucher. Choisir entre deux coups n'a aucun sens tant qu'aucun arbitrage ne
rend ce choix dépendant de la situation.

| Mécanique | Version | Raison du report |
|---|---|---|
| Garde | v2 | Sans capacité à toucher, il n'y a rien à bloquer. Doit avoir un coût (mobilité réduite), sinon garder en permanence devient dominant. |
| Coup de pied | v3 | Un second coup n'a de valeur que si le choix dépend de la situation. C'est la garde qui crée cet arbitrage : coup lent contre une garde, coup rapide contre un adversaire mobile. Sans elle, l'IA n'utiliserait que le meilleur des deux en moyenne. |
| Endurance | v4 | Demande un répertoire d'actions déjà riche pour que gérer son rythme soit une compétence. |
| Rounds multiples | v5 | Sans endurance, rien ne traverse un round : trois rounds seraient trois combats indépendants dont l'IA n'aurait rien à apprendre. |
| Esquive | v6 | Non atteignable par hasard depuis un comportement aléatoire — une action précise dans une fenêtre de 2 ticks n'arrivera jamais spontanément, donc ne sera jamais sélectionnée. Nécessitera une fenêtre élargie puis resserrée au fil des générations. |

### La règle qui gouverne cet ordre

Une mécanique n'est apprenable que si elle remplit deux conditions :

1. **être atteignable par hasard** depuis le comportement actuel de la
   population ;
2. **payer immédiatement**, dès la première fois où elle survient.

Si l'une des deux manque, l'évolution ne la découvrira jamais et la mécanique
restera du code mort. C'est ce critère, et non la complexité d'implémentation,
qui a déterminé l'ordre ci-dessus.

---

## 7. Décisions de méthode

**Entraîner sur un round, montrer trois rounds.** L'entraînement se fait sur
un round de 450 ticks. Les démonstrations et les vidéos utilisent le format
complet de trois rounds.

Cette séparation est valide tant qu'aucun état ne traverse les rounds : sans
endurance, un boxeur entame le round 2 exactement comme il entamait le
round 1. Le comportement appris sur un round se transfère donc intégralement.

Elle cessera d'être valide en v4 : dès que l'endurance existera, gérer son
rythme sur trois rounds deviendra une compétence à part entière, et
l'entraînement devra porter sur le match complet.

**Coût.** Entraîner sur trois minutes plutôt que quinze secondes multiplierait
par douze le coût de chaque génération. En phase exploratoire, ce qui limite
la progression n'est pas la puissance de calcul mais le nombre d'allers-retours
possibles par jour.