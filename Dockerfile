# Use the Red Hat Universal Base Image 8
FROM fedora

COPY ./entrypoint/entrypoint.sh  /entrypoint.sh
COPY ./book /book/
RUN dnf install    -y gnuplot \
                      texlive \
                      texlive-anyfontsize \
                      texlive-dvisvgm \
                      graphviz \
                      python3-sphinx_rtd_theme \
                      mathjax \
                      make \
                      python3-imageio \
                      python3-matplotlib

ENTRYPOINT ["/entrypoint.sh"]
