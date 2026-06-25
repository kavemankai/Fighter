"""
fighter.py
Last Round – Combat Prototype v0.1
Spec: Technical Combat Specification v0.2
"""


class Fighter:
    """
    Holds all combat state for one fighter.
    No logic lives here — combat_manager.py owns resolution.
    """

    RANGES = ["LONG", "MID", "CLOSE"]

    def __init__(self, name: str, style: str):
        self.name    = name
        self.style   = style          # "KARATE" | "BOXER"

        # Core stats (spec §2)
        self.hp       = 100
        self.stamina  = 100
        self.momentum = 0
        self.balance  = 50            # Starting value per v0.2

        # Shared range — both fighters occupy the same range state.
        # combat_manager owns the authoritative range variable.
        # This field is a convenience reference, kept in sync by the manager.
        self.range    = "MID"

        # Temporary effect flags (cleared end of round, spec §3 step 8)
        self.blocking = False
        self.dodging  = False
        self.staggered = False

    # ── Stat helpers ──────────────────────────────────────────────────────

    @property
    def hp_max(self):      return 100
    @property
    def stamina_max(self): return 100
    @property
    def momentum_max(self): return 100
    @property
    def balance_max(self): return 50

    def is_ko(self) -> bool:
        return self.hp <= 0

    def can_afford(self, cost: int) -> bool:
        return self.stamina >= cost

    # ── Stat mutators (clamped) ───────────────────────────────────────────

    def apply_hp_damage(self, amount: int):
        self.hp = max(0, self.hp - amount)

    def apply_stamina_damage(self, amount: int):
        self.stamina = max(0, self.stamina - amount)

    def apply_balance_damage(self, amount: int):
        self.balance = max(0, self.balance - amount)

    def spend_stamina(self, cost: int):
        self.stamina = max(0, self.stamina - cost)

    def gain_momentum(self, amount: int):
        self.momentum = min(self.momentum_max, self.momentum + amount)

    def lose_momentum(self, amount: int):
        self.momentum = max(0, self.momentum - amount)

    def restore_stamina(self, amount: int):
        self.stamina = min(self.stamina_max, self.stamina + amount)

    def restore_balance(self, amount: int):
        self.balance = min(self.balance_max, self.balance + amount)

    # ── Regeneration (spec §4) ────────────────────────────────────────────

    def regenerate(self):
        """Called once per round after both fighters have acted."""
        self.stamina = min(self.stamina_max, self.stamina + 5)
        self.balance = min(self.balance_max, self.balance + 3)
        # Momentum does not regenerate.

    # ── Stagger (spec §10) ───────────────────────────────────────────────

    def enter_stagger(self):
        """
        Triggered when balance reaches 0.
        Momentum loss applied here immediately (spec §10).
        """
        self.staggered = True
        self.lose_momentum(10)

    def resolve_stagger_recovery(self):
        """
        Natural recovery: Balance set to 15 at start of next round.
        Called during clear-effects phase (spec §3 step 8).
        """
        if self.staggered:
            self.balance = 15        # Set to 15, not restore by 15 (v0.2 clarification)
            self.staggered = False

    # ── Clear effects (spec §3 step 8) ───────────────────────────────────

    def clear_round_effects(self):
        """Clear all temporary flags. Called after both fighters act."""
        self.blocking  = False
        self.dodging   = False
        self.resolve_stagger_recovery()

    # ── Debug ──────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        flags = []
        if self.blocking:  flags.append("BLOCKING")
        if self.dodging:   flags.append("DODGING")
        if self.staggered: flags.append("STAGGERED")
        flag_str = f" [{', '.join(flags)}]" if flags else ""
        return (
            f"{self.name} ({self.style}){flag_str}\n"
            f"  HP:{self.hp:>3}  STA:{self.stamina:>3}  MOM:{self.momentum:>3}  BAL:{self.balance:>3}  "
            f"Range:{self.range}"
        )
