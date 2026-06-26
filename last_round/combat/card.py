"""
card.py
Last Round – Combat Prototype v0.1
Spec: Technical Combat Specification v0.2
"""

from dataclasses import dataclass, field
from typing import Optional


# Range modifier table (spec §6)
# Keys: "LONG" | "MID" | "CLOSE"
# Values: float multiplier, or None = Disabled
RANGE_MODIFIERS: dict[str, dict[str, Optional[float]]] = {
    "Straight Kick":  {"LONG": 1.0, "MID": 0.75, "CLOSE": None},
    "Front Kick":     {"LONG": 1.0, "MID": 1.0,  "CLOSE": None},
    "Reverse Punch":  {"LONG": 0.75,"MID": 1.0,  "CLOSE": 1.0},
    "Roundhouse":     {"LONG": 1.0, "MID": 1.0,  "CLOSE": None},
    "Jab":            {"LONG": None,"MID": 1.0,  "CLOSE": 1.0},
    "Cross":          {"LONG": None,"MID": 1.0,  "CLOSE": 1.0},
    "Hook":           {"LONG": None,"MID": 0.75, "CLOSE": 1.0},
    "Body Shot":      {"LONG": None,"MID": 1.0,  "CLOSE": 1.0},
    "Haymaker":       {"LONG": None,"MID": 1.0,  "CLOSE": 1.0},

    # Muay Thai
    "Teep":           {"LONG": 0.75, "MID": 1.0,  "CLOSE": 1.0 },
    "Leg Kick":       {"LONG": 0.75, "MID": 1.0,  "CLOSE": 1.0 },
    "High Kick":      {"LONG": 1.0,  "MID": 1.0,  "CLOSE": None},
    "Elbow":          {"LONG": None, "MID": 0.5,  "CLOSE": 1.0 },
    "Knee":           {"LONG": None, "MID": 1.0,  "CLOSE": 1.0 },

    # Capoeira
    "Meia Lua":       {"LONG": 1.0,  "MID": 1.0,  "CLOSE": None},
    "Martelo":        {"LONG": None, "MID": 1.0,  "CLOSE": 1.0 },
    "Armada":         {"LONG": 1.0,  "MID": 1.0,  "CLOSE": None},
    "Joana":          {"LONG": 0.75, "MID": 1.0,  "CLOSE": 1.0 },

    # Wrestler
    "Overhand":       {"LONG": None, "MID": 1.0,  "CLOSE": 1.0 },
    "Takedown":       {"LONG": None, "MID": None, "CLOSE": 1.0 },
    "Slam":           {"LONG": None, "MID": None, "CLOSE": 1.0 },
    "Double Leg":     {"LONG": None, "MID": 0.5,  "CLOSE": 1.0 },
}

# Momentum tier multipliers (spec §7)
MOMENTUM_TIERS = [
    (100, 1.4),
    (75,  1.3),
    (50,  1.2),
    (25,  1.1),
    (0,   1.0),
]


def get_momentum_modifier(momentum: int) -> float:
    for threshold, multiplier in MOMENTUM_TIERS:
        if momentum >= threshold:
            return multiplier
    return 1.0


