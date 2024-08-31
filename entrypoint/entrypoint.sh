#!/bin/bash

cd /book/docs
make html


# fix issues that github has for displaying the pages for me
cd _build/html/
rm -rf static images sources
mv _sources sources
mv _images images
mv _static static

find . -iname '*.rst.txt' | xargs sed -i -e 's@_static/@static/@g'
find . -iname '*.rst.txt' | xargs sed -i -e 's@_images/@images/@g'
find . -iname '*.rst.txt' | xargs sed -i -e 's@_sources/@sources/@g'

find . -iname '*.html' | xargs sed -i -e 's@_static/@static/@g'
find . -iname '*.html' | xargs sed -i -e 's@_images/@images/@g'
find . -iname '*.html' | xargs sed -i -e 's@_sources/@sources/@g'

find . -iname '*.inv' | xargs sed -i -e 's@_static/@static/@g'
find . -iname '*.inv' | xargs sed -i -e 's@_images/@images/@g'
find . -iname '*.inv' | xargs sed -i -e 's@_sources/@sources/@g'

find . -iname '*.js' | xargs sed -i -e 's@_static/@static/@g'
find . -iname '*.js' | xargs sed -i -e 's@_images/@images/@g'
find . -iname '*.js' | xargs sed -i -e 's@_sources/@sources/@g'


# copy the files over
mkdir /output/modelviewprojection
cp -r * /output/modelviewprojection/
