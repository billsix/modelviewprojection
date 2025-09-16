FROM registry.fedoraproject.org/fedora:42

COPY .emacs.d /root/.emacs.d
COPY .tmux.conf /root/.tmux.conf

RUN dnf upgrade -y
RUN dnf install -y \
                   aspell \
                   aspell-en \
                   autoconf \
                   automake \
                   emacs \
		   ffmpeg \
		   firefox \
                   g++ \
		   gcc \
                   glfw \
		   gnuplot \
                   graphviz \
                   ImageMagick \
                   inkscape \
		   jupyter \
		   jupyterlab  \
		   jupytext \
                   latexmk \
                   libglvnd-gles \
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
                   libXtst \
                   libXv \
                   libXxf86vm \
                   make \
                   mathjax \
                   mathjax-main-fonts \
                   mathjax-math-fonts \
                   mesa-dri-drivers  \
                   mesa-libGLU-devel \
                   python3-devel \
                   python3-furo \
                   python3-glfw \
                   python3-isort \
		   python3-jupyterlab-jupytext \
		   python3-jupyter-lsp \
		   python3-lsp-server \
                   python3-matplotlib \
		   python3-numpy \
                   python3-openimageio \
		   python3-pillow \
                   python3-pip \
                   python3-pyopengl \
                   python3-pytest \
		   python3-pytest-lsp \
                   python3-sphinx_rtd_theme \
		   python3-sympy \
                   python3-wxpython4  \
                   ruff \
                   texlive \
                   texlive-anyfontsize \
                   texlive-dvipng \
                   texlive-dvisvgm \
                   texlive-standalone \
                   tmux && \
     python3 -c "import matplotlib.pyplot as plt; plt.plot([1,2,3], [4,5,6]); plt.show()" && \
     dnf clean all

RUN python3 -m pip install --break-system-packages --root-user-action=ignore moviepy
RUN cd ~/ && \
    git clone https://github.com/billsix/pyimgui.git && \
    cd pyimgui && \
    git submodule init && git submodule update && \
    python3 -m pip install --break-system-packages --root-user-action=ignore .


RUN emacs --batch --load ~/.emacs.d/install-melpa-packages.el
RUN echo "alias ls='ls --color=auto'" >> ~/.bashrc



RUN dnf install -y python3-sphinxcontrib-bibtex


ENTRYPOINT ["/entrypoint.sh"]
