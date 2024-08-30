# Use the Red Hat Universal Base Image 8
FROM fedora

RUN dnf install    -y gnuplot \
                      texlive \
                      texlive-anyfontsize \
                      texlive-dvisvgm \
                      graphviz \
                      python3-sphinx_rtd_theme \
                      mathjax \
                      make \
                      python3-imageio \
                      python3-matplotlib \
                      texlive-standalone

COPY ./entrypoint/entrypoint.sh  /entrypoint.sh
COPY ./book /book/

ENTRYPOINT ["/entrypoint.sh"]
