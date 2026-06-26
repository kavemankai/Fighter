"""
ai.py
Last Round – Combat Prototype v0.1
Spec: Technical Combat Specification v0.2 §15

AI priority table implemented exactly as specified.
No magic numbers outside this file.
"""

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fighter import Fighter
    from card import Card
    from combat_manager import CombatManager


def choose_action(boxer: "Fighter", player: "Fighter", manager: "CombatManager") -> "Card":
    _dispatch = {
        "BOXER":     _choose_boxer,
        "MUAY_THAI": _choose_muay_thai,
        "CAPOEIRA":  _choose_capoeira,
        "WRESTLER":  _choose_wrestler,
    }
    return _dispatch.get(boxer.style, _choose_boxer)(boxer, player, manager)


def _choose_boxer(boxer: "Fighter", player: "Fighter", manager: "CombatManager") -> "Card":
    from card import BOXER_CARD_MAP

    def can_use(name: str) -> bool:
        card = BOXER_CARD_MAP[name]
        if card.is_recover and boxer.recover_cooldown > 0:
            return False
        return (
            boxer.can_afford(card.stamina_cost)
            and card.is_available_at_range(manager.current_range)
        )

    # Priority 1 – Staggered response
    if boxer.staggered:
        if can_use("Brace"):
            return BOXER_CARD_MAP["Brace"]
        return BOXER_CARD_MAP["Guard"]

    # Priority 2 – Stamina critical
    if boxer.stamina < 20 and can_use("Recover"):
        return BOXER_CARD_MAP["Recover"]
    elif boxer.stamina < 20:
        return BOXER_CARD_MAP["Guard"]

    # Priority 3 – Wrong range — push in
    if manager.current_range == "LONG":
        if can_use("Pressure Forward"):
            return BOXER_CARD_MAP["Pressure Forward"]

    # Priority 4 – Haymaker window
    if boxer.momentum > 50 and can_use("Haymaker"):
        return BOXER_CARD_MAP["Haymaker"]

    # Priority 5 – Player is staggered — exploit with Hook
    if player.balance < 15 and can_use("Hook"):
        return BOXER_CARD_MAP["Hook"]

    # Priority 6 – Default attack pool (random, weighted toward feel)
    attack_pool = []
    for name in ["Jab", "Cross", "Body Shot"]:
        if can_use(name):
            attack_pool.append(BOXER_CARD_MAP[name])

    if attack_pool:
        weights = [2 if card.name == "Jab" else 1 for card in attack_pool]
        return random.choices(attack_pool, weights=weights, k=1)[0]

    # Priority 7 – Fallback guard
    return BOXER_CARD_MAP["Guard"]


def _choose_muay_thai(boxer: "Fighter", player: "Fighter", manager: "CombatManager") -> "Card":
    from card import MUAY_THAI_CARD_MAP as C

    def can_use(name: str) -> bool:
        card = C[name]
        if card.is_recover and boxer.recover_cooldown > 0:
            return False
        return boxer.can_afford(card.stamina_cost) and card.is_available_at_range(manager.current_range)

    # Priority 1 – Staggered
    if boxer.staggered:
        return C["Brace"] if can_use("Brace") else C["Block"]

    # Priority 2 – Stamina critical
    if boxer.stamina < 20 and can_use("Recover"):
        return C["Recover"]
    elif boxer.stamina < 20:
        return C["Block"]

    # Priority 3 – Wrong range — close in
    if manager.current_range == "LONG":
        return C["Clinch"]

    # Priority 4 – Power window at CLOSE
    if boxer.momentum > 50:
        if can_use("Elbow"):
            return C["Elbow"]
        if can_use("Knee"):
            return C["Knee"]

    # Priority 5 – Erode player balance
    if player.balance < 20 and can_use("Knee"):
        return C["Knee"]

    # Priority 6 – Default: Leg Kick favoured (2×), then High Kick / Teep
    pool = [(C["Leg Kick"], 2), (C["High Kick"], 1), (C["Teep"], 1)]
    pool = [(c, w) for c, w in pool if can_use(c.name)]
    if pool:
        cards, weights = zip(*pool)
        return random.choices(cards, weights=list(weights), k=1)[0]

    # Priority 7 – Fallback
    return C["Block"]


