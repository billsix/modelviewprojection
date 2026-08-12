#!/usr/bin/env bash
#
# 01-install-base.sh -- install the ALWAYS-needed Fedora packages for this project.
#
# One package group per script, and the scripts take NO options: which optional
# groups (docs, X, emacs, jupyter, spyder) also get installed is decided by the
# DOCKERFILE (its ARG `if` blocks), or by a human choosing which scripts to run.
# The same script installs the same packages whether run during `podman build`, on a
# bare Fedora host, or in a guest with no container runtime.
#
# Run base first (it upgrades and installs the core set); then run whichever of the
# 0N-install-*.sh feature scripts you want, e.g.:
#     sudo ./entrypoint/01-install-base.sh
#     sudo ./entrypoint/02-install-docs.sh      # only if you want the book toolchain
#
# Multiple dnf calls here, so accumulate a non-zero exit if any fails (don't let a
# later success mask an earlier failure).
set -uo pipefail

# These are Fedora packages, so dnf is required. Fail loudly on anything else.
if ! command -v dnf >/dev/null 2>&1; then
    echo "01-install-base.sh: needs 'dnf' (this installs Fedora packages), not found." >&2
    echo "Run on a Fedora host/guest, or inside the project's Fedora-based image." >&2
    exit 1
fi

status=0

dnf upgrade -y || status=1

dnf install -y \
    gcc-g++ \
    glib \
    glib2-devel \
    glfw \
    meson \
    ninja \
    python3-glfw \
    python3-numpy \
    python3-openimageio \
    python3-pillow \
    python3-pyopengl \
    python3-devel \
    python3-pytest \
    python3-pytest-lsp \
    python3-sympy \
    python3-virtualenv \
    python3-wxpython4 \
    ruff \
    uv \
    tmux \
    ty \
    which \
    wxGTK \
    wxGTK-devel || status=1

dnf install -y pinentry || status=1

# libatomic is a runtime dependency of pyright (the Dockerfile pip-installs pyright
# into /venv). Always installed, as in the original Dockerfile.
dnf install -y libatomic || status=1

exit $status
