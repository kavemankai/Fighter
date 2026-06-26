"""
combat_manager.py
Last Round – Combat Prototype v0.1
Spec: Technical Combat Specification v0.2

This is the only system that owns combat state.
Everything resolves through here — no card or fighter modifies state directly.

Turn sequence (spec §3):
  1. Player selects card
  2. Player card resolves
  3. Check KO
  4. AI selects action
  5. AI action resolves
  6. Check KO
  7. Regeneration phase
  8. Clear temporary effects
  9. Start next round
"""

from __future__ import annotations
from typing import Optional
from fighter import Fighter
from card import Card, KARATE_CARD_MAP, BOXER_CARD_MAP, STYLE_CARD_MAP, get_momentum_modifier
import ai


# Range index helpers
_RANGE_ORDER = ["LONG", "MID", "CLOSE"]


def _range_index(r: str) -> int:
    return _RANGE_ORDER.index(r)


def _range_at(idx: int) -> str:
    return _RANGE_ORDER[max(0, min(2, idx))]


class CombatResult:
    """Carries the outcome of one card resolution for display/logging."""

    def __init__(self):
        self.actor:          str = ""
        self.card_name:      str = ""
        self.damage_dealt:   int = 0
        self.balance_dealt:  int = 0
        self.stamina_dealt:  int = 0
        self.dodged:         bool = False
        self.blocked:        bool = False
        self.stagger_caused: bool = False
        self.range_changed:  bool = False
        self.new_range:      str = ""
        self.messages:       list[str] = []

    def log(self, msg: str):
        self.messages.append(msg)

    def summary(self) -> str:
        return "\n".join(self.messages)


