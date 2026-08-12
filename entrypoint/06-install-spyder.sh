#!/usr/bin/env bash
#
# 06-install-spyder.sh -- the Spyder IDE (package only). Corresponds to the
# Dockerfile's USE_SPYDER flag; run only when USE_SPYDER=1. The spyder.ini CONFIG
# stays in the Dockerfile because it writes a container path. No options -- see
# 01-install-base.sh for the design.
#
# Single dnf call, so its own exit status is this script's exit status.
set -uo pipefail

dnf install -y spyder
