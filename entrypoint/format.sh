#!/bin/env bash

export VIRTUAL_ENV_DISABLE_PROMPT=1
source /venv/bin/activate

ruff check src --fix
ruff check tests --fix
ruff format src --line-length=80
ruff format tests --line-length=80
ty check /mvp/src
ty check /mvp/tests
