FROM docker.io/fedora:42

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
                   inkscape \
                   latexmk \
                   automake \
                   autoconf \
                   gcc \
                   aspell \
                   aspell-en \
                   tmux  && \
     python3 -c "import matplotlib.pyplot as plt; plt.plot([1,2,3], [4,5,6]); plt.show()"

RUN dnf install -y texlive-standalone

RUN emacs --batch --load ~/.emacs.d/install-melpa-packages.el
RUN echo "alias ls='ls --color=auto'" >> ~/.bashrc


# packages to run spyder and graphics demos from within the container
RUN dnf install -y spyder \
    mesa-dri-drivers  \
    libXtst \
    libXcomposite \
    libXcursor \
    libXdamage \
    libXfixes \
    libXft \
    libXi \
    libXinerama \
    libXmu \
    libXrandr \
    libXrender \
    libXres \
    libXv \
    libXxf86vm \
    libglvnd-gles \
    mesa-libGLU-devel \
    python3-glfw \
    python3-pyopengl

ENTRYPOINT ["/entrypoint.sh"]
