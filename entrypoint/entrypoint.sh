#!/bin/env bash

cd /book/docs
make html


# fix issues that github has for displaying the pages for me
cd _build/html/

# copy the files over
mkdir /output/modelviewprojection
cp -r * /output/modelviewprojection/
# see if this fixes github issue with unscores in
# filenames created by sphinx
touch /output/modelviewprojection/.nojekyll


cd /book/docs
make latexpdf
cp  _build/latex/*pdf /output/modelviewprojection/

make epub
cp _build/epub/* /output/modelviewprojection/
