#!/bin/bash

cd /book/docs
make html
mkdir /output/modelviewprojection
cp -r _build/* /output/modelviewprojection/
