#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/last_round/game"
exec python fight_test.py "$@"
