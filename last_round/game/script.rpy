## script.rpy — game entry point

init python:
    import sys, os
    _combat_path = os.path.join(renpy.config.gamedir, "..", "combat")
    if _combat_path not in sys.path:
        sys.path.insert(0, _combat_path)

    from fighter import Fighter
    from combat_manager import CombatManager

label start:
    python:
        manager = CombatManager(
            Fighter("Karate Fighter", "KARATE"),
            Fighter("Boxer", "BOXER")
        )
    call combat_start
    return
