FROM registry.fedoraproject.org/fedora:42

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
                   npm \
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
                   python3-sphinxcontrib-bibtex \
                   python3-sympy \
                   python3-wxpython4  \
                   ruff \
                   texlive \
                   texlive-anyfontsize \
                   texlive-dvipng \
                   texlive-dvisvgm \
                   texlive-standalone \
                   tmux && \
     # cache matplotlib stuff \
     python3 -c "import matplotlib.pyplot as plt; plt.plot([1,2,3], [4,5,6]); plt.show()" && \
     # clean out dnf \
     dnf clean all && \
     # install pyright for lsp \
     npm install -g pyright && \
     # install moviepy until fedora takes it \
     python3 -m pip install --break-system-packages --root-user-action=ignore moviepy && \
     # install imgui, until I replace imgui code with wxpython4 \
     cd ~/ && \
     git clone https://github.com/billsix/pyimgui.git && \
     cd pyimgui && \
     git submodule init && git submodule update && \
     python3 -m pip install --break-system-packages --root-user-action=ignore .


COPY entrypoint/dotfiles/ /root/

RUN emacs --batch --load /root/.emacs.d/install-melpa-packages.el && \
    echo "alias ls='ls --color=auto'" >> ~/.bashrc



ENTRYPOINT ["/entrypoint.sh"]
