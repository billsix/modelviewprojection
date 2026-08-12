#!/usr/bin/env bash
#
# verify-permutations.sh -- prove the REAL Dockerfile installs the right package
# groups for different feature-flag permutations.
#
# The flag logic lives in the Dockerfile (per-group 0N-install-*.sh scripts take no
# options; the Dockerfile's ARG `if` blocks decide which run). So the honest test is to
# actually BUILD the image with several --build-arg permutations and check, in each
# resulting image, which install scripts ran.
#
# HOW WE CHECK -- `dnf repoquery --userinstalled`, not sentinel packages.
# A first attempt used one sentinel package per group and checked `rpm -q`. That gives
# FALSE failures, because Fedora's dependency trees are deep: a "sentinel" is often
# pulled in as a transitive dependency of some OTHER group's package, so it is present
# even when its own flag is off (e.g. texlive-luahbtex via texlive-collection-basic,
# libxkbcommon via wxGTK-devel, inkscape via jupyter/spyder). And `dnf install spyder`
# actually installs `python3-spyder`, so `rpm -q spyder` misses it.
#
# `dnf repoquery --userinstalled` lists only the packages that were EXPLICITLY
# requested (reason=user) -- exactly what the 0N-install-*.sh scripts ran `dnf install`
# on -- and never transitive dependencies. So a group's representative package appears
# in that set IFF that group's script ran. Immune to both problems above.
#
# Run from the repo root:  bash tasks/adhoc/.../verify-permutations.sh
# Requires nested podman (this sandbox) and network. The buildkit layer cache + dnf
# cache mount make re-runs fast. Each image is removed after checking.
set -uo pipefail

IMG_PREFIX=mvp-verify

# columns: BUILD_DOCS USE_EMACS USE_JUPYTER USE_SPYDER USE_X_WINDOWS
declare -a NAMES=(BUILD_DOCS USE_EMACS USE_JUPYTER USE_SPYDER USE_X_WINDOWS)
# A representative package EXPLICITLY named in each group's install script, as a grep
# pattern against the userinstalled name list. Two subtleties, both learned here:
#   - `spyder` matches python3-spyder (what `dnf install spyder` actually installs).
#   - the docs representative must be a package base does NOT already pull as a
#     dependency. texlive-standalone fails this (base's texlive tree pulls it, so the
#     docs script's re-request never flips its reason to `user` -> userinstalled=0 even
#     when docs ran). inkscape is clean: base never pulls it; jupyter/spyder pull it
#     only as a dependency (so it stays userinstalled=0 there); the docs script installs
#     it explicitly (userinstalled=1). So inkscape-in-userinstalled == docs script ran.
declare -a PATTERN=('^inkscape$' '^emacs$' '^jupyterlab$' 'spyder' '^libXres$')

# Permutations: each flag is on in >=1 build and off in >=1 build.
declare -a PERMS=(
  "0 0 0 0 0"   # all off -> base only
  "0 1 1 1 1"   # every feature except docs
  "1 0 0 0 0"   # docs only (TeX + texExp)
)

overall=0; n=0
for perm in "${PERMS[@]}"; do
  n=$((n+1)); tag="${IMG_PREFIX}-p${n}"
  read -r BUILD_DOCS USE_EMACS USE_JUPYTER USE_SPYDER USE_X_WINDOWS <<<"$perm"
  echo "============================================================"
  echo "PERM p${n}: BUILD_DOCS=$BUILD_DOCS USE_EMACS=$USE_EMACS USE_JUPYTER=$USE_JUPYTER USE_SPYDER=$USE_SPYDER USE_X_WINDOWS=$USE_X_WINDOWS"

  if ! podman build \
        --build-arg BUILD_DOCS="$BUILD_DOCS" --build-arg USE_EMACS="$USE_EMACS" \
        --build-arg USE_JUPYTER="$USE_JUPYTER" --build-arg USE_SPYDER="$USE_SPYDER" \
        --build-arg USE_X_WINDOWS="$USE_X_WINDOWS" \
        -t "$tag" . > "/tmp/${tag}.buildlog" 2>&1; then
    echo "  FAIL: build failed (see /tmp/${tag}.buildlog)"; tail -5 "/tmp/${tag}.buildlog" | sed 's/^/    /'
    overall=1; continue
  fi

  # The set of EXPLICITLY-installed package names in the built image.
  ui="$(podman run --rm --cgroups=disabled --entrypoint bash "$tag" -c \
        'dnf repoquery --userinstalled --qf "%{name}\n" 2>/dev/null | sort -u')"

  perm_ok=1
  grep -qx tmux <<<"$ui" || { echo "  FAIL: base package tmux not user-installed"; perm_ok=0; }
  vals=($BUILD_DOCS $USE_EMACS $USE_JUPYTER $USE_SPYDER $USE_X_WINDOWS)
  for i in 0 1 2 3 4; do
    want=${vals[$i]}
    if grep -qE "${PATTERN[$i]}" <<<"$ui"; then got=1; else got=0; fi
    if [ "$got" = "$want" ]; then
      echo "  ok   ${NAMES[$i]}=$want -> ${PATTERN[$i]} userinstalled=$got"
    else
      echo "  FAIL ${NAMES[$i]}=$want but ${PATTERN[$i]} userinstalled=$got"; perm_ok=0
    fi
  done
  if [ "$perm_ok" = 1 ]; then echo "  => PERM p${n} PASS"; else echo "  => PERM p${n} FAIL"; overall=1; fi

  podman rmi -f "$tag" >/dev/null 2>&1
done

echo "============================================================"
if [ "$overall" = 0 ]; then echo "ALL PERMUTATIONS PASSED"; else echo "SOME PERMUTATIONS FAILED"; fi
exit $overall
