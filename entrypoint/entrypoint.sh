#!/bin/bash

cd /book/docs
make html
mkdir /output/modelviewprojection
cp -r _build/html /output/modelviewprojection/

cd /output/modelviewprojection/
rm -rf static images sources
mv _sources sources
mv _images images
mv _static static

# For MacOS to not have sed complain
export LC_CTYPE=C
export LANG=C

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

