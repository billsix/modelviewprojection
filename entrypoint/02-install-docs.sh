#!/usr/bin/env bash
#
# 02-install-docs.sh -- the book toolchain: Sphinx, TeX Live, plotting, and the
# system deps needed to build texExpToPng. Corresponds to the Dockerfile's BUILD_DOCS
# feature flag; the Dockerfile runs this only when BUILD_DOCS=1. No options -- see
# 01-install-base.sh for the design.
#
# Single dnf call, so its own exit status is this script's exit status.
set -uo pipefail

dnf install -y \
    autoconf \
    automake \
    aspell \
    aspell-en \
    g++ \
    gcc \
    git \
    gnuplot \
    graphviz \
    ImageMagick \
    inkscape \
    latexmk \
    make \
    mathjax \
    mathjax-main-fonts \
    mathjax-math-fonts \
    python3-furo \
    python3-matplotlib \
    python3-nbsphinx \
    python3-sphinx_rtd_theme \
    python3-sphinxcontrib-bibtex \
    sphinx \
    python-sphinxcontrib-bibtex-doc \
    python3-sphinx-epytext \
    python3-sphinx-latex \
    python3-sphinx-math-dollar \
    python3-sphinxcontrib-bibtex \
    python3-texext \
    texlive \
    texlive-amsmath \
    texlive-anyfontsize \
    texlive-dvipng \
    texlive-dvisvgm \
    texlive-fontspec \
    texlive-gnu-freefont \
    texlive-luahbtex \
    texlive-luatex85 \
    texlive-polyglossia \
    texlive-standalone
