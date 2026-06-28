#!/bin/env bash

export VIRTUAL_ENV_DISABLE_PROMPT=1
source /venv/bin/activate

ruff check src --fix
ruff check tests --fix
ruff format src --line-length=80
ruff format tests --line-length=80
ty check /mvp/src
ty check /mvp/tests
# Code-the-Classics pygame compatibility shim + the typed game ports. The games
# are faithful BSD ports -- type-checked (annotations only) but NOT reformatted by
# ruff, to keep them byte-faithful to upstream. See ports/codetheclassics/.
ty check /mvp/ports/codetheclassics/pgzero_gl
ty check /mvp/ports/codetheclassics/vol1
ty check /mvp/ports/codetheclassics/vol2
