################################################################################
# combat_screen.rpy
# Last Round – Ren'Py UI layer  v0.2
#
# Scene hierarchy
# ───────────────
# Arena Scene
# ├── Background
# ├── Ring
# ├── Crowd Layer
# ├── Fighter Sprites (Boxer, Karate Fighter)
# ├── FX Layer (Punches, Camera Shake, Dust, Hit Sparks)
# ├── HUD (Health Bars, Stamina, Momentum, Portraits, Round Timer)
# └── Card Hand (Attack Cards, Skill Cards, Defense Cards, End Turn)
#
# USAGE
# ─────
# Before calling combat_start, initialise the manager:
#
#   python:
#       from fighter import Fighter
#       from combat_manager import CombatManager
#       player  = Fighter("Karate Fighter", "KARATE")
#       boxer   = Fighter("Boxer", "BOXER")
#       manager = CombatManager(player, boxer)
#
#   call combat_start
#
# On return, check manager.winner() → "player" | "boxer"
#
# ASSETS  (swap Solid() placeholders for real files in game/images/)
# ──────
#   arena_bg.png          — full-screen arena backdrop
#   arena_ring.png        — boxing ring (centre, bottom half)
#   arena_crowd.png       — crowd layer (behind ring, loops/scrolls)
#   portrait_karate.png   — 120×120 portrait, player
#   portrait_boxer.png    — 120×120 portrait, opponent
#   sprite_karate_idle    — karate fighter idle sprite sheet / image
#   sprite_boxer_idle     — boxer idle sprite sheet / image
#   fx_spark.png          — hit-spark single frame (tinted per hit type)
#   fx_dust.png           — dust puff single frame
################################################################################


# ── Image definitions  ────────────────────────────────────────────────────────
# Replace Solid() with real image files once assets are ready.

image arena_bg          = Solid("#1a0f08")
image arena_ring        = Solid("#2e1a0c")
image arena_crowd       = Solid("#110a05")

image portrait_karate   = Solid("#3a6040")
image portrait_boxer    = Solid("#6a3030")

image sprite_karate_idle = Solid("#4a8060")
image sprite_boxer_idle  = Solid("#904040")

image fx_spark           = Solid("#ffe080")
image fx_dust            = Solid("#c8a060")
image fx_punch_blur      = Solid("#ffffff")


# ── ATL transforms  ───────────────────────────────────────────────────────────

# Camera shake — apply to the fighter/ring container on heavy hits
transform camera_shake:
    subpixel True
    linear 0.04  xoffset  14
    linear 0.04  xoffset -12
    linear 0.035 xoffset   8
    linear 0.035 xoffset  -6
    linear 0.03  xoffset   3
    linear 0.03  xoffset   0
    xoffset 0

# Quick hit flash overlay (full-screen tint)
transform hit_flash_in_out:
    alpha 0.0
    linear 0.06 alpha 0.55
    linear 0.14 alpha 0.0
    alpha 0.0

# Spark appears at impact point then fades
transform fx_spark_pop:
    zoom 0.4 alpha 0.0
    linear 0.05 zoom 1.1 alpha 1.0
    linear 0.15 zoom 1.4 alpha 0.0

# Dust puff rises and fades
transform fx_dust_rise:
    yoffset 0 alpha 0.0
    linear 0.05 alpha 0.85
    linear 0.25 yoffset -30 alpha 0.0

# Fighter sprite — absorb-hit reel
transform sprite_hit_reel:
    subpixel True
    linear 0.05 xoffset -8
    linear 0.06 xoffset  5
    linear 0.04 xoffset  0
    xoffset 0

# Fighter sprite — dodge sway
transform sprite_dodge_sway:
    subpixel True
    linear 0.08 xoffset -20
    linear 0.12 xoffset  0
    xoffset 0

# Fighter sprite — KO fall
transform sprite_ko_fall:
    rotate 0 alpha 1.0
    linear 0.4 rotate 80 xoffset 120 yoffset 60 alpha 0.0


# ── init python helpers  ──────────────────────────────────────────────────────

