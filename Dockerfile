FROM docker.io/debian:trixie

COPY .emacs.d /root/.emacs.d
COPY .tmux.conf /root/.tmux.conf


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
                      aspell-en \
                      emacs-nox \
                      tmux  && \
     python3 -c "import matplotlib.pyplot as plt; plt.plot([1,2,3], [4,5,6]); plt.show()"

RUN emacs --batch --load ~/.emacs.d/install-melpa-packages.el
RUN echo "alias ls='ls --color=auto'" >> ~/.bashrc



ENTRYPOINT ["/entrypoint.sh"]
