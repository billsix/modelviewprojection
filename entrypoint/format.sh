#!/bin/env bash

cd /mvp/

ruff check . --fix
ruff format --line-length=80

