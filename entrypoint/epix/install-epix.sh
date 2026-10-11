#!/usr/bin/env bash
#
# install-epix.sh -- fetch the maintainer's ePiX mirror (github.com/billsix/epix-mirror)
# at ONE pinned commit, install the C++ library + drivers into /usr/local with Meson,
# then build its Python front-end (the nanobind extension) and install the `epix`
# package into /venv, so the book's figures can be written in Python the way
# epix-mirror's own notebooks are. Run after install-epix-deps.sh (the build +
# render packages). Adapted verbatim from the sibling geometricalgebra repo
# (github.com/billsix/geometricalgebra), which pins this same commit.
#
# The commit comes from the environment -- the Dockerfile passes its EPIX_COMMIT ARG
# explicitly (`RUN EPIX_COMMIT=$EPIX_COMMIT install-epix.sh`), so the pin lives in one
# place (the Dockerfile) and a bare-host run must name it too. Pinning to a commit, not a
# branch, is what makes the image layer reproducible; bump the ARG to move it.
#
# The fetch is a shallow fetch of exactly that commit (GitHub serves reachable SHAs), so
# the layer holds one tree, not the history. The tree is fetched to /epix -- the path
# epix-mirror's own entrypoint/build_py.sh hard-codes, which is why that script can be
# reused unchanged to build the extension against the installed libepix (the Meson
# build dir is removed first so it links the INSTALLED library) -- and then MOVED to
# /opt/epix-src before the Python package is installed editable from its python/ dir
# (the extension's .so sits inside that package dir). The move matters: a directory
# named `epix` in `/` would be found by Python as an empty namespace package whenever
# the cwd is `/` (sys.path[0]) and would shadow the installed package -- exactly what a
# Dockerfile RUN's cwd is. The source stays in the image (small; samples/ and notebooks/
# are the reference for writing figures). This runs at IMAGE-BUILD time -- network is
# used here and never at run time.
set -euo pipefail

: "${EPIX_COMMIT:?install-epix.sh: set EPIX_COMMIT to the epix-mirror commit SHA to install}"
EPIX_URL="${EPIX_URL:-https://github.com/billsix/epix-mirror.git}"
SRC=/epix                          # where build_py.sh expects the tree while building
DEST="${EPIX_SRC:-/opt/epix-src}"  # where it lives afterwards (NOT a bare `epix` in /)

rm -rf "$SRC"
git init -q "$SRC"
git -C "$SRC" remote add origin "$EPIX_URL"
git -C "$SRC" fetch -q --depth 1 origin "$EPIX_COMMIT"
git -C "$SRC" checkout -q --detach FETCH_HEAD
echo "epix-mirror at $(git -C "$SRC" rev-parse HEAD)"

meson setup "$SRC/build" "$SRC" --prefix=/usr/local
meson install -C "$SRC/build"
rm -rf "$SRC/build" "$SRC/.git"
epix --version

# Python front-end: nanobind (headers + nb_combined.cpp) into the venv, the extension
# built by epix-mirror's own script (g++ against /usr/local's libepix), then the tree
# moved out of / and the package installed editable so `import epix` resolves to
# $DEST/python. The check runs from / on purpose: that is the cwd that would expose a
# namespace-package shadow.
export VIRTUAL_ENV_DISABLE_PROMPT=1
source /venv/bin/activate
uv pip install --python /venv/bin/python nanobind
bash "$SRC/entrypoint/build_py.sh"
rm -rf "$DEST"
mv "$SRC" "$DEST"
uv pip install --python /venv/bin/python --no-deps --no-build-isolation -e "$DEST/python"
(cd / && python -c 'import epix; epix.Point(x=1, y=2); print("epix python front-end OK:", epix.__file__)')
