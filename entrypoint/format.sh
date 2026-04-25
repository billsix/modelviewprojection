#!/bin/env bash

export VIRTUAL_ENV_DISABLE_PROMPT=1
source /venv/bin/activate

ruff check . --fix
ruff format . --line-length=80