init python:

    def combat_card_category(card):
        """Bin a card into 'attack' | 'defense' | 'skill'."""
        if card.is_attack():
            return "attack"
        if card.is_block or card.is_dodge or card.is_recover or card.is_brace:
            return "defense"
        return "skill"   # focus, movement

    def combat_cards_by_category(manager, category):
        """Return all player cards (available + greyed) for a given category."""
        return [
            c for c in manager.all_player_cards()
            if combat_card_category(c) == category
        ]

    # FX state — set by labels, read by screens
    _fx_shake_player = False   # shake the player sprite
    _fx_shake_boxer  = False   # shake the boxer sprite
    _fx_shake_screen = False   # shake the whole ring
    _fx_spark_pos    = (640, 360)  # (x, y) pixel coords of spark
    _fx_show_spark   = False
    _fx_show_dust    = False
    _card_tab        = "attack"   # active card hand tab


# ── Styles  ───────────────────────────────────────────────────────────────────

style hud_portrait_frame:
    background "#0007"
    padding (4, 4)

style hud_name is text:
    color "#eee"
    bold True
    size 18

style hud_label is text:
    color "#999"
    size 14
    xsize 40

style hud_value is text:
    color "#ddd"
    size 14
    xsize 32
    textalign 1.0

style hud_flag is text:
    color "#8cf"
    size 13
    bold True

style hud_flag_bad is text:
    color "#f84"
    size 13
    bold True

style hud_range_label is text:
    color "#aaa"
    size 13
    textalign 0.5
    xalign 0.5

style hud_range_value is text:
    color "#fe8"
    size 24
    bold True
    textalign 0.5
    xalign 0.5

style round_timer_text is text:
    color "#ccc"
    size 20
    bold True
    textalign 0.5
    xalign 0.5

style card_tab_btn is button:
    padding (14, 6)
    background "#1c2a1c"
    hover_background "#2a3e2a"

style card_tab_btn_active is button:
    padding (14, 6)
    background "#2a4a2a"
    hover_background "#2a4a2a"

style card_tab_text is text:
    color "#8a8"
    size 15
    bold True

style card_tab_text_active is text:
    color "#cec"
    size 15
    bold True

style card_btn is button:
    background "#1e2e1e"
    hover_background "#2a4030"
    padding (10, 7)
    xfill True

style card_btn_text is text:
    color "#bec"
    size 15

style card_btn_stat is text:
    color "#7a9"
    size 13

style card_btn_heavy is button:
    background "#2a1e1e"
    hover_background "#3a2424"
    padding (10, 7)
    xfill True

style card_btn_heavy_text is text:
    color "#e8b080"
    size 15

style card_btn_disabled is frame:
    background "#161616"
    padding (10, 7)
    xfill True

style card_disabled_text is text:
    color "#444"
    size 14

style card_disabled_reason is text:
    color "#553"
    size 12
    italic True

style end_turn_btn is button:
    background "#3a2010"
    hover_background "#5a3018"
    padding (16, 10)
    xfill True

style end_turn_btn_text is text:
    color "#e8a050"
    size 16
    bold True
    textalign 0.5

style advance_btn is button:
    background "#1a2e1a"
    hover_background "#2a4a2a"
    padding (28, 12)
    xalign 0.5

style advance_btn_text is text:
    color "#cec"
    size 18
    bold True

style result_header is text:
    color "#fe8"
    size 15
    bold True

style log_text is text:
    color "#bbb"
    size 14
    line_spacing 2

style ko_banner_text is text:
    color "#f84"
    size 56
    bold True
    xalign 0.5
    outlines [(2, "#400", 0, 0)]


# ── Stat bar helper  ──────────────────────────────────────────────────────────

screen stat_bar(val, maxval, bar_color="#4af", width=200):
    bar:
        value val
        range maxval
        xsize width
        ysize 12
        yalign 0.5
        left_bar  Solid(bar_color)
        right_bar Solid("#2a2a2a")
        thumb     Null()


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 6 — HUD
# Contains: Health Bars, Stamina, Momentum, Portraits, Round Timer
# ═══════════════════════════════════════════════════════════════════════════════

