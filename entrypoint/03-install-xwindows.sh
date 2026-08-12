#!/usr/bin/env bash
#
# 03-install-xwindows.sh -- X11 / Wayland client libraries for the GL demos.
# Corresponds to the Dockerfile's USE_X_WINDOWS flag; run only when USE_X_WINDOWS=1.
# No options -- see 01-install-base.sh for the design.
#
# Single dnf call, so its own exit status is this script's exit status.
set -uo pipefail

dnf install -y \
    libglvnd-gles \
    libXcomposite \
    libXcursor \
    libXdamage \
    libXfixes \
    libXft \
    libXi \
    libXinerama \
    libXmu \
    libXrandr \
    libXrender \
    libXres \
    libXtst \
    libXv \
    libXxf86vm \
    mesa-dri-drivers \
    mesa-libGLU-devel \
    libwayland-egl \
    libwayland-client \
    libxkbcommon
