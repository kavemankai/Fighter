# Last Round — Combat Prototype

## Project Structure

```
last_round/
│
├── combat/
│   ├── fighter.py          # Fighter stats and state
│   ├── card.py             # Card definitions, range table, damage formula
│   ├── combat_manager.py   # Owns all combat state and resolution
│   └── ai.py               # Boxer AI priority tree (spec §15)
│
├── screens/
│   └── combat_screen.rpy   # (to be built — Ren'Py UI layer)
│
└── game/
    └── fight_test.py       # Text-mode combat loop (run this first)
```

## Running the Text Test

No dependencies beyond Python 3.10+.

```bash
cd game
python fight_test.py
```

Controls: type a number and press Enter to select a card. `q` to quit.

## Ren'Py Integration Notes

- Copy `combat/` into your Ren'Py `game/` directory.
- In Ren'Py, `game/` is on the Python path — imports work as-is.
- Build `combat_screen.rpy` as a `screen` that calls:
  - `manager.all_player_cards()` to render card buttons
  - `manager.card_disabled_reason(card)` for greyed-out state
  - `manager.player_turn(card)` on button press
  - `manager.ai_turn()` after player result resolves
  - `manager.end_round()` after AI result resolves
- `CombatResult.messages` gives you the text feed for the combat log UI.

## Spec Reference

See `LastRound_TechSpec_v0.2.docx` for all formulas, rules, and design decisions.

## Known Tuning Points (from simulation run)

- Roundhouse is hard to fire consistently due to stamina cost (30). This is intentional
  pressure but watch whether players feel locked out of it. If so, reduce to 25.
- Boxer Haymaker fires reliably at momentum > 50. In a 12-round match it landed once
  for 30 damage — appropriately punishing without being a fight-ender on its own.
- Stagger was not triggered in the sim. Balance damage needs a dedicated test with
  Roundhouse-heavy play. Target: 3–4 Roundhouses to stagger.