@dataclass
class Card:
    """
    Represents one combat card.
    Cards are stateless — they describe what happens, not the game state.
    Resolution is handled by combat_manager.py.
    """

    name:            str
    stamina_cost:    int
    damage:          int            = 0
    balance_damage:  int            = 0
    stamina_damage:  int            = 0   # Body Shot stamina drain
    momentum_gain:   int            = 0
    is_heavy:        bool           = False   # Roundhouse / Haymaker

    # Behavioural flags
    is_block:        bool           = False
    is_dodge:        bool           = False
    is_recover:      bool           = False   # Restore stamina
    is_brace:        bool           = False   # Restore balance
    is_focus:        bool           = False   # Gain momentum, no attack
    is_movement:     bool           = False   # Step In / Retreat / Pressure Forward
    move_direction:  int            = 0       # +1 = closer, -1 = farther
    push_target:     bool           = False   # Front Kick pushes opponent back

    def is_attack(self) -> bool:
        return self.damage > 0

    def is_available_at_range(self, current_range: str) -> bool:
        """Returns False if the card is Disabled at this range."""
        if self.name not in RANGE_MODIFIERS:
            return True   # Non-attack cards (Block, Recover, etc.) always available
        return RANGE_MODIFIERS[self.name].get(current_range) is not None

    def range_modifier(self, current_range: str) -> float:
        if self.name not in RANGE_MODIFIERS:
            return 1.0
        mod = RANGE_MODIFIERS[self.name].get(current_range)
        return mod if mod is not None else 0.0

    def final_damage(self, current_range: str, momentum: int) -> int:
        """
        Final Damage = Base Damage × Range Modifier × Momentum Modifier
        Rounded down. (spec §7)
        """
        if not self.is_attack():
            return 0
        raw = self.damage * self.range_modifier(current_range) * get_momentum_modifier(momentum)
        return int(raw)   # floor

    def __repr__(self) -> str:
        return (
            f"[{self.name}] STA:{self.stamina_cost}  "
            f"DMG:{self.damage}  BAL:{self.balance_damage}  "
            f"MOM:+{self.momentum_gain}"
        )


# ── Card Definitions ──────────────────────────────────────────────────────────

# Karate (player) cards
KARATE_CARDS: list[Card] = [
    Card("Straight Kick",  stamina_cost=15, damage=12, momentum_gain=5),
    Card("Front Kick",     stamina_cost=10, damage=8,  momentum_gain=5,  push_target=True),
    Card("Reverse Punch",  stamina_cost=12, damage=10, momentum_gain=5),
    Card("Roundhouse",     stamina_cost=30, damage=20, balance_damage=15, momentum_gain=10, is_heavy=True),
    Card("Block",          stamina_cost=0,  is_block=True),
    Card("Sidestep",       stamina_cost=10, is_dodge=True,   momentum_gain=10),
    Card("Focus",          stamina_cost=0,  is_focus=True,   momentum_gain=20),
    Card("Recover",        stamina_cost=0,  is_recover=True),
    Card("Step In",        stamina_cost=5,  is_movement=True, move_direction=1,  momentum_gain=5),
    Card("Retreat",        stamina_cost=5,  is_movement=True, move_direction=-1),
    Card("Brace",          stamina_cost=10, is_brace=True),
]

# Boxer (AI) cards
BOXER_CARDS: list[Card] = [
    Card("Jab",              stamina_cost=8,  damage=8,  momentum_gain=5),
    Card("Cross",            stamina_cost=12, damage=12, momentum_gain=5),
    Card("Hook",             stamina_cost=18, damage=15, momentum_gain=5),
    Card("Body Shot",        stamina_cost=12, damage=8,  stamina_damage=10, momentum_gain=5),
    Card("Guard",            stamina_cost=0,  is_block=True),
    Card("Slip",             stamina_cost=10, is_dodge=True, momentum_gain=10),
    Card("Recover",          stamina_cost=0,  is_recover=True),
    Card("Pressure Forward", stamina_cost=5,  is_movement=True, move_direction=1, momentum_gain=5),
    Card("Haymaker",         stamina_cost=35, damage=25, balance_damage=10, momentum_gain=10, is_heavy=True),
    Card("Brace",            stamina_cost=10, is_brace=True),
]

