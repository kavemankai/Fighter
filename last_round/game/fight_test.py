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

# ── ANSI colour helpers ───────────────────────────────────────────────────
R       = "\033[0m"   # Reset
B       = "\033[1m"   # Bold
DIM     = "\033[2m"   # Dim

CYAN    = "\033[96m"  # Bright cyan    — player / dodge
RED     = "\033[91m"  # Bright red     — opponent / damage
GREEN   = "\033[92m"  # Bright green   — HP healthy / success
YELLOW  = "\033[93m"  # Bright yellow  — MOM / momentum messages
BLUE    = "\033[94m"  # Bright blue    — STA / stamina messages
MAGENTA = "\033[95m"  # Bright magenta — stagger
WHITE   = "\033[97m"  # Bright white   — neutral emphasis
AMBER   = "\033[33m"  # Amber          — BAL / balance messages

_FLAG_STYLE = {
    "STAGGERED": RED + B,
    "BLOCKING":  CYAN,
    "DODGING":   GREEN,
}


def hp_color(hp: int) -> str:
    if hp > 60: return GREEN
    if hp > 30: return YELLOW
    return RED


def fmt_flag(f: str) -> str:
    style = _FLAG_STYLE.get(f) or (YELLOW if f.startswith("REC") else WHITE)
    return style + f + R


def colorize_msg(msg: str) -> str:
    ml = msg.lower()
    if "staggered" in ml:                   return MAGENTA + B + msg + R
    if "dodges" in ml:                      return GREEN + msg + R
    if "blocks" in ml:                      return CYAN + msg + R
    if "damage" in ml and ("hp" in ml or "→" in ml and "hp" not in ml):
        return RED + msg + R
    if "balance damage" in ml:              return AMBER + msg + R
    if "stamina damage" in ml:             return BLUE + msg + R
    if "recovers" in ml:                   return BLUE + msg + R
    if "momentum" in ml:                   return YELLOW + msg + R
    if "pushed back" in ml or "moves →" in ml: return WHITE + msg + R
    return msg


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def bar(value: int, maximum: int, width: int = 20,
        char: str = "█", color: str = "") -> str:
    filled = int((value / maximum) * width)
    return color + char * filled + R + DIM + "░" * (width - filled) + R


def pick_style(prompt: str) -> str:
    print(f"\n  {WHITE}{prompt}{R}")
    for i, s in enumerate(STYLES, 1):
        print(f"  {DIM}[{R}{B}{i}{R}{DIM}]{R} {s}")
    while True:
        raw = input(f"  {DIM}>{R} ").strip()
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(STYLES):
                return STYLES[idx]
        except ValueError:
            pass
        print(f"  {DIM}Enter a number 1–{len(STYLES)}{R}")


def render_hud(manager: CombatManager):
    p = manager.player
    b = manager.boxer

    print(f"\n{DIM}{'─' * 60}{R}")
    print(f"  {CYAN}{B}{p.style:<30}{R}  {RED}{B}{b.style}{R}")

    print(f"  {DIM}HP {R} [{bar(p.hp,  100, color=hp_color(p.hp))}] {hp_color(p.hp)}{p.hp:>3}{R}   "
          f"[{bar(b.hp,  100, color=hp_color(b.hp))}] {hp_color(b.hp)}{b.hp:>3}{R}")
    print(f"  {DIM}STA{R} [{bar(p.stamina, 100, color=BLUE)}] {BLUE}{p.stamina:>3}{R}   "
          f"[{bar(b.stamina, 100, color=BLUE)}] {BLUE}{b.stamina:>3}{R}")
    print(f"  {DIM}MOM{R} [{bar(p.momentum, 100, color=YELLOW)}] {YELLOW}{p.momentum:>3}{R}   "
          f"[{bar(b.momentum, 100, color=YELLOW)}] {YELLOW}{b.momentum:>3}{R}")
    print(f"  {DIM}BAL{R} [{bar(p.balance, 50, char='▪', color=AMBER)}] {AMBER}{p.balance:>3}{R}   "
          f"[{bar(b.balance, 50, char='▪', color=AMBER)}] {AMBER}{b.balance:>3}{R}")

    flags_p = []
    if p.staggered:            flags_p.append(fmt_flag("STAGGERED"))
    if p.blocking:             flags_p.append(fmt_flag("BLOCKING"))
    if p.dodging:              flags_p.append(fmt_flag("DODGING"))
    if p.recover_cooldown > 0: flags_p.append(fmt_flag(f"REC({p.recover_cooldown})"))

    flags_b = []
    if b.staggered:            flags_b.append(fmt_flag("STAGGERED"))
    if b.blocking:             flags_b.append(fmt_flag("BLOCKING"))
    if b.dodging:              flags_b.append(fmt_flag("DODGING"))
    if b.recover_cooldown > 0: flags_b.append(fmt_flag(f"REC({b.recover_cooldown})"))

    if flags_p or flags_b:
        # flags contain ANSI codes so we can't use str width formatting directly
        p_flags_str = "  " + " ".join(flags_p)
        b_flags_str = " ".join(flags_b)
        # pad the player column by counting visible (non-escape) chars
        p_visible = " ".join(f.split("\033")[0] if "\033" in f else f for f in flags_p)
        pad = max(0, 32 - len("  " + p_visible))
        print(p_flags_str + " " * pad + b_flags_str)

    print(f"\n  {B}── Range: {manager.current_range} ──{R}")
    print(f"{DIM}{'─' * 60}{R}")


