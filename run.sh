#!/bin/bash


podman run -it --rm \
       -v ./output/:/output/:Z \
       modelviewprojection-html
