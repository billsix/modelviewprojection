FROM docker.io/debian:bookworm

RUN apt update && apt upgrade -y && \
    apt install    -y gnuplot \
                      texlive \
                      texlive-latex-extra \
                      graphviz \
                      python3-sphinx-rtd-theme \
                      fonts-mathjax \
                      libjs-mathjax \
                      make \
                      python3-imageio \
                      python3-matplotlib \
                      dvipng

COPY ./entrypoint/entrypoint.sh  /entrypoint.sh
COPY ./book /book/
COPY ./src /src/

ENTRYPOINT ["/entrypoint.sh"]
