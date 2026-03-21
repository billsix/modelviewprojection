#!/bin/env bash

cd /mvp/ && pytest --exitfirst --disable-warnings || exit

cd /mvp/
jupytext --to notebook src/modelviewprojection/notebooksrc/plot2d.py --output  assignments/demo02/plot2d.ipynb
jupytext --to notebook src/modelviewprojection/notebooksrc/plot2d.py --output book/docs/plot2d.ipynb

jupytext --to notebook src/modelviewprojection/notebooksrc/framebuffer.py --output notebooks/framebuffer.ipynb
jupytext --to notebook src/modelviewprojection/notebooksrc/framebuffer.py --output book/docs/framebuffer.ipynb

jupytext --to notebook src/modelviewprojection/notebooksrc/ndc.py --output notebooks/ndc.ipynb
jupytext --to notebook src/modelviewprojection/notebooksrc/ndc.py --output book/docs/ndc.ipynb

uv pip install --no-deps --no-index --no-build-isolation -e . --system

cd /mvp/book/docs
make html
make latexpdf
make epub

# copy the files over
mkdir -p /output/modelviewprojection

# fix issues that github has for displaying the pages for me
cp -r _build/html/ /output/modelviewprojection/
cp -r _build/latex/*pdf /output/modelviewprojection/
cp -r _build/epub/*epub /output/modelviewprojection/
# see if this fixes github issue with unscores in
# filenames created by sphinx
touch /output/modelviewprojection/.nojekyll
