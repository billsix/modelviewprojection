podman run -it --rm \
       --entrypoint /bin/bash \
       -v ./output/:/output/:Z \
       modelviewprojection-html
