#!/usr/bin/env bash
#
# 04-install-emacs.sh -- Emacs + the pyright language server that lsp-pyright
# drives. Corresponds to the Dockerfile's USE_EMACS flag; run only when
# USE_EMACS=1. No options -- see 01-install-base.sh for the design.
#
# pyright is the EDITOR's server only; the format/type-check gates run ty. It
# comes from npm, never the pip `pyright` package: the pip package is a launcher
# that downloads Node and the real server on first use in each fresh container,
# so it fails offline. `npm install -g` puts pyright-langserver in
# /usr/local/bin, where lsp-pyright finds it.
#
# Two commands, so accumulate their exit statuses.
set -uo pipefail
status=0

dnf install -y \
    emacs \
    emacs-gtk+x11 \
    emacs-pgtk \
    nodejs \
    npm || status=1
npm install -g pyright || status=1

exit $status
