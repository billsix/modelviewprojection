#!/usr/bin/env bash
#
# 04-install-emacs.sh -- Emacs + the Python LSP server. Corresponds to the
# Dockerfile's USE_EMACS flag; run only when USE_EMACS=1. No options -- see
# 01-install-base.sh for the design.
#
# Single dnf call, so its own exit status is this script's exit status.
set -uo pipefail

dnf install -y \
    emacs \
    emacs-gtk+x11 \
    emacs-pgtk \
    python3-lsp-server
