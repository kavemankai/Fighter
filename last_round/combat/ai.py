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
    """
    Returns the Card the Boxer will play this turn.
    Evaluates priorities top-to-bottom and takes the first applicable action.
    (spec §15)
    """
    from card import BOXER_CARD_MAP

    def can_use(name: str) -> bool:
        card = BOXER_CARD_MAP[name]
        return (
            boxer.can_afford(card.stamina_cost)
            and card.is_available_at_range(manager.current_range)
        )

    # Priority 1 – Staggered response (v0.2: explicit conditional)
    if boxer.staggered:
        if can_use("Brace"):
            return BOXER_CARD_MAP["Brace"]
        return BOXER_CARD_MAP["Guard"]

    # Priority 2 – Stamina critical
    if boxer.stamina < 20:
        return BOXER_CARD_MAP["Recover"]

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
        # Weight: Jab appears twice to feel like a boxer's bread-and-butter
        weights = []
        for card in attack_pool:
            weights.append(2 if card.name == "Jab" else 1)
        return random.choices(attack_pool, weights=weights, k=1)[0]

    # Priority 7 – Fallback guard
    return BOXER_CARD_MAP["Guard"]
