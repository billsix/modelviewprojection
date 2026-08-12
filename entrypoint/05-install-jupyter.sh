#!/usr/bin/env bash
#
# 05-install-jupyter.sh -- JupyterLab + jupytext (packages only). Corresponds to the
# Dockerfile's USE_JUPYTER flag; run only when USE_JUPYTER=1. The jupyter CONFIG
# (moviepy, jupytext-config, disabling the announcements extension) stays in the
# Dockerfile because it writes container paths and needs the /venv. No options -- see
# 01-install-base.sh for the design.
#
# Single dnf call, so its own exit status is this script's exit status.
set -uo pipefail

dnf install -y \
    ffmpeg \
    jupyter \
    jupyterlab \
    jupytext \
    make \
    mathjax \
    mathjax-main-fonts \
    mathjax-math-fonts \
    myst-nb \
    python3-jupyterlab-jupytext \
    python3-jupyter-lsp