def _choose_capoeira(boxer: "Fighter", player: "Fighter", manager: "CombatManager") -> "Card":
    from card import CAPOEIRA_CARD_MAP as C

    def can_use(name: str) -> bool:
        card = C[name]
        if card.is_recover and boxer.recover_cooldown > 0:
            return False
        return boxer.can_afford(card.stamina_cost) and card.is_available_at_range(manager.current_range)

    # Priority 1 – Staggered — Capoeira dodges out, not blocks
    if boxer.staggered:
        if can_use("Ginga"):
            return C["Ginga"]
        return C["Brace"] if can_use("Brace") else C["Block"]

    # Priority 2 – Stamina critical
    if boxer.stamina < 20 and can_use("Recover"):
        return C["Recover"]
    elif boxer.stamina < 20:
        return C["Block"]

    # Priority 3 – Retreat to preferred range (Capoeira likes space)
    if manager.current_range == "CLOSE" and can_use("Ginga Step"):
        return C["Ginga Step"]

    # Priority 4 – Armada window (high momentum + space)
    if boxer.momentum > 65 and can_use("Armada"):
        return C["Armada"]

    # Priority 5 – Balance damage follow-up
    if player.balance < 20 and can_use("Meia Lua"):
        return C["Meia Lua"]

    # Priority 6 – Default: Meia Lua (2×), Martelo, occasional Ginga for rhythm
    pool = [(C["Meia Lua"], 2), (C["Martelo"], 1), (C["Ginga"], 1)]
    pool = [(c, w) for c, w in pool if can_use(c.name)]
    if pool:
        cards, weights = zip(*pool)
        return random.choices(cards, weights=list(weights), k=1)[0]

    # Priority 7 – Fallback — Capoeira uses Ginga, not static block
    return C["Ginga"] if can_use("Ginga") else C["Block"]


def _choose_wrestler(boxer: "Fighter", player: "Fighter", manager: "CombatManager") -> "Card":
    from card import WRESTLER_CARD_MAP as C

    def can_use(name: str) -> bool:
        card = C[name]
        if card.is_recover and boxer.recover_cooldown > 0:
            return False
        return boxer.can_afford(card.stamina_cost) and card.is_available_at_range(manager.current_range)

    # Priority 1 – Staggered
    if boxer.staggered:
        return C["Brace"] if can_use("Brace") else C["Sprawl"]

    # Priority 2 – Stamina critical
    if boxer.stamina < 20 and can_use("Recover"):
        return C["Recover"]
    elif boxer.stamina < 20:
        return C["Sprawl"]

    # Priority 3+4 – Close the distance aggressively
    if manager.current_range in ("LONG", "MID") and can_use("Clinch Grab"):
        return C["Clinch Grab"]

    # Priority 5 – At CLOSE: power grapple window
    if manager.current_range == "CLOSE":
        if boxer.momentum > 40 and can_use("Slam"):
            return C["Slam"]
        pool = [(C["Takedown"], 2), (C["Double Leg"], 1)]
        pool = [(c, w) for c, w in pool if can_use(c.name)]
        if pool:
            cards, weights = zip(*pool)
            return random.choices(cards, weights=list(weights), k=1)[0]

    # Priority 6 – Not yet CLOSE — strike while closing
    pool = [(C["Overhand"], 1), (C["Jab"], 1)]
    pool = [(c, w) for c, w in pool if can_use(c.name)]
    if pool:
        cards, weights = zip(*pool)
        return random.choices(cards, weights=list(weights), k=1)[0]

    # Priority 7 – Fallback
    return C["Sprawl"]
