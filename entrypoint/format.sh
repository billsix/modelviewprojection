#!/bin/env bash

ruff check . --fix
ruff format --line-length=80