def render_cards(manager: CombatManager) -> list[Card]:
    all_cards = manager.all_player_cards()

    print(f"\n  {WHITE}Select a card:{R}\n")
    selectable = []
    for card in all_cards:
        reason = manager.card_disabled_reason(card)
        if not reason:
            idx = len(selectable) + 1
            selectable.append(card)
            print(f"  {WHITE}{B}[{idx}]{R} {WHITE}{card.name:<20}{R}  "
                  f"{DIM}STA:{R}{card.stamina_cost:>2}  "
                  f"{DIM}DMG:{R}{RED}{card.damage:>2}{R}  "
                  f"{DIM}BAL:{R}{AMBER}{card.balance_damage:>2}{R}  "
                  f"{DIM}MOM:{R}{YELLOW}+{card.momentum_gain}{R}")
        else:
            print(f"  {DIM}[ ] {card.name:<20} — {reason}{R}")

    if not selectable:
        from card import STYLE_CARD_MAP
        style_map = STYLE_CARD_MAP.get(manager.player.style, {})
        forced = next((c for c in style_map.values() if c.is_block), None)
        if forced:
            selectable = [forced]
            print(f"\n  {YELLOW}{B}[!]{R} {DIM}No cards available — forced to [{forced.name}].{R}")

    return selectable


def run_fight():
    p_style = pick_style("Choose YOUR style:")
    b_style = pick_style("Choose OPPONENT style:")

    player  = Fighter("Fighter", p_style)
    boxer   = Fighter("Opponent", b_style)
    manager = CombatManager(player, boxer)

    print(f"\n  {DIM}══════════════════════════════════{R}")
    print(f"  {B}{WHITE}      LAST ROUND — TEXT MODE{R}")
    print(f"  {DIM}══════════════════════════════════{R}")
    print(f"  {CYAN}{B}{player.style}{R}  vs  {RED}{B}{boxer.style}{R}")
    print(f"  {DIM}Press Enter to begin...{R}\n")
    input()

    while not manager.is_over():
        render_hud(manager)
        selectable = render_cards(manager)

        # Player input
        choice = None
        while choice is None:
            raw = input(f"\n  {DIM}>{R} ").strip().lower()
            if raw == "q":
                print(f"\n  {DIM}Match abandoned.{R}\n")
                return
            try:
                idx = int(raw) - 1
                if 0 <= idx < len(selectable):
                    choice = selectable[idx]
                else:
                    print(f"  {DIM}Enter a number 1–{len(selectable)}{R}")
            except ValueError:
                print(f"  {DIM}Enter a number or 'q' to quit.{R}")

        # Player turn
        p_result = manager.player_turn(choice)
        print(f"\n  {CYAN}{B}── PLAYER: {choice.name} ──{R}")
        for msg in p_result.messages:
            print(f"  {colorize_msg(msg)}")

        if manager.is_over():
            break

        # AI turn
        ai_result = manager.ai_turn()
        print(f"\n  {RED}{B}── OPPONENT: {ai_result.card_name} ──{R}")
        for msg in ai_result.messages:
            print(f"  {colorize_msg(msg)}")

        input(f"\n  {DIM}[Enter for next round]{R}")

        if not manager.is_over():
            manager.end_round()

    # Match over
    render_hud(manager)
    winner = manager.winner()
    print(f"\n{DIM}{'═' * 60}{R}")
    if winner == "player":
        print(f"  {GREEN}{B}VICTORY — The opponent has been defeated.{R}")
    else:
        print(f"  {RED}{B}DEFEAT — You have been knocked out.{R}")
    print(f"  {DIM}Match lasted {manager.round_number - 1} rounds.{R}")
    print(f"{DIM}{'═' * 60}{R}\n")


if __name__ == "__main__":
    run_fight()
