# Last Round — Combat Prototype

One-on-one card-combat encounter (Ren'Py visual novel). Currently: combat logic
only, text-mode test harness, Ren'Py screen scaffolding. No metagame or story.

## Stack
- Python 3.10+  (combat engine — no pip dependencies)
- Ren'Py 8.x    (UI layer — screen language + ATL)
- Branch: claude/new-session-leqm8x
- PR: https://github.com/kavemankai/Fighter/pull/1

## Structure
```
last_round/
├── combat/
│   ├── fighter.py         # Stat container, clamped mutators, stagger/regen
│   ├── card.py            # Card dataclass, range table, damage formula
│   ├── combat_manager.py  # Turn resolution; only file that mutates state
│   └── ai.py              # 7-priority Boxer decision tree (spec §15)
├── game/
│   └── fight_test.py      # Standalone text-mode loop — run this to playtest
└── screens/
    └── combat_screen.rpy  # Full Ren'Py UI (placeholder assets, all logic wired)
```

## Run
```bash
cd last_round/game && python fight_test.py
# Controls: number key to pick a card, q to quit
```

## Test
No formal test suite yet. Smoke test:
```bash
cd /home/user/Fighter && python -c "
import sys; sys.path.insert(0, 'last_round/combat')
from fighter import Fighter
from combat_manager import CombatManager
from card import KARATE_CARD_MAP
p = Fighter('P', 'KARATE'); b = Fighter('B', 'BOXER')
m = CombatManager(p, b)
for _ in range(3):
    m.player_turn(KARATE_CARD_MAP['Reverse Punch'])
    m.ai_turn()
    m.end_round()
assert p.hp < 100 and b.hp < 100
print('OK')
"
```

## Key rules (for review/qa context)
- `combat_manager.py` is the **only** file that mutates fighter state — cards and fighters are stateless data
- Damage formula: `floor(base × range_modifier × momentum_modifier)`
- Momentum tiers: 0→1.0×, 25→1.1×, 50→1.2×, 75→1.3×, 100→1.4×
- Stagger: balance ≤ 0 → `staggered = True`, balance reset to 15 next round
- Simultaneous KO → player wins (both resolve to 0 HP same round; player action always resolved first, so player's KO is applied before opponent's, and `winner()` checks opponent first)
- Block halves both HP damage and balance damage (floor each)
- Dodge: no damage to defender; attacker still gains card momentum; dodger gains +10 momentum
- Front Kick `push_target` pushes defender back one range step even on a successful dodge; disabled at CLOSE (was 0.5× = 4dmg, not worth a hand slot)
- Recover locked for 1 round after use (`recover_cooldown = 2`, decremented each `end_round`) — prevents zero-cost stall loops
- Balance regen: +1/round (not +3). At +3, Roundhouse pressure (−15 BAL every 2 rounds) nets only −9 balance per cycle; stagger never triggers before KO. At +1, stagger lands at round 7 with HP=18 still alive.

## Card catalogue

### Player (Karate Fighter)
| Card | STA | DMG | BAL DMG | MOM+ | Notes |
|---|---|---|---|---|---|
| Straight Kick | 15 | 12 | — | +5 | LONG/MID only |
| Front Kick | 10 | 8 | — | +5 | Pushes target back; LONG/MID only |
| Reverse Punch | 12 | 10 | — | +5 | Best at MID/CLOSE |
| Roundhouse | 30 | 20 | 15 | +10 | Heavy; LONG/MID only |
| Block | 0 | — | — | — | Halves incoming damage |
| Sidestep | 10 | — | — | +10 | Dodge |
| Focus | 0 | — | — | +20 | Momentum only |
| Recover | 0 | — | — | — | +25 STA; 1-round cooldown after use |
| Step In | 5 | — | — | +5 | Move closer |
| Retreat | 5 | — | — | — | Move back |
| Brace | 10 | — | — | — | +25 BAL |

### Boxer AI (7-priority tree)
1. Staggered → Brace / Guard
2. STA < 20 → Recover
3. Range == LONG → Pressure Forward
4. Momentum > 50 → Haymaker
5. Player balance < 15 → Hook
6. Default → Jab (2×) / Cross / Body Shot (random weighted)
7. Fallback → Guard

## Open / watch
- Roundhouse at 30 STA cost may lock player out; consider reducing to 25 if it feels inaccessible
- **Body Shot combo (intentional)**: 2–3 early Body Shots → player burns Recover turns → Boxer gains momentum → Haymaker. This is a valid pressure loop. If it feels oppressive, cap stamina damage or add diminishing returns.
- **Simultaneous KO UI**: the "player wins on draw" rule is invisible. Consider a "DRAW → YOU WIN" banner in Ren'Py (`combat_screen.rpy`) to surface the decision visually.
- No real image/audio assets yet (all `Solid()` placeholders in `combat_screen.rpy`)
- `combat_screen.rpy` targets 1280×720; fighter sprites at xpos 160 (player) and 940 (boxer)
