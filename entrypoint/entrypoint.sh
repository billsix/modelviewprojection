#!/bin/bash

cd /book/docs
make html


# fix issues that github has for displaying the pages for me
cd _build/html/

# copy the files over
mkdir /output/modelviewprojection
cp -r * /output/modelviewprojection/
