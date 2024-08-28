#!/bin/bash

cd /book/docs
make html
make latexpdf
mkdir /output/modelviewprojection
cp -r _build/* /output/modelviewprojection/
