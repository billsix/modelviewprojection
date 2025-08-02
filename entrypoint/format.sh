#!/bin/env bash

cd /mvp/

ruff check . --select F401,F841 --fix
ruff format --line-length=80

for FILE in $(find . -iname '*.py')
do
    isort $FILE
done
