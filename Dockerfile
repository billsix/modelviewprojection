FROM registry.fedoraproject.org/fedora:45

# Layer order: least volatile and most expensive first, so an edit near the
# bottom never rebuilds what is above it.  Two rules keep the cache stable:
#   - each install script is COPYed just before the RUN that uses it (an early
#     `COPY entrypoint/*.sh` would make every script edit rebuild everything);
#   - each ARG is declared just before the first layer that reads it (a
#     build-arg's value is part of the cache key of every later RUN, so a
#     top-of-file ARG toggle would rebuild every slow layer below it).
#
# System-package installation lives in per-group scripts (entrypoint/0N-install-*.sh)
# so the exact same package set can be installed on a bare Fedora host/guest (no
# container runtime needed), not only during this build. The scripts take NO options:
# WHICH optional groups get installed is decided HERE, by the feature-flag ARG `if`
# blocks below -- the flag logic lives only in the Dockerfile. The dnf CACHE MOUNT and
# `keepcache=True` also stay HERE (build-time plumbing that makes rebuilds fast; the
# scripts are runtime-agnostic and must not depend on them).

# Base packages (always installed); see entrypoint/01-install-base.sh.
COPY entrypoint/01-install-base.sh /usr/local/bin/
RUN  --mount=type=cache,target=/var/cache/libdnf5 \
     --mount=type=cache,target=/var/lib/dnf \
     echo "keepcache=True" >> /etc/dnf/dnf.conf && \
     /usr/local/bin/01-install-base.sh

# The book toolchain (Sphinx + TeX Live, the slowest group); see
# entrypoint/02-install-docs.sh.  BUILD_DOCS is read by this layer and the
# tex-expression-to-png layer right after it.
ARG BUILD_DOCS=0
COPY entrypoint/02-install-docs.sh /usr/local/bin/
RUN  --mount=type=cache,target=/var/cache/libdnf5 \
     --mount=type=cache,target=/var/lib/dnf \
     if [ "$BUILD_DOCS" = "1" ]; then /usr/local/bin/02-install-docs.sh; fi

# tex-expression-to-png (github.com/billsix/tex-expression-to-png), pinned by
# SHA, renders the book's TeX expressions.  The matplotlib call warms its font
# cache once at build time.
RUN  if [ "$BUILD_DOCS" = "1" ]; then \
        ( git clone https://github.com/billsix/tex-expression-to-png.git /tmp/tex_exp_to_png && \
          cd /tmp/tex_exp_to_png && \
          git checkout 67da442daf12eff07d5d8e6d57258be01492e3d0 && \
          meson setup builddir && \
          meson compile -C builddir && \
          meson install -C builddir ) && \
        rm -rf /tmp/tex_exp_to_png && \
        python3 -c "import matplotlib.pyplot as plt; plt.plot([1,2,3], [4,5,6]); plt.show()" ; \
     fi

# X11 / Wayland client libraries for the GL demos; see
# entrypoint/03-install-xwindows.sh.
ARG USE_X_WINDOWS=0
COPY entrypoint/03-install-xwindows.sh /usr/local/bin/
RUN  --mount=type=cache,target=/var/cache/libdnf5 \
     --mount=type=cache,target=/var/lib/dnf \
     if [ "$USE_X_WINDOWS" = "1" ]; then /usr/local/bin/03-install-xwindows.sh; fi

# The Python venv and every Python package.  requirements.txt and
# constraints.txt are COPYed (not bind-mounted) so that a change to either
# changes this layer's cache key and reruns the install.
COPY requirements.txt /requirements.txt
COPY constraints.txt /constraints.txt
RUN  --mount=type=cache,target=/root/.cache/uv \
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
     uv pip install setuptools wheel -c /constraints.txt \
         --python /venv/bin/python && \
     # Every Python package goes into /venv, at the exact version in
     # constraints.txt (direct AND transitive; regenerate with `make
     # update-pins`).  uv does not count the distro python3-* packages as
     # installed, so /venv gets its own copy of each and the venv copy wins:
     # every console script (pytest, sphinx-build, jupyter) is then a
     # /venv/bin script that can import the venv's packages.  wxpython is the
     # one distro-only package (python3-wxpython4), so it is filtered out.
     grep -v wxpython /requirements.txt | \
         uv pip install --python /venv/bin/python -c /constraints.txt -r - && \
     rm /requirements.txt /constraints.txt

# ePiX -- the book's LaTeX-native figure source (github.com/billsix/epix-mirror),
# built from source at ONE pinned commit and installed into /usr/local, with its
# Python front-end (`epix`) installed editable in /venv (so it comes after the
# venv layer). Figures live in book/figures/epix/*.py and render to
# _static/epix/<name>.{pdf,png}. Mirrors the sibling geometricalgebra repo's
# setup; it replaced the gnuplot + matplotlib book figures.
#
# Default 0 so a plain build is unaffected; the Makefile passes USE_EPIX=1.
# The ePiX build is the most expensive layer after TeX, so it sits above the
# cheap Jupyter/Spyder/Emacs groups and the dotfiles: editing one of those
# never rebuilds ePiX.
ARG USE_EPIX=0
ARG EPIX_COMMIT=ebf3ca607ae6c1d4fa307e8b0359960d875d219c
COPY entrypoint/epix/install-epix-deps.sh entrypoint/epix/install-epix.sh /usr/local/bin/
# constraints.txt is bind-mounted (not left in the image) so nanobind installs
# at its pinned version.
RUN --mount=type=cache,target=/var/cache/libdnf5 \
    --mount=type=cache,target=/var/lib/dnf \
    --mount=type=bind,source=constraints.txt,target=/constraints.txt \
    if [ "$USE_EPIX" = "1" ]; then \
      bash /usr/local/bin/install-epix-deps.sh && \
      EPIX_COMMIT="$EPIX_COMMIT" CONSTRAINTS=/constraints.txt \
        bash /usr/local/bin/install-epix.sh ; \
    fi

