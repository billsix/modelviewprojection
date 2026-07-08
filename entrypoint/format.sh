#!/bin/env bash

export VIRTUAL_ENV_DISABLE_PROMPT=1
source /venv/bin/activate

ruff check src --fix
ruff check tests --fix
# The ports (Code the Classics shim + games, OpenGL SuperBible) are formatted
# too, as of 2026-07-08 -- the old byte-faithful "no ruff on the games" rule
# was retired along with the structural modernization (see the ctc-* task
# series); the games stay BEHAVIOUR-faithful only.
ruff check ports --fix
ruff format src --line-length=80
ruff format tests --line-length=80
ruff format ports --line-length=80
ty check /mvp/src
ty check /mvp/tests
# Code-the-Classics pygame compatibility shim + the typed game ports.
ty check /mvp/ports/codetheclassics/pgzero_gl
ty check /mvp/ports/codetheclassics/vol1
ty check /mvp/ports/codetheclassics/vol2