# Muay Thai cards
MUAY_THAI_CARDS: list[Card] = [
    Card("Teep",      stamina_cost=10, damage=8,  momentum_gain=5,  push_target=True),
    Card("Leg Kick",  stamina_cost=12, damage=8,  balance_damage=10, momentum_gain=5),
    Card("High Kick", stamina_cost=15, damage=12, momentum_gain=5),
    Card("Elbow",     stamina_cost=18, damage=16, momentum_gain=8,  is_heavy=True),
    Card("Knee",      stamina_cost=16, damage=14, balance_damage=8,  momentum_gain=8),
    Card("Clinch",    stamina_cost=5,  is_movement=True, move_direction=1,  momentum_gain=5),
    Card("Block",     stamina_cost=0,  is_block=True),
    Card("Slip",      stamina_cost=10, is_dodge=True, momentum_gain=10),
    Card("Recover",   stamina_cost=0,  is_recover=True),
    Card("Step Back", stamina_cost=5,  is_movement=True, move_direction=-1),
    Card("Brace",     stamina_cost=10, is_brace=True),
]

# Capoeira cards
CAPOEIRA_CARDS: list[Card] = [
    Card("Ginga",      stamina_cost=0,  is_dodge=True,    momentum_gain=15),
    Card("Au",         stamina_cost=10, is_dodge=True,    momentum_gain=20),
    Card("Meia Lua",   stamina_cost=14, damage=11, balance_damage=8,  momentum_gain=8),
    Card("Martelo",    stamina_cost=12, damage=10, momentum_gain=6),
    Card("Armada",     stamina_cost=22, damage=18, momentum_gain=12, is_heavy=True),
    Card("Joana",      stamina_cost=8,  damage=7,  momentum_gain=5,  push_target=True),
    Card("Ginga Step", stamina_cost=5,  is_movement=True, move_direction=-1, momentum_gain=8),
    Card("Step In",    stamina_cost=5,  is_movement=True, move_direction=1,  momentum_gain=5),
    Card("Recover",    stamina_cost=0,  is_recover=True),
    Card("Brace",      stamina_cost=10, is_brace=True),
    Card("Block",      stamina_cost=0,  is_block=True),
]

# Wrestler cards
WRESTLER_CARDS: list[Card] = [
    Card("Jab",         stamina_cost=8,  damage=7,  momentum_gain=4),
    Card("Overhand",    stamina_cost=14, damage=14, momentum_gain=5),
    Card("Clinch Grab", stamina_cost=5,  is_movement=True, move_direction=1, momentum_gain=5),
    Card("Takedown",    stamina_cost=20, damage=8,  balance_damage=20, momentum_gain=10, is_heavy=True),
    Card("Slam",        stamina_cost=25, damage=20, balance_damage=12, momentum_gain=10, is_heavy=True),
    Card("Double Leg",  stamina_cost=16, damage=6,  balance_damage=16, momentum_gain=8),
    Card("Sprawl",      stamina_cost=0,  is_block=True),
    Card("Shoot",       stamina_cost=10, is_dodge=True, momentum_gain=10),
    Card("Recover",     stamina_cost=0,  is_recover=True),
    Card("Brace",       stamina_cost=10, is_brace=True),
    Card("Retreat",     stamina_cost=5,  is_movement=True, move_direction=-1),
]

# Lookup dicts
KARATE_CARD_MAP:    dict[str, Card] = {c.name: c for c in KARATE_CARDS}
BOXER_CARD_MAP:     dict[str, Card] = {c.name: c for c in BOXER_CARDS}
MUAY_THAI_CARD_MAP: dict[str, Card] = {c.name: c for c in MUAY_THAI_CARDS}
CAPOEIRA_CARD_MAP:  dict[str, Card] = {c.name: c for c in CAPOEIRA_CARDS}
WRESTLER_CARD_MAP:  dict[str, Card] = {c.name: c for c in WRESTLER_CARDS}

# Style → card map (used by CombatManager for player card dispatch)
STYLE_CARD_MAP: dict[str, dict[str, "Card"]] = {
    "KARATE":    KARATE_CARD_MAP,
    "BOXER":     BOXER_CARD_MAP,
    "MUAY_THAI": MUAY_THAI_CARD_MAP,
    "CAPOEIRA":  CAPOEIRA_CARD_MAP,
    "WRESTLER":  WRESTLER_CARD_MAP,
}