screen combat_hud(manager):
    $ p = manager.player
    $ b = manager.boxer

    # HUD backdrop strip
    add Solid("#000a") xfill True ysize 170 ypos 0

    # ── Player side (left) ──────────────────────────────────────────────────
    frame:
        xpos 10
        ypos 8
        background "#0000"
        padding (0, 0)

        hbox:
            spacing 10

            # Portrait
            frame:
                style "hud_portrait_frame"
                add "portrait_karate" xsize 80 ysize 80

            # Bars
            vbox:
                spacing 3
                text p.name style "hud_name"
                hbox:
                    spacing 4
                    text "HP " style "hud_label"
                    use stat_bar(p.hp, p.hp_max, "#3d3", 180)
                    text "[p.hp]" style "hud_value"
                hbox:
                    spacing 4
                    text "STA" style "hud_label"
                    use stat_bar(p.stamina, p.stamina_max, "#36f", 180)
                    text "[p.stamina]" style "hud_value"
                hbox:
                    spacing 4
                    text "MOM" style "hud_label"
                    use stat_bar(p.momentum, p.momentum_max, "#fa4", 180)
                    text "[p.momentum]" style "hud_value"
                hbox:
                    spacing 4
                    text "BAL" style "hud_label"
                    use stat_bar(p.balance, p.balance_max, "#f84", 180)
                    text "[p.balance]" style "hud_value"

            # Status flags
            vbox:
                spacing 4
                yalign 0.5
                if p.staggered:
                    text "STAGGERED" style "hud_flag_bad"
                if p.blocking:
                    text "BLOCKING"  style "hud_flag"
                if p.dodging:
                    text "DODGING"   style "hud_flag"

    # ── Centre: Round timer + range ─────────────────────────────────────────
    vbox:
        xalign 0.5
        ypos 10
        spacing 6
        xsize 180
        text "ROUND [manager.round_number]" style "round_timer_text"
        text "─ [manager.current_range] ─"  style "hud_range_value"

    # ── Boxer side (right, mirrored) ────────────────────────────────────────
    frame:
        xalign 1.0
        xoffset -10
        ypos 8
        background "#0000"
        padding (0, 0)

        hbox:
            spacing 10

            # Status flags (left of bars for right side)
            vbox:
                spacing 4
                yalign 0.5
                if b.staggered:
                    text "STAGGERED" style "hud_flag_bad"

            # Bars
            vbox:
                spacing 3
                text b.name style "hud_name" xalign 1.0
                hbox:
                    spacing 4
                    text "HP " style "hud_label"
                    use stat_bar(b.hp, b.hp_max, "#3d3", 180)
                    text "[b.hp]" style "hud_value"
                hbox:
                    spacing 4
                    text "STA" style "hud_label"
                    use stat_bar(b.stamina, b.stamina_max, "#36f", 180)
                    text "[b.stamina]" style "hud_value"
                hbox:
                    spacing 4
                    text "MOM" style "hud_label"
                    use stat_bar(b.momentum, b.momentum_max, "#fa4", 180)
                    text "[b.momentum]" style "hud_value"
                hbox:
                    spacing 4
                    text "BAL" style "hud_label"
                    use stat_bar(b.balance, b.balance_max, "#f84", 180)
                    text "[b.balance]" style "hud_value"

            # Portrait
            frame:
                style "hud_portrait_frame"
                add "portrait_boxer" xsize 80 ysize 80


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 7 — CARD HAND
# Contains: Attack Cards | Skill Cards | Defense Cards | End Turn
# ═══════════════════════════════════════════════════════════════════════════════

