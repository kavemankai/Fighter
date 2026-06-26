## options.rpy — game configuration

define config.name        = "Last Round"
define config.version     = "0.1"
define config.window_title = "Last Round"

## Match the 1280×720 layout in combat_screen.rpy
init python:
    config.screen_width  = 1280
    config.screen_height = 720
