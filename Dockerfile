FROM registry.fedoraproject.org/fedora:44

ARG BUILD_DOCS=0
ARG USE_EMACS=0
ARG USE_JUPYTER=0
ARG USE_SPYDER=0
ARG USE_X_WINDOWS=0

COPY entrypoint/dotfiles/ /root/
COPY entrypoint/*.sh /usr/local/bin
COPY entrypoint/entrypoint.sh /
COPY requirements.txt /requirements.txt
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
                   python3-devel \
                   python3-pytest \
		   python3-pytest-lsp \
                   python3-sympy \
                   python3-virtualenv \
                   python3-wxpython4  \
                   ruff \
                   uv \
                   tmux  \
                   ty \
                   which \
                   wxGTK \
                   wxGTK-devel; \
     dnf install -y \
                   pinentry; \
    if [ "$BUILD_DOCS" = "1" ]; then \
       dnf install -y \
                   autoconf \
                   automake \
                   aspell \
                   aspell-en \
                   g++ \
                   gcc \
                   git \
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
                   texlive-fontspec \
                   texlive-gnu-freefont \
                   texlive-luahbtex \
                   texlive-luatex85 \
                   texlive-polyglossia \
                   texlive-standalone && \
       ( git clone https://github.com/billsix/tex-expression-to-png.git /tmp/tex_exp_to_png && \
         cd /tmp/tex_exp_to_png && \
         git checkout fbbd9a3fefa48ab86136ca4fba9861553289c5ee && \
         meson setup builddir && \
         meson compile -C builddir && \
         meson install -C builddir ) && \
       rm -rf /tmp/tex_exp_to_png ; \
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
                   mesa-libGLU-devel \
                   libwayland-egl \
                   libwayland-client \
                   libxkbcommon; \
    fi ; \
    python3 -m venv --system-site-packages /venv/ && \
    export VIRTUAL_ENV_DISABLE_PROMPT=1  && \
    source /venv/bin/activate && \
    # setuptools/wheel are BUILD prereqs for loadpackages.sh's editable install.
    # It runs `uv pip install --no-index --no-build-isolation -e .`, which by
    # design neither creates an isolated build env nor installs
    # build-system.requires -- so the backend must already be in /venv. Python
    # 3.12+ venvs no longer seed setuptools, so without this the editable
    # install fails with ModuleNotFoundError and `make format` never runs.
    # (gacalc's Dockerfile does the same thing.)
    uv pip install setuptools wheel --python $(which python) && \
    dnf install -y libatomic && uv pip install pyright --python $(which python); \
    if [ "$USE_EMACS" = "1" ]; then \
      dnf install -y \
                  emacs \
                  emacs-gtk+x11 \
                  emacs-pgtk \
                  python3-lsp-server; \
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
       uv pip install moviepy --python $(which python); \
    fi; \
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
    echo "source ~/.extrabashrc" >> ~/.bashrc && \
    echo "/usr/local/bin/jupyter.sh # on http://127.0.0.1:8888/lab" >> ~/.bash_history && \
    echo "emacs src/modelviewprojection/mathutils3d.py" >> ~/.bash_history && \
    echo "emacs src/modelviewprojection/mathutils2d.py" >> ~/.bash_history && \
    echo "emacs src/modelviewprojection/mathutils1d.py" >> ~/.bash_history && \
    echo "emacs src/modelviewprojection/mathutils.py" >> ~/.bash_history && \
    grep -v wxpython /requirements.txt | uv pip install --python $(which python) -r - && \
    rm /requirements.txt

ENTRYPOINT ["/entrypoint.sh"]