screen combat_card_hand(manager):

    # Card hand panel — bottom of screen
    frame:
        xfill True
        yalign 1.0
        ysize 210
        background "#0e160e"
        padding (10, 8)

        vbox:
            spacing 6

            # ── Tab row ────────────────────────────────────────────────────
            hbox:
                spacing 4

                $ tabs = [("attack", "⚔ Attack"), ("skill", "✦ Skill"), ("defense", "🛡 Defense")]
                for tab_id, tab_label in tabs:
                    $ is_active = (_card_tab == tab_id)
                    textbutton tab_label:
                        style "card_tab_btn_active" if is_active else "card_tab_btn"
                        text_style "card_tab_text_active" if is_active else "card_tab_text"
                        action [SetVariable("_card_tab", tab_id), renpy.restart_interaction]

                # End Turn — always visible, plays Block (guard)
                $ block_card = manager.all_player_cards()[[c.name for c in manager.all_player_cards()].index("Block")]
                textbutton "End Turn":
                    style "end_turn_btn"
                    text_style "end_turn_btn_text"
                    action Return(block_card)
                    xalign 1.0

            # ── Card rows for active tab ────────────────────────────────
            $ tab_cards = combat_cards_by_category(manager, _card_tab)

            hbox:
                spacing 8
                for card in tab_cards:
                    $ reason = manager.card_disabled_reason(card)

                    if reason is None:
                        button:
                            style "card_btn_heavy" if card.is_heavy else "card_btn"
                            action Return(card)
                            xsize 230
                            vbox:
                                spacing 2
                                text card.name:
                                    style "card_btn_heavy_text" if card.is_heavy else "card_btn_text"
                                hbox:
                                    spacing 8
                                    if card.damage:
                                        text "DMG [card.damage]"     style "card_btn_stat"
                                    if card.balance_damage:
                                        text "BAL -[card.balance_damage]" style "card_btn_stat"
                                    if card.stamina_damage:
                                        text "STA -[card.stamina_damage]" style "card_btn_stat"
                                    if card.momentum_gain:
                                        text "+[card.momentum_gain]M"     style "card_btn_stat"
                                text "Cost: [card.stamina_cost] STA" style "card_btn_stat"
                    else:
                        frame:
                            style "card_btn_disabled"
                            xsize 230
                            vbox:
                                spacing 2
                                text card.name   style "card_disabled_text"
                                text reason      style "card_disabled_reason"


# ═══════════════════════════════════════════════════════════════════════════════
# LAYERS 1–5 — ARENA + FIGHTERS + FX
# ═══════════════════════════════════════════════════════════════════════════════

screen combat_arena(manager, shake_screen=False):

    # Layer 1: Background
    add "arena_bg" xfill True yfill True

    # Layer 2 + 3: Crowd then Ring (crowd behind ring)
    add "arena_crowd" xfill True ysize 400 ypos 120
    add "arena_ring"  xsize 860 ysize 320 xalign 0.5 yalign 0.85

    # Layer 4: Fighter sprites
    # Apply camera_shake transform to the fighter container when a heavy hit lands
    frame:
        background "#0000"
        xfill True
        ysize 400
        ypos 140
        at (camera_shake if shake_screen else Null())

        # Karate fighter — left side
        add "sprite_karate_idle":
            xsize 180 ysize 300
            xpos  160 yalign 0.9
            at sprite_hit_reel if _fx_shake_player else Null()

        # Boxer — right side (mirrored via zoom=-1 on x-axis once real sprites are in)
        add "sprite_boxer_idle":
            xsize 180 ysize 300
            xpos  940 yalign 0.9
            at sprite_hit_reel if _fx_shake_boxer else Null()

    # Layer 5: FX — Hit sparks
    if _fx_show_spark:
        add "fx_spark":
            xsize 60 ysize 60
            xpos  (_fx_spark_pos[0] - 30)
            ypos  (_fx_spark_pos[1] - 30)
            at fx_spark_pop

    # Layer 5: FX — Dust puff (low on ring, after heavy move)
    if _fx_show_dust:
        add "fx_dust":
            xsize 80 ysize 40
            xpos  (_fx_spark_pos[0] - 40)
            ypos  480
            at fx_dust_rise

    # Layer 5: FX — Hit punch-blur flash
    if _fx_show_spark:
        add "fx_punch_blur":
            xfill True yfill True
            alpha 0.0
            at hit_flash_in_out


# ═══════════════════════════════════════════════════════════════════════════════
# COMBINED SELECTION SCREEN
# Shows all layers; card hand returns the chosen Card.
# ═══════════════════════════════════════════════════════════════════════════════

screen combat_select(manager):
    modal True

    use combat_arena(manager, shake_screen=False)
    use combat_hud(manager)
    use combat_card_hand(manager)


