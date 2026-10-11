#!/usr/bin/env bash
#
# install-epix-deps.sh -- the Fedora packages ePiX needs on top of what mvp's
# BUILD_DOCS block already installs. Run before install-epix.sh.
#
# mvp's main Dockerfile RUN already provides the build toolchain (meson, ninja,
# gcc-g++/g++/gcc, git under BUILD_DOCS) and ImageMagick + a base texlive, so this
# only adds the pieces specific to the ePiX render chain. The list mirrors
# epix-mirror's own entrypoint/02-install-render.sh (the figure-rendering
# toolchain: latex -> dvips -> ghostscript -> eps/pdf; convert for png), plus
# gcc-c++ to guarantee the g++ the `epix` driver compiles each figure with.
#
# A single dnf call, so its own exit status is the gate. dnf is idempotent, so a
# package mvp already installed is a no-op here.
set -uo pipefail

dnf install -y \
    gcc-c++ \
    ghostscript \
    ImageMagick \
    texlive-collection-basic \
    texlive-collection-latexrecommended \
    texlive-collection-pictures \
    texlive-collection-fontsrecommended \
    texlive-eepic \
    texlive-epstopdf \
    texlive-dvips \
    texlive-collection-pstricks \
    texlive-pgf
