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
                      dvipng \
                      aspell-en && \
     python3 -c "import matplotlib.pyplot as plt; plt.plot([1,2,3], [4,5,6]); plt.show()"

COPY ./book /book/
COPY ./src /src/
COPY ./entrypoint/entrypoint.sh  /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
