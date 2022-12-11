#!/bin/env bash

for f in `find ./mvpVisualization/ -name "*.py" | grep -v '__init__'`; do autoflake8 --in-place $f; done
for f in `find ./mvpVisualization/ -name "*.py" | grep -v '__init__'`; do black -l 120 $f; done

for f in `find ./src/ -name "*.py" | grep -v '__init__'`; do autoflake8 --in-place $f; done
for f in `find ./src/ -name "*.py" | grep -v '__init__'`; do black $f; done
