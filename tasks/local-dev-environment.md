# Local (non-container) dev environment: Makefile.local + deps script

**Status:** proposed — needs go-ahead
**Created:** 2026-06-15

## Goal

Give a contributor a **fully local** way to build and run mvp on the host — no
podman — that:

1. **`Makefile.local`** — a parallel Makefile (invoked `make -f Makefile.local …`)
   that does a local build: builds/installs **texExpToPng into a local directory**,
   creates the **venv in a local directory**, installs the package editable, and
   runs demos with both wired up.
2. **`install-deps.sh`** — a shell script that **detects the Linux distribution**
   (and macOS) and installs the relevant system packages via the right package
   manager, **modeled on how the mario64 repo documents it** (per-distro lists in
   `Ghostship/docs/building.md`: Debian/Ubuntu → apt, Arch → pacman, Fedora → dnf,
   openSUSE → zypper, macOS → brew).
3. **README.md update** — after the above is working, document the local-environment
   path (a "Local build (no container)" section), copy-paste-able like the existing
   texExpToPng section.

This complements (does not replace) the container `Makefile`. The container stays
the canonical/reproducible build; `Makefile.local` is the "I just want to hack on
it on my machine" path.

## Why everything goes in *local directories*

Keep the host clean and the tree self-contained / disposable:
- venv → `./.venv/` (gitignored)
- texExpToPng (+ anything else built) → `./.local/` (so the binary is
  `./.local/bin/texExpToPng`), gitignored
- meson build dir → `./.local/build-texexp/` (or `/tmp`), gitignored

So a `make -f Makefile.local clean-local` (or `rm -rf .venv .local`) fully resets,
and nothing lands in `$HOME` or `/usr/local`.

## `Makefile.local` — proposed targets

Header mirrors the repo conventions but with local paths:

```make
LOCAL_DIR  := $(CURDIR)/.local
VENV       := $(CURDIR)/.venv
TEXEXP_SRC := book/docs/_static/tex_exp_to_png
PY         := $(VENV)/bin/python
export PATH := $(LOCAL_DIR)/bin:$(VENV)/bin:$(PATH)   # so demos see texExpToPng + venv
```

| target | does |
| --- | --- |
| `deps` | run `./install-deps.sh` (distro-detect + system packages) |
| `venv` | `python3 -m venv $(VENV)`; `pip install -U pip`; `pip install -e .` + `-r requirements.txt` |
| `texexp` | `meson setup $(LOCAL_DIR)/build-texexp $(TEXEXP_SRC) --prefix=$(LOCAL_DIR)`; `meson compile`/`install` → `$(LOCAL_DIR)/bin/texExpToPng` |
| `local` (default) | `deps` → `venv` → `texexp` (the full one-shot setup) |
| `run` | run a demo with the local env, e.g. `DEMO=src/modelviewprojection/mathdemos/crossproduct.py`; `$(PY) $(DEMO)` (PATH already exports texExpToPng) |
| `verify` | smoke checks: `$(PY) -c "import modelviewprojection"`, `texExpToPng --help`, render one label PNG |
| `clean-local` | `rm -rf $(VENV) $(LOCAL_DIR)` |
| `help` | the standard `##`-grep help one-liner |

Notes:
- `deps` needs `sudo` (system packages) — the script handles that; the rest of the
  targets are unprivileged.
- `texexp` is **optional/non-fatal**: if its build deps/TeX are missing, warn and
  continue (demos still run, labels just skip — matching the runtime
  `shutil.which` graceful degradation already in `_labels.py`).
- Keep it a *separate* file so the container `Makefile` is untouched; `make -f
  Makefile.local local`.

## `install-deps.sh` — distro detection + per-distro packages

Shape (mirrors mario64/Ghostship's per-distro doc sections, but as one auto-detecting
script):

```sh
#!/usr/bin/env bash
set -euo pipefail
if [ "$(uname -s)" = "Darwin" ]; then
  brew install ...           # macOS
  exit 0
fi
. /etc/os-release            # sets $ID and $ID_LIKE
case "$ID $ID_LIKE" in
  *debian*|*ubuntu*)  sudo apt-get update && sudo apt-get install -y <DEB_PKGS> ;;
  *fedora*|*rhel*)    sudo dnf install -y <FEDORA_PKGS> ;;
  *arch*)             sudo pacman -S --needed <ARCH_PKGS> ;;
  *suse*)             sudo zypper install -y <SUSE_PKGS> ;;
  *) echo "Unsupported distro '$ID'; install equivalents of: <generic list>"; exit 1 ;;
esac
```

