"""
fight_test.py
Last Round – Combat Prototype v0.1

Standalone text-mode combat loop.
Run this with plain Python to validate balance and logic
before attaching any Ren'Py UI.

Usage:
    python fight_test.py

Controls (type and press Enter):
    Number to select a card
    q to quit
"""

import sys
import os

# Allow imports from combat/ when running from game/ or project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "combat"))

from fighter import Fighter
from card import Card
from combat_manager import CombatManager


STYLES = ["KARATE", "MUAY_THAI", "CAPOEIRA", "WRESTLER", "BOXER"]


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def bar(value: int, maximum: int, width: int = 20, char: str = "█") -> str:
    filled = int((value / maximum) * width)
    return char * filled + "░" * (width - filled)


def pick_style(prompt: str) -> str:
    print(f"\n  {prompt}")
    for i, s in enumerate(STYLES, 1):
        print(f"  [{i}] {s}")
    while True:
        raw = input("  > ").strip()
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(STYLES):
                return STYLES[idx]
        except ValueError:
            pass
        print(f"  Enter a number 1–{len(STYLES)}")


def render_hud(manager: CombatManager):
    p = manager.player
    b = manager.boxer
    p_label = f"{p.style}"
    b_label = f"{b.style}"
    print(f"\n{'─' * 60}")
    print(f"  {p_label:<30} {b_label}")
    print(f"  HP  [{bar(p.hp, 100)}] {p.hp:>3}   [{bar(b.hp, 100)}] {b.hp:>3}")
    print(f"  STA [{bar(p.stamina, 100)}] {p.stamina:>3}   [{bar(b.stamina, 100)}] {b.stamina:>3}")
    print(f"  MOM [{bar(p.momentum, 100)}] {p.momentum:>3}   [{bar(b.momentum, 100)}] {b.momentum:>3}")
    print(f"  BAL [{bar(p.balance, 50, char='▪')}] {p.balance:>3}   [{bar(b.balance, 50, char='▪')}] {b.balance:>3}")

    flags_p = []
    if p.staggered: flags_p.append("STAGGERED")
    if p.blocking:  flags_p.append("BLOCKING")
    if p.dodging:   flags_p.append("DODGING")

    flags_b = []
    if b.staggered: flags_b.append("STAGGERED")

    if flags_p or flags_b:
        print(f"  {' '.join(flags_p) or '':30s}  {' '.join(flags_b) or ''}")

    print(f"\n  ── Range: {manager.current_range} ──")
    print(f"{'─' * 60}")


def render_cards(manager: CombatManager) -> list[Card]:
    all_cards = manager.all_player_cards()

    print("\n  Select a card:\n")
    selectable = []
    for card in all_cards:
        reason = manager.card_disabled_reason(card)
        idx = len(selectable) + 1 if not reason else " "
        if not reason:
            selectable.append(card)
            print(f"  [{idx}] {card.name:<20} STA:{card.stamina_cost:>2}  DMG:{card.damage:>2}  BAL:{card.balance_damage:>2}  MOM:+{card.momentum_gain}")
        else:
            print(f"  [ ] {card.name:<20} — {reason}")

    return selectable


def run_fight():
    p_style = pick_style("Choose YOUR style:")
    b_style = pick_style("Choose OPPONENT style:")

    player = Fighter("Fighter", p_style)
    boxer  = Fighter("Opponent", b_style)
    manager = CombatManager(player, boxer)

    print("\n  ══════════════════════════════════")
    print("        LAST ROUND — TEXT MODE")
    print("  ══════════════════════════════════")
    print(f"  {player.style}  vs  {boxer.style}")
    print("  Press Enter to begin...\n")
    input()

    while not manager.is_over():
        render_hud(manager)
        selectable = render_cards(manager)

        # Player input
        choice = None
        while choice is None:
            raw = input("\n  > ").strip().lower()
            if raw == "q":
                print("\n  Match abandoned.\n")
                return
            try:
                idx = int(raw) - 1
                if 0 <= idx < len(selectable):
                    choice = selectable[idx]
                else:
                    print(f"  Enter a number 1–{len(selectable)}")
            except ValueError:
                print("  Enter a number or 'q' to quit.")

        # Player turn
        p_result = manager.player_turn(choice)
        print(f"\n  ── PLAYER: {choice.name} ──")
        for msg in p_result.messages:
            print(f"  {msg}")

        if manager.is_over():
            break

        # AI turn
        ai_result = manager.ai_turn()
        print(f"\n  ── OPPONENT: {ai_result.card_name} ──")
        for msg in ai_result.messages:
            print(f"  {msg}")

        input("\n  [Enter for next round]")

        if not manager.is_over():
            manager.end_round()

    # Match over
    render_hud(manager)
    winner = manager.winner()
    print(f"\n{'═' * 60}")
    if winner == "player":
        print("  VICTORY — The opponent has been defeated.")
    else:
        print("  DEFEAT — You have been knocked out.")
    print(f"  Match lasted {manager.round_number - 1} rounds.")
    print(f"{'═' * 60}\n")


if __name__ == "__main__":
    run_fight()