# JupyterLab + jupytext packages (entrypoint/05-install-jupyter.sh), then their
# config, which writes container paths so it stays here.  The venv is active,
# so these are the /venv jupytext-config and jupyter, the same ones
# jupyter.sh's server runs.  --level=user writes /root/.jupyter/labconfig/,
# which JupyterLab reads under any prefix.
ARG USE_JUPYTER=0
COPY entrypoint/05-install-jupyter.sh /usr/local/bin/
RUN  --mount=type=cache,target=/var/cache/libdnf5 \
     --mount=type=cache,target=/var/lib/dnf \
     if [ "$USE_JUPYTER" = "1" ]; then \
        /usr/local/bin/05-install-jupyter.sh && \
        export VIRTUAL_ENV_DISABLE_PROMPT=1 && \
        source /venv/bin/activate && \
        jupytext-config set-default-viewer python && \
        jupyter labextension disable --level=user "@jupyterlab/apputils-extension:announcements" ; \
     fi

# The Spyder IDE (entrypoint/06-install-spyder.sh), then its spyder.ini,
# which writes a container path so it stays here.
ARG USE_SPYDER=0
COPY entrypoint/06-install-spyder.sh /usr/local/bin/
RUN  --mount=type=cache,target=/var/cache/libdnf5 \
     --mount=type=cache,target=/var/lib/dnf \
     if [ "$USE_SPYDER" = "1" ]; then \
        /usr/local/bin/06-install-spyder.sh && \
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
     fi

# Emacs + the pyright language server; see entrypoint/04-install-emacs.sh.
# Packages only: the vendored elpa tree is bind-mounted at `make shell` and
# byte-compiled by Emacs at run time, never in this build.
ARG USE_EMACS=0
COPY entrypoint/04-install-emacs.sh /usr/local/bin/
RUN  --mount=type=cache,target=/var/cache/libdnf5 \
     --mount=type=cache,target=/var/lib/dnf \
     if [ "$USE_EMACS" = "1" ]; then /usr/local/bin/04-install-emacs.sh; fi

# Dotfiles (.extrabashrc, .emacs.d minus the vendored elpa), the run-time
# entrypoint scripts, and the shell-history seeding: cheap, and edited more
# often than any package group, so they come after all of them.  The Makefile
# also bind-mounts entrypoint.sh, shell.sh, format.sh, jupyter.sh and
# spyder.sh over these copies; the baked copies are what a pulled image runs.
COPY entrypoint/dotfiles/ /root/
COPY entrypoint/entrypoint.sh /
COPY entrypoint/entrypoint.sh entrypoint/format.sh entrypoint/jupyter.sh \
     entrypoint/loadpackages.sh entrypoint/shell.sh entrypoint/spyder.sh \
     /usr/local/bin/
RUN  echo "source ~/.extrabashrc" >> ~/.bashrc && \
     echo "/usr/local/bin/jupyter.sh # on http://127.0.0.1:8888/lab" >> ~/.bash_history && \
     echo "emacs src/modelviewprojection/mathutils3d.py" >> ~/.bash_history && \
     echo "emacs src/modelviewprojection/mathutils2d.py" >> ~/.bash_history && \
     echo "emacs src/modelviewprojection/mathutils1d.py" >> ~/.bash_history && \
     echo "emacs src/modelviewprojection/mathutils.py" >> ~/.bash_history

# gacalc SOURCE version for the book's literalinclude (docs-only, see below).
# MUST match the gacalc== pin in requirements.txt -- the same version drives both
# the runtime wheel and the docs source, so the book never documents a version
# the code does not run.  Declared HERE so a version bump only rebuilds this
# layer and the baked source below.
ARG GACALC_VERSION=0.1.1
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

# Bake the project's OWN source into the image so a PULLED image is runnable
# standalone with no bind-mount: the entrypoint builds the book / runs the demos
# and tests from this baked copy.  `make shell` and the run targets bind-mount
# the live host repo over /mvp, which SHADOWS this baked copy at the same path,
# so development overrides it (see tasks/reference/container-source-and-mounts.md).
# The editable install below targets /mvp, so imports resolve to the baked source
# when pulled and to the live mount during development; loadpackages.sh re-runs
# it idempotently on entry.  COPY is LAST so a source change rebuilds only these
# two layers.  .dockerignore keeps .git / output / *.tar / caches out of the
# baked tree.
COPY . /mvp
RUN source /venv/bin/activate && cd /mvp && \
    uv pip install --no-deps --no-index --no-build-isolation -e . \
        --python /venv/bin/python

ENTRYPOINT ["/entrypoint.sh"]
