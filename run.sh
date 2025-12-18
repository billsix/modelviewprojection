podman run -it --rm \
       --entrypoint /bin/bash \
       -e DISPLAY="$DISPLAY" \
       -v /tmp/.X11-unix:/tmp/.X11-unix \
       --security-opt label=type:container_runtime_t \
       -e WAYLAND_DISPLAY="$WAYLAND_DISPLAY" \
       -e XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" \
       -v "$XDG_RUNTIME_DIR:$XDG_RUNTIME_DIR" \
       docker.io/billsix/modelviewprojection:0.0.3