### Dependency set (what mvp actually needs locally)

Three groups:
- **Run the demos:** Python 3 + venv + pip; OpenGL + windowing runtime (mesa libGL,
  X11 + xkbcommon + Wayland libs so glfw/imgui-bundle can open a window). The
  Python deps (glfw, imgui-bundle, numpy, pyopengl, pillow, gacalc, …) come from
  the venv via `pip install -e . -r requirements.txt`, **not** the system.
- **Build texExpToPng:** C toolchain + `glib2` dev + `meson` + `ninja` + `pkgconf`.
- **Run texExpToPng:** a LaTeX subset — `latex`, `dvipng`, `standalone.cls`,
  `amsmath.sty`.

Concrete per-distro mapping (to be finalized + validated during implementation —
the texExpToPng halves are already proven in the README work):

| group | Debian/Ubuntu (apt) | Fedora (dnf) | Arch (pacman) | openSUSE (zypper) |
| --- | --- | --- | --- | --- |
| python | `python3 python3-venv python3-pip` | `python3 python3-pip` | `python python-pip` | `python3 python3-pip python3-virtualenv` |
| GL/X11/Wayland | `libgl1-mesa-dev libx11-dev libxkbcommon-dev libwayland-dev libxrandr-dev libxinerama-dev libxcursor-dev libxi-dev` | `mesa-libGL-devel libX11-devel libxkbcommon-devel wayland-devel libXrandr-devel libXinerama-devel libXcursor-devel libXi-devel` | `mesa libx11 libxkbcommon wayland libxrandr libxinerama libxcursor libxi` | `Mesa-libGL-devel libX11-devel libxkbcommon-devel wayland-devel libXrandr-devel …` |
| texExpToPng build | `build-essential libglib2.0-dev meson ninja-build pkg-config` | `gcc gcc-c++ glib2-devel meson ninja-build pkgconf-pkg-config` | `gcc glib2 meson ninja pkgconf` | `gcc gcc-c++ glib2-devel meson ninja pkg-config` |
| LaTeX (labels) | `texlive-latex-base texlive-latex-extra dvipng` | `texlive-scheme-basic texlive-standalone texlive-amsmath texlive-dvipng` | `texlive-basic texlive-latexextra texlive-binextra` | `texlive-latex texlive-standalone texlive-dvipng` |
| macOS (brew) | — | — | — | `python glib meson ninja pkg-config` + `--cask mactex-no-gui` (latex/dvipng) |

(The Debian/Ubuntu and Fedora texExpToPng package sets are already verified working
end-to-end from the README task; Arch/openSUSE/macOS names need a validation pass.)

## Plan / steps

- [ ] Write `install-deps.sh` (distro detect + the table above), `chmod +x`.
- [ ] Write `Makefile.local` (targets above; `PATH` export; non-fatal `texexp`).
- [ ] Add `.venv/` and `.local/` to `.gitignore`.
- [ ] Validate end-to-end on **Fedora** and **Debian/Ubuntu** in throwaway
      containers (same method used to validate the README install blocks): run
      `install-deps.sh`, `make -f Makefile.local local`, then `make -f
      Makefile.local verify`. Headless GL can't be fully exercised in-sandbox, but
      import + texExpToPng render can. Best-effort check Arch/openSUSE package names.
- [ ] Once working, **update README.md**: a "Local build (no container)" section —
      `./install-deps.sh` then `make -f Makefile.local local`, then `make -f
      Makefile.local run DEMO=…`. Copy-paste-able, like the texExpToPng section.

## Open questions

- venv tool: plain `python3 -m venv` + `pip` (no extra deps), or `uv` (faster, but
  another thing to install)? Default: stdlib `venv` + `pip` for least friction;
  `uv` if already present.
- Should `Makefile.local`'s `run` default to a specific demo (crossproduct?) or
  require `DEMO=`? (Lean: default to a simple demo, allow override.)
- How aggressively to validate non-Fedora/Debian distros — Arch/openSUSE/macOS
  package names are best-effort unless we can test them.
- macOS: full MacTeX is huge; `mactex-no-gui` or BasicTeX + `tlmgr install
  standalone dvipng`? (BasicTeX is far smaller — probably better.)
