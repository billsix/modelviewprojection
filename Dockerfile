FROM registry.fedoraproject.org/fedora:43

ARG BUILD_DOCS=0
ARG USE_EMACS=0
ARG USE_IMGUI=0
ARG USE_JUPYTER=0
ARG USE_SPYDER=0

COPY entrypoint/dotfiles/ /root/

RUN  --mount=type=cache,target=/var/cache/libdnf5 \
     --mount=type=cache,target=/var/lib/dnf \
     echo "keepcache=True" >> /etc/dnf/dnf.conf && \
     dnf upgrade -y && \
     dnf install -y \
                   gcc-g++ \
                   glib \
                   glib2-devel \
                   glfw \
                   meson \
                   ninja \
                   python3-glfw \
		   python3-numpy \
                   python3-openimageio \
		   python3-pillow \
                   python3-pyopengl \
                   python3-pytest \
		   python3-pytest-lsp \
                   python3-sympy \
                   python3-wxpython4  \
                   ruff \
                   uv \
                   tmux  \
                   ty \
                   wxGTK \
                   wxGTK-devel; \
    if [ "$BUILD_DOCS" = "1" ]; then \
       dnf install -y \
                   autoconf \
                   automake \
                   aspell \
                   aspell-en \
                   g++ \
                   gcc \
                   gnuplot \
                   graphviz \
                   ImageMagick \
                   inkscape \
                   latexmk \
                   make \
                   mathjax \
                   mathjax-main-fonts \
                   mathjax-math-fonts \
                   python3-furo \
                   python3-matplotlib \
                   python3-nbsphinx \
                   python3-sphinx_rtd_theme \
                   python3-sphinxcontrib-bibtex \
                   sphinx \
                   python-sphinxcontrib-bibtex-doc \
                   python3-sphinx-epytext \
                   python3-sphinx-latex \
                   python3-sphinx-math-dollar \
                   python3-sphinxcontrib-bibtex \
                   python3-texext \
                   texlive \
                   texlive-amsmath \
                   texlive-anyfontsize \
                   texlive-dvipng \
                   texlive-dvisvgm \
                   texlive-standalone; \
       python3 -c "import matplotlib.pyplot as plt; plt.plot([1,2,3], [4,5,6]); plt.show()" ; \
    fi ; \
    if [ "$USE_X_WINDOWS" = "1" ]; then \
       dnf install -y \
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
                   mesa-dri-drivers  \
                   mesa-libGLU-devel; \
    fi ; \
    dnf install -y libatomic && uv pip install --system pyright; \
    if [ "$USE_EMACS" = "1" ]; then \
      dnf install -y \
                  emacs \
                  emacs-gtk+x11 \
                  emacs-pgtk \
                  python3-lsp-server && \
      emacs --batch --load /root/.emacs.d/install-melpa-packages.el && \
      echo "alias ls='ls --color=auto'" >> ~/.bashrc ;\
    fi ; \
    if [ "$USE_JUPYTER" = "1" ]; then \
       dnf install -y \
        	   ffmpeg \
        	   jupyter \
        	   jupyterlab  \
        	   jupytext \
                   make \
                   mathjax \
                   mathjax-main-fonts \
                   mathjax-math-fonts \
                   myst-nb \
        	   python3-jupyterlab-jupytext \
        	   python3-jupyter-lsp  && \
       uv pip install --system moviepy; \
    fi; \
    if [ "$USE_IMGUI" = "1" ]; then \
       dnf install -y \
                   autoconf \
                   automake \
                   g++ \
        	   gcc \
                   python3-devel && \
        cd ~/ && \
        git clone https://github.com/billsix/pyimgui.git && \
        cd pyimgui && \
        git submodule init && git submodule update && \
        uv pip install --system . ;\
     fi ; \
    if [ "$USE_SPYDER" = "1" ]; then \
      dnf install -y spyder && \
      mkdir -p ~/.config/spyder-py3/config && \
      echo "[editor]" >> ~/.config/spyder-py3/config/spyder.ini && \
      echo "font/family = Source Code Pro" >> ~/.config/spyder-py3/config/spyder.ini && \
      echo "font/size = 24" >> ~/.config/spyder-py3/config/spyder.ini && \
      echo "[file_explorer]" >> ~/.config/spyder-py3/config/spyder.ini && \
      echo "visible = False" >> ~/.config/spyder-py3/config/spyder.ini && \
      echo "[tours]" >> ~/.config/spyder-py3/config/spyder.ini && \
      echo "show_tour_message = False" >> ~/.config/spyder-py3/config/spyder.ini && \
      echo "[appearance]" >> ~/.config/spyder-py3/config/spyder.ini && \
      echo "font/family = Adwaita Mono" >> ~/.config/spyder-py3/config/spyder.ini && \
      echo "font/size = 18" >> ~/.config/spyder-py3/config/spyder.ini; \
    fi ; \
    echo "exit() {" >> ~/.bashrc && \
    echo "    echo "Formatting on shell exit"" >> ~/.bashrc && \
    echo "    cd /mvp/src/ && format.sh" >> ~/.bashrc && \
    echo "    builtin exit "$@"" >> ~/.bashrc && \
    echo "}" >> ~/.bashrc && \
    echo "cd /mvp/" >> ~/.bashrc && \
    echo "PS1='\[\e[36m\]┌─(\t) \[\e[32m\]\u@\h:\w\n\[\e[36m\]└─λ \[\e[0m\]'" >> ~/.bashrc && \
    echo "emacs src/modelviewprojection/mathutils3d.py" >> ~/.bash_history && \
    echo "emacs src/modelviewprojection/mathutils2d.py" >> ~/.bash_history && \
    echo "emacs src/modelviewprojection/mathutils1d.py" >> ~/.bash_history && \
    echo "emacs src/modelviewprojection/mathutils.py" >> ~/.bash_history


COPY entrypoint/*.sh /usr/local/bin
COPY entrypoint/entrypoint.sh /

COPY requirements.txt /requirements.txt
RUN  uv pip install --system -r /requirements.txt && \
     rm /requirements.txt


RUN  --mount=type=cache,target=/var/cache/libdnf5 \
     --mount=type=cache,target=/var/lib/dnf \
     dnf install -y wxGTK \
                    wxGTK-devel \
                    gcc-g++


ENTRYPOINT ["/entrypoint.sh"]
