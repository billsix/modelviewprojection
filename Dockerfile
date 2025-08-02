FROM registry.fedoraproject.org/fedora:42

COPY .emacs.d /root/.emacs.d
COPY .tmux.conf /root/.tmux.conf

RUN dnf upgrade -y
RUN dnf install -y gnuplot \
                   emacs \
                   graphviz \
                   mathjax \
                   make \
                   python3-furo \
                   python3-openimageio \
                   python3-matplotlib \
                   python3-pytest \
                   python3-pip \
                   python3-sphinx_rtd_theme \
                   mathjax-main-fonts \
                   mathjax-math-fonts \
                   texlive \
                   texlive-dvipng \
                   texlive-anyfontsize \
                   texlive-dvisvgm \
                   texlive-standalone \
                   inkscape \
                   latexmk \
                   automake \
                   autoconf \
                   gcc \
                   aspell \
                   aspell-en \
                   ruff \
                   python3-isort \
                   tmux  && \
     python3 -c "import matplotlib.pyplot as plt; plt.plot([1,2,3], [4,5,6]); plt.show()" && \
     dnf clean all


RUN emacs --batch --load ~/.emacs.d/install-melpa-packages.el
RUN echo "alias ls='ls --color=auto'" >> ~/.bashrc

ENTRYPOINT ["/entrypoint.sh"]
