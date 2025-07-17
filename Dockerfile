FROM docker.io/debian:trixie

RUN apt update  && apt upgrade -y && \
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
                      inkscape \
                      latexmk \
                      automake \
                      autoconf \
                      make \
                      gcc \
                      python3-pytest \
                      python3-pip \
                      aspell-en && \
     python3 -c "import matplotlib.pyplot as plt; plt.plot([1,2,3], [4,5,6]); plt.show()"


ENTRYPOINT ["/entrypoint.sh"]
