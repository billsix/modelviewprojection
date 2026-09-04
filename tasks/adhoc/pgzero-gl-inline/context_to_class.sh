#!/usr/bin/env bash
# One-time refactor: pgzero_gl's `context` MODULE (module globals) -> a `Context`
# CLASS (src/.../context.py, rewritten by hand). Class-attribute state makes
# `Context.renderer = ...` a typed assignment the type checker accepts, which the
# single-file inlined games need (a module global reached via a
# sys.modules[__name__] alias is not ty-legible). This rewrites every call site:
# the `from . import [...] context` imports become `from .context import Context`,
# and every `context.` becomes `Context.`.
#
# Idempotent: a second run finds no `context.`/`from . import context` (they are
# now `Context.`/`from .context import Context`) and changes nothing.
#
# Usage:  bash tasks/adhoc/pgzero-gl-inline/context_to_class.sh
set -eu
cd "$(git rev-parse --show-toplevel)"
SHIM=src/modelviewprojection/pgzero_gl

# Shim modules (relative imports).
for f in "$SHIM"/actor.py "$SHIM"/audio.py "$SHIM"/draw.py "$SHIM"/joystick.py \
         "$SHIM"/resources.py "$SHIM"/runner.py "$SHIM"/screen.py \
         "$SHIM"/surface.py "$SHIM"/text.py "$SHIM"/__init__.py; do
  sed -i -E \
    -e 's/^from \. import audio, context$/from . import audio\nfrom .context import Context/' \
    -e 's/^from \. import context$/from .context import Context/' \
    -e 's/\bcontext\./Context./g' \
    "$f"
done

# The out-of-tree smoke-test harness (absolute import).
sed -i -E \
  -e 's/^( *)from modelviewprojection\.pgzero_gl import context$/\1from modelviewprojection.pgzero_gl.context import Context/' \
  -e 's/\bcontext\./Context./g' \
  ports/codetheclassics/_smoketest.py

echo "context -> Context refactor applied."
