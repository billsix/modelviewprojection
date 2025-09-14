FROM registry.fedoraproject.org/fedora:42

COPY .emacs.d /root/.emacs.d
COPY .tmux.conf /root/.tmux.conf

RUN dnf upgrade -y
RUN dnf install -y aspell \
                   aspell-en \
                   autoconf \
                   automake \
                   emacs \
		   firefox \
		   ffmpeg \
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
                   make \
                   mathjax \
                   mathjax-main-fonts \
                   mathjax-math-fonts \
                   python3-furo \
                   python3-isort \
		   python3-jupyterlab-jupytext \
		   python3-jupyter-lsp \
		   python3-lsp-server \
                   python3-matplotlib \
                   python3-openimageio \
                   python3-pip \
                   python3-pytest \
                   python3-sphinx_rtd_theme \
		   python3-sympy \
		   python3-pillow \
		   python3-pytest-lsp \
		   python3-numpy \
                   ruff \
                   texlive \
                   texlive-anyfontsize \
                   texlive-dvipng \
                   texlive-dvisvgm \
                   texlive-standalone \
                   tmux \
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
                   python3-pyopengl \
                   python3-wxpython4 && \
     python3 -c "import matplotlib.pyplot as plt; plt.plot([1,2,3], [4,5,6]); plt.show()" && \
     dnf clean all


RUN emacs --batch --load ~/.emacs.d/install-melpa-packages.el
RUN echo "alias ls='ls --color=auto'" >> ~/.bashrc

RUN python3 -m pip install --break-system-packages --root-user-action=ignore moviepy

RUN dnf install -y g++ \
                   python3-devel

RUN cd ~/ && \
    git clone https://github.com/billsix/pyimgui.git && \
    cd pyimgui && \
    git submodule init && git submodule update && \
    python3 -m pip install --break-system-packages --root-user-action=ignore .


ENTRYPOINT ["/entrypoint.sh"]
