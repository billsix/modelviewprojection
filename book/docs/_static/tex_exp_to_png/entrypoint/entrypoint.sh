#!/bin/env bash

cd /root/texExpToPng
texExpToPng --exp "$1" --size "$2" --output /output/"$3"
