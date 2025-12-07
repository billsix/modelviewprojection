#!/bin/env bash

cd /mvp/ && pytest --exitfirst --disable-warnings || exit

cd /mvp/
jupytext --to notebook src/modelviewprojection/notebooksrc/plot2d.py --output  assignments/demo02/plot2d.ipynb
jupytext --to notebook src/modelviewprojection/notebooksrc/plot2d.py --output book/docs/plot2d.ipynb
python3 -m pip install --no-deps -e . --break-system-packages --root-user-action=ignore

cd /mvp/book/docs
make html


# fix issues that github has for displaying the pages for me
cd _build/html/

# copy the files over
mkdir -p /output/modelviewprojection
cp -r * /output/modelviewprojection/
# see if this fixes github issue with unscores in
# filenames created by sphinx
touch /output/modelviewprojection/.nojekyll