class CombatManager:
    """
    Owns all combat state and orchestrates the turn sequence.
    Ren'Py integration: call player_turn() with a Card, then ai_turn(),
    then end_round(). Check is_over() after each turn step.
    """

    def __init__(self, player: Fighter, boxer: Fighter):
        self.player = player
        self.boxer  = boxer

        # Shared range (spec §5)
        self.current_range: str = "MID"
        self._sync_ranges()

        self.round_number: int = 1
        self.log: list[str] = []

        # Round result cache (for UI display)
        self.last_player_result: Optional[CombatResult] = None
        self.last_ai_result:     Optional[CombatResult] = None

    # ── Public API ─────────────────────────────────────────────────────────

    def player_turn(self, card: Card) -> CombatResult:
        """Step 1–3: Resolve player card, check KO."""
        result = self._resolve_card(card, attacker=self.player, defender=self.boxer)
        self.last_player_result = result
        self._log(f"Round {self.round_number} | Player: {card.name}")
        self._log(result.summary())
        return result

    def ai_turn(self) -> CombatResult:
        """Step 4–6: AI chooses and resolves its card, check KO."""
        card = ai.choose_action(self.boxer, self.player, self)
        result = self._resolve_card(card, attacker=self.boxer, defender=self.player)
        self.last_ai_result = result
        self._log(f"Round {self.round_number} | Boxer: {card.name}")
        self._log(result.summary())
        return result

    def end_round(self):
        """Steps 7–8: Regeneration + clear effects."""
        self.player.regenerate()
        self.boxer.regenerate()
        self.player.clear_round_effects()
        self.boxer.clear_round_effects()
        self.round_number += 1
        self._log(f"--- End of round {self.round_number - 1} ---")

    def is_over(self) -> bool:
        return self.player.is_ko() or self.boxer.is_ko()

    def winner(self) -> Optional[str]:
        """Returns 'player', 'boxer', or None if match is ongoing."""
        if self.player.is_ko() and self.boxer.is_ko():
            return "player"   # Simultaneous KO: player action resolved first (spec §16)
        if self.boxer.is_ko():
            return "player"
        if self.player.is_ko():
            return "boxer"
        return None

    def _player_card_map(self) -> dict:
        return STYLE_CARD_MAP.get(self.player.style, KARATE_CARD_MAP)

    def available_player_cards(self) -> list[Card]:
        """
        Returns all player cards that can be used this turn.
        Greyed-out logic: disabled at range OR insufficient stamina.
        """
        return [
            c for c in self._player_card_map().values()
            if c.is_available_at_range(self.current_range)
            and self.player.can_afford(c.stamina_cost)
            and (not c.is_recover or self.player.recover_cooldown == 0)
        ]

    def all_player_cards(self) -> list[Card]:
        """All player cards including disabled ones (for UI rendering)."""
        return list(self._player_card_map().values())

    def card_disabled_reason(self, card: Card) -> Optional[str]:
        """Returns a human-readable reason a card is unavailable, or None."""
        if not card.is_available_at_range(self.current_range):
            return f"Disabled at {self.current_range}"
        if not self.player.can_afford(card.stamina_cost):
            return f"Need {card.stamina_cost} stamina (have {self.player.stamina})"
        if card.is_recover and self.player.recover_cooldown > 0:
            return f"Recover on cooldown ({self.player.recover_cooldown} round{'s' if self.player.recover_cooldown > 1 else ''})"
        return None

    # ── Resolution ──────────────────────────────────────────────────────────

    def _resolve_card(self, card: Card, attacker: Fighter, defender: Fighter) -> CombatResult:
        result = CombatResult()
        result.actor     = attacker.name
        result.card_name = card.name

        # Spend stamina
        attacker.spend_stamina(card.stamina_cost)

        # ── Movement cards ──────────────────────────────────────────
        if card.is_movement:
            old_range = self.current_range
            new_idx = _range_index(self.current_range) + card.move_direction
            new_idx = max(0, min(2, new_idx))
            self.current_range = _range_at(new_idx)
            self._sync_ranges()

            if self.current_range != old_range:
                result.range_changed = True
                result.new_range     = self.current_range
                result.log(f"{attacker.name} moves → {self.current_range}")
            else:
                result.log(f"{attacker.name} is already at {self.current_range}")

            if card.momentum_gain:
                attacker.gain_momentum(card.momentum_gain)
                result.log(f"{attacker.name} gains {card.momentum_gain} Momentum ({attacker.momentum})")
            return result

        # ── Block / Guard ────────────────────────────────────────────
        if card.is_block:
            attacker.blocking = True
            result.log(f"{attacker.name} takes a guard stance.")
            return result

        # ── Sidestep / Slip ──────────────────────────────────────────
        if card.is_dodge:
            attacker.dodging = True
            if card.momentum_gain:
                attacker.gain_momentum(card.momentum_gain)
                result.log(f"{attacker.name} Momentum → {attacker.momentum}")
            result.log(f"{attacker.name} prepares to slip the next attack.")
            return result

        # ── Recover (stamina) ────────────────────────────────────────
        if card.is_recover:
            attacker.restore_stamina(25)
            attacker.recover_cooldown = 2   # locked for next round
            result.log(f"{attacker.name} recovers. Stamina → {attacker.stamina}")
            return result

        # ── Brace (balance) ──────────────────────────────────────────
        if card.is_brace:
            attacker.restore_balance(25)
            result.log(f"{attacker.name} braces. Balance → {attacker.balance}")
            return result

        # ── Focus (momentum) ─────────────────────────────────────────
        if card.is_focus:
            attacker.gain_momentum(card.momentum_gain)
            result.log(f"{attacker.name} focuses. Momentum → {attacker.momentum}")
            return result

        # ── Attack ───────────────────────────────────────────────────
        if card.is_attack():
            # Dodge check — attacker still gains momentum (spec §12)
            if defender.dodging:
                result.dodged = True
                attacker.gain_momentum(card.momentum_gain)
                defender.gain_momentum(10)  # Dodger gains momentum on success (spec §8)
                result.log(f"{defender.name} dodges {card.name}!")
                result.log(f"{attacker.name} Momentum → {attacker.momentum}")
                result.log(f"{defender.name} Momentum → {defender.momentum}")

                # Range change from Front Kick still applies even when dodged (spec §12)
                if card.push_target:
                    self._push_target_back(attacker, defender, result)

                return result

            # Calculate damage
            hp_dmg = card.final_damage(self.current_range, attacker.momentum)

            # Block check
            if defender.blocking:
                result.blocked = True
                hp_dmg  = int(hp_dmg * 0.5)
                bal_dmg = int(card.balance_damage * 0.5)
                result.log(f"{defender.name} blocks!")
            else:
                bal_dmg = card.balance_damage

            # Apply HP damage
            defender.apply_hp_damage(hp_dmg)
            result.damage_dealt = hp_dmg
            result.log(f"{card.name}: {hp_dmg} damage → {defender.name} HP {defender.hp}")

            # Apply Balance damage
            if bal_dmg:
                defender.apply_balance_damage(bal_dmg)
                result.balance_dealt = bal_dmg
                result.log(f"  Balance damage: {bal_dmg} → {defender.name} Balance {defender.balance}")

                if defender.balance <= 0 and not defender.staggered:
                    defender.enter_stagger()
                    result.stagger_caused = True
                    # Attacker gains stagger momentum (spec §8)
                    attacker.gain_momentum(15)
                    result.log(f"  {defender.name} is STAGGERED! {attacker.name} +15 Momentum ({attacker.momentum})")

            # Apply Stamina damage (Body Shot)
            if card.stamina_damage:
                defender.apply_stamina_damage(card.stamina_damage)
                result.stamina_dealt = card.stamina_damage
                result.log(f"  Stamina damage: {card.stamina_damage} → {defender.name} Stamina {defender.stamina}")

            # Attacker momentum gain (spec §8) — always apply; stagger bonus additive
            attacker.gain_momentum(card.momentum_gain)
            result.log(f"  {attacker.name} Momentum → {attacker.momentum}")

            # Front Kick push (spec §12: push applies even on dodge, handled above)
            if card.push_target and not result.dodged:
                self._push_target_back(attacker, defender, result)

        return result

    # ── Internal helpers ───────────────────────────────────────────────────

    def _push_target_back(self, attacker: Fighter, defender: Fighter, result: CombatResult):
        """Move the range one step away from attacker (Front Kick effect)."""
        old_range = self.current_range
        new_idx = _range_index(self.current_range) - 1  # Push back = increase distance
        new_idx = max(0, min(2, new_idx))
        self.current_range = _range_at(new_idx)
        self._sync_ranges()

        if self.current_range != old_range:
            result.range_changed = True
            result.new_range     = self.current_range
            result.log(f"  {defender.name} pushed back → {self.current_range}")
        else:
            result.log(f"  {defender.name} already at maximum range.")

    def _sync_ranges(self):
        """Keep both fighter range references in sync with the shared range."""
        self.player.range = self.current_range
        self.boxer.range  = self.current_range

    def _log(self, msg: str):
        self.log.append(msg)

    # ── Debug state dump ──────────────────────────────────────────────────

    def state_summary(self) -> str:
        return (
            f"\n=== Round {self.round_number} | Range: {self.current_range} ===\n"
            f"{self.player}\n"
            f"{self.boxer}\n"
        )
