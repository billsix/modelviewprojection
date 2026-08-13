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

# System-package installation lives in per-group scripts (entrypoint/0N-install-*.sh)
# so the exact same package set can be installed on a bare Fedora host/guest (no
# container runtime needed), not only during this build. The scripts take NO options:
# WHICH optional groups get installed is decided HERE, by the feature-flag ARG `if`
# blocks below -- the flag logic lives only in the Dockerfile. The dnf CACHE MOUNT and
# `keepcache=True` also stay HERE (build-time plumbing that makes rebuilds fast; the
# scripts are runtime-agnostic and must not depend on them). base is always installed;
# each feature group runs only when its flag is 1. `&&` between them so a failed
# install fails the build.
RUN  --mount=type=cache,target=/var/cache/libdnf5 \
     --mount=type=cache,target=/var/lib/dnf \
     echo "keepcache=True" >> /etc/dnf/dnf.conf && \
     /usr/local/bin/01-install-base.sh && \
     if [ "$BUILD_DOCS" = "1" ];    then /usr/local/bin/02-install-docs.sh;     fi && \
     if [ "$USE_X_WINDOWS" = "1" ]; then /usr/local/bin/03-install-xwindows.sh; fi && \
     if [ "$USE_EMACS" = "1" ];     then /usr/local/bin/04-install-emacs.sh;    fi && \
     if [ "$USE_JUPYTER" = "1" ];   then /usr/local/bin/05-install-jupyter.sh;  fi && \
     if [ "$USE_SPYDER" = "1" ];    then /usr/local/bin/06-install-spyder.sh;   fi && \
     if [ "$BUILD_DOCS" = "1" ]; then \
        ( git clone https://github.com/billsix/tex-expression-to-png.git /tmp/tex_exp_to_png && \
          cd /tmp/tex_exp_to_png && \
          git checkout 67da442daf12eff07d5d8e6d57258be01492e3d0 && \
          meson setup builddir && \
          meson compile -C builddir && \
          meson install -C builddir ) && \
        rm -rf /tmp/tex_exp_to_png && \
        python3 -c "import matplotlib.pyplot as plt; plt.plot([1,2,3], [4,5,6]); plt.show()" ; \
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
     # (gacalc's Dockerfile does the same thing.) libatomic (a pyright runtime
     # dep) is installed by 01-install-base.sh above.
     uv pip install setuptools wheel --python /venv/bin/python && \
     uv pip install pyright --python /venv/bin/python && \
     if [ "$USE_JUPYTER" = "1" ]; then \
        uv pip install moviepy --python /venv/bin/python && \
        jupytext-config set-default-viewer python && \
        # --level=user writes /root/.jupyter/labconfig/, which JupyterLab reads
        # under any prefix. The default sys_prefix level would resolve through
        # /usr/bin/jupyter here (the venv gets its own jupyter binary only from
        # the later requirements install) and write /usr/etc, which the
        # venv-launched server never reads.
        jupyter labextension disable --level=user "@jupyterlab/apputils-extension:announcements" ; \
     fi ; \
     if [ "$USE_SPYDER" = "1" ]; then \
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
     grep -v wxpython /requirements.txt | uv pip install --python /venv/bin/python -r - && \
     rm /requirements.txt

# gacalc SOURCE version for the book's literalinclude (docs-only, see below).
# MUST match the gacalc== pin in requirements.txt -- the same version drives both
# the runtime wheel and the docs source, so the book never documents a version
# the code does not run.  Declared HERE (not with the ARGs up top) so a version
# bump only rebuilds this layer, not the expensive TeX/dnf install above.
ARG GACALC_VERSION=0.0.16
# Pull the gacalc SOURCE (its PyPI sdist) into the image, purely so the book can
# ``literalinclude`` gacalc's doc-region markers.  This is DOCS-ONLY: nothing
# imports it and it is never on sys.path -- the runtime dependency is the gacalc
# WHEEL installed from requirements.txt above.  The sdist is used (not a git
# clone) because it already contains the generated g1/g2/g3/scalar modules with
# markers baked in, so no git checkout and no code generation are needed here.
# entrypoint.sh copies these files into book/docs/_gacalc_src/ before the build.
RUN python3 -c "import json, urllib.request, tarfile, io; \
d = json.load(urllib.request.urlopen('https://pypi.org/pypi/gacalc/${GACALC_VERSION}/json')); \
url = [f['url'] for f in d['urls'] if f['packagetype'] == 'sdist'][0]; \
tarfile.open(fileobj=io.BytesIO(urllib.request.urlopen(url).read())).extractall('/opt/gacalc-sdist')" && \
    mkdir -p /opt/gacalc-src && \
    cp /opt/gacalc-sdist/gacalc-${GACALC_VERSION}/src/gacalc/*.py /opt/gacalc-src/ && \
    rm -rf /opt/gacalc-sdist

ENTRYPOINT ["/entrypoint.sh"]