# ═══════════════════════════════════════════════════════════════════════════════
# ROUND RESULT SCREEN
# Shown after both fighters have acted; waits for player to advance.
# ═══════════════════════════════════════════════════════════════════════════════

screen combat_round_result(manager, p_result, ai_result, shake_screen=False):
    modal True

    use combat_arena(manager, shake_screen=shake_screen)
    use combat_hud(manager)

    # Log panel — bottom right, above card hand area
    frame:
        xalign 1.0
        yalign 0.97
        xsize  400
        ysize  230
        background "#0e1a0e"
        padding (12, 10)

        vbox:
            spacing 5

            if p_result is not None:
                text "▶ You — [p_result.card_name]" style "result_header"
                for msg in p_result.messages:
                    text msg style "log_text"
                null height 4

            if ai_result is not None:
                text "▶ Boxer — [ai_result.card_name]" style "result_header"
                for msg in ai_result.messages:
                    text msg style "log_text"

    # KO banner
    if manager.is_over():
        $ _winner = manager.winner()
        text ("VICTORY!" if _winner == "player" else "KO!"):
            style "ko_banner_text"
            xalign 0.5
            yalign 0.42

    # Advance / continue button
    vbox:
        xalign 0.5
        yalign 0.93
        textbutton ("Continue →" if manager.is_over() else "Next Round →"):
            style "advance_btn"
            action Return(True)


# ═══════════════════════════════════════════════════════════════════════════════
# COMBAT LABELS
# ═══════════════════════════════════════════════════════════════════════════════

label combat_start:
    $ _card_tab       = "attack"
    $ _fx_shake_player = False
    $ _fx_shake_boxer  = False
    $ _fx_shake_screen = False
    $ _fx_show_spark   = False
    $ _fx_show_dust    = False
    $ _fx_spark_pos    = (640, 360)
    jump combat_loop


label combat_loop:

    if manager.is_over():
        jump combat_end

    # ── Player picks a card ──────────────────────────────────────────────────
    $ _chosen_card = renpy.call_screen("combat_select", manager=manager)

    # ── Resolve player turn ──────────────────────────────────────────────────
    $ _p_result = manager.player_turn(_chosen_card)

    # ── Player FX: spark on boxer when hit lands ─────────────────────────────
    if _p_result.damage_dealt > 0:
        $ _fx_show_spark   = True
        $ _fx_spark_pos    = (900, 300)   # boxer impact zone
        $ _fx_show_dust    = _chosen_card.is_heavy
        $ _fx_shake_screen = _chosen_card.is_heavy
        $ renpy.pause(0.35, hard=True)
        $ _fx_show_spark  = False
        $ _fx_show_dust   = False
        $ _fx_shake_screen = False

    # ── Resolve AI turn ──────────────────────────────────────────────────────
    if not manager.is_over():
        $ _ai_result = manager.ai_turn()

        # AI FX: spark on player when hit lands
        if _ai_result.damage_dealt > 0:
            $ _fx_show_spark   = True
            $ _fx_spark_pos    = (260, 300)   # player impact zone
            $ _fx_show_dust    = _ai_result.damage_dealt >= 15
            $ _fx_shake_screen = _ai_result.damage_dealt >= 15
            $ renpy.pause(0.35, hard=True)
            $ _fx_show_spark  = False
            $ _fx_show_dust   = False
            $ _fx_shake_screen = False
    else:
        $ _ai_result = None

    # ── Show round result, wait for advance ──────────────────────────────────
    $ renpy.call_screen("combat_round_result",
        manager=manager,
        p_result=_p_result,
        ai_result=_ai_result,
        shake_screen=False)

    if manager.is_over():
        jump combat_end

    $ manager.end_round()
    jump combat_loop


label combat_end:
    $ _winner = manager.winner()
    $ _rounds = manager.round_number - 1
    $ _p_name = manager.player.name
    $ _b_name = manager.boxer.name

    scene black with fade

    if _winner == "player":
        "[_p_name] wins!\nThe [_b_name] has been defeated after [_rounds] rounds."
    else:
        "Defeat.\n[_p_name] has been knocked out after [_rounds] rounds."

    return
