.DEFAULT_GOAL := shell

# Modify these to 0 if you want a quicker build and don't
# need the features
BUILD_DOCS ?= 1
USE_EMACS ?= 1
USE_JUPYTER ?= 1
USE_SPYDER ?= 0
USE_X_WINDOWS ?= 1

CONTAINER_CMD = podman
CONTAINER_NAME = modelviewprojection

TMUX_FILE := $(HOME)/.tmux.conf
TMUX_REAL_PATH := $(shell readlink -f $(TMUX_FILE))
TMUX_MOUNT := $(shell if [ -f $(TMUX_REAL_PATH) ]; then echo "-v $(TMUX_REAL_PATH):/root/.tmux.conf:Z" ; fi)

GITCONFIG_FILE := $(HOME)/.gitconfig
GITCONFIG_REAL_PATH := $(shell readlink -f $(GITCONFIG_FILE))
GITCONFIG_MOUNT := $(shell if [ -f $(GITCONFIG_REAL_PATH) ]; then echo "-v $(GITCONFIG_REAL_PATH):/root/.gitconfig:Z" ; fi)

GNUPG_FILE := $(HOME)/.gnupg
GNUPG_REAL_PATH := $(shell readlink -f $(GNUPG_FILE))
GNUPG_MOUNT := $(shell if [ -d $(GNUPG_REAL_PATH) ]; then echo "-v $(GNUPG_REAL_PATH):/root/.gnupg:Z" ; fi)



FILES_TO_MOUNT = -v $(shell pwd):/mvp/:Z \
		-v ./entrypoint/entrypoint.sh:/entrypoint.sh:Z \
		-v ./entrypoint/format.sh:/usr/local/bin/format.sh:Z \
		-v ./entrypoint/jupyter.sh:/usr/local/bin/jupyter.sh:Z \
		-v ./entrypoint/spyder.sh:/usr/local/bin/spyder.sh:Z \
		-v ./entrypoint/shell.sh:/usr/local/bin/shell.sh:Z \
		-v ./output/:/output/:Z \
                $(TMUX_MOUNT) \
                $(GITCONFIG_MOUNT) \
                $(GNUPG_MOUNT)

USE_X = -e DISPLAY=$(DISPLAY) \
	-v /tmp/.X11-unix:/tmp/.X11-unix \
	--security-opt label=type:container_runtime_t
# GPU render node for hardware GL (Wayland EGL / X11); skipped if /dev/dri is absent.
DRI_DEVICE := $(shell [ -d /dev/dri ] && echo "--device /dev/dri")

# Wayland for the GUI demos, WITHOUT breaking imgui_bundle.  The demos' `import glfw`
# (PyPI) loads first, then imgui_bundle's native lib -- and BOTH bind the same soname
# `libglfw.so.3`.  PyPI glfw's *Wayland-only* build lacks `glfwGetX11Window` (which
# imgui_bundle needs), so forcing that variant crashes imgui_bundle.  Instead point
# PyPI glfw at the SYSTEM Fedora libglfw (a DUAL X11+Wayland build, from the `glfw`
# rpm); it loads first, so imgui_bundle binds the same dual lib (has the X11 symbol)
# and GLFW picks Wayland at runtime via WAYLAND_DISPLAY.  Needs libwayland-egl/
# libwayland-client/libxkbcommon (Dockerfile USE_X_WINDOWS block).
WAYLAND_FLAGS_FOR_CONTAINER = -e "XDG_SESSION_TYPE=wayland" \
                              -e "WAYLAND_DISPLAY=${WAYLAND_DISPLAY}" \
                              -e "XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR}" \
                              -e "PYGLFW_LIBRARY=/usr/lib64/libglfw.so.3" \
                              -v "${XDG_RUNTIME_DIR}:${XDG_RUNTIME_DIR}" \
                              $(DRI_DEVICE)


# USE_EMACS=1 (the default) bind-mounts the vendored host elpa tree into the
# container so an interactive `make shell` can *use* the vendored packages (:U
# chowns it to the container user, :z relabels for SELinux). Set USE_EMACS=0 to
# skip the mount. To *refresh* the vendored packages, use `make
# update-emacs-packages` below.
ifeq ($(USE_EMACS), 1)
  ELPA_MOUNT= -v $(CURDIR)/entrypoint/dotfiles/.emacs.d/elpa:/root/.emacs.d/elpa:U,z
else
  ELPA_MOUNT=
endif


EXPOSE_PORT = -p 8888:8888


.PHONY: all
all: image ## Build the HTML and PDF from scratch in Debian Bulleye

.PHONY: image
image: ## Build a podman image in which to build the book
	# build the container
	$(CONTAINER_CMD) build  \
                         --build-arg BUILD_DOCS=$(BUILD_DOCS) \
                         --build-arg USE_EMACS=$(USE_EMACS) \
                         --build-arg USE_JUPYTER=$(USE_JUPYTER) \
                         --build-arg USE_SPYDER=$(USE_SPYDER) \
                         --build-arg USE_X_WINDOWS=$(USE_X_WINDOWS) \
                         $(ELPA_MOUNT) \
                         -t $(CONTAINER_NAME) \
                         .


.PHONY: clean
clean: ## Delete the output directory, cleaning out the HTML and the PDF
	rm -rf output/*

.PHONY: shell
shell: ## Get Shell into a ephermeral container made from the image
	$(CONTAINER_CMD) run -it --rm \
		--entrypoint /bin/bash \
		$(FILES_TO_MOUNT) \
		$(USE_X) \
		$(WAYLAND_FLAGS_FOR_CONTAINER) \
		$(EXPOSE_PORT) \
                $(ELPA_MOUNT) \
		$(CONTAINER_NAME) \
		/usr/local/bin/shell.sh


.PHONY: jupyter
jupyter: image ## Run Jupyter Lab in a container (open http://127.0.0.1:8888/lab)
	@echo ""
	@echo "  Jupyter Lab is starting in the container."
	@echo "  Open this in your web browser:  http://127.0.0.1:8888/lab"
	@echo "  (no token/password needed; press Ctrl-C here to stop the server)"
	@echo ""
	$(CONTAINER_CMD) run -it --rm \
		--entrypoint /bin/bash \
		$(FILES_TO_MOUNT) \
		$(USE_X) \
		$(WAYLAND_FLAGS_FOR_CONTAINER) \
		$(EXPOSE_PORT) \
                $(ELPA_MOUNT) \
		$(CONTAINER_NAME) \
		/usr/local/bin/jupyter.sh


# Format/lint/typecheck the source INSIDE the container (the image's pinned ruff +
# ty).  loadpackages.sh installs the package editable (so ty resolves
# `modelviewprojection`); then format.sh runs ruff check --fix / ruff format / ty
# check -- the same pair the shell-exit trap runs.  We must `cd /mvp` HERE:
# format.sh uses relative paths (`ruff check src`), and loadpackages.sh's own
# `cd /mvp` is subprocess-local so it doesn't carry over to format.sh.
.PHONY: format
format: image ## (container) ruff + ty over the source (loadpackages.sh + format.sh)
	$(CONTAINER_CMD) run --rm \
		--entrypoint /bin/bash \
		$(FILES_TO_MOUNT) \
		$(CONTAINER_NAME) \
		-c 'cd /mvp && loadpackages.sh && format.sh'


# Refresh the vendored Emacs packages. Forces USE_EMACS=1 and rebuilds the image
# first (so it doesn't matter whether the last `make image` set USE_EMACS). Then,
# in the container, wipes the elpa tree and reinstalls from MELPA into the host's
# bind-mounted entrypoint/dotfiles/.emacs.d/elpa (the current
# install-melpa-packages.el is mounted read-only, so edits to it take effect
# without a rebuild). Finally strips compiled *.elc/*.eln (regenerated,
# machine-specific build artifacts) and force-stages the whole tree (git add -A
# -f overrides .gitignore's *.elc/*.eln/... patterns) so the vendored tree is
# ready to commit. Needs network access.
.PHONY: update-emacs-packages
update-emacs-packages: ## USE_EMACS=1: rebuild image, wipe+reinstall elpa, strip *.elc/*.eln, git add -f
	$(MAKE) image USE_EMACS=1
	$(CONTAINER_CMD) run --rm \
		-v $(CURDIR)/entrypoint/dotfiles/.emacs.d/elpa:/root/.emacs.d/elpa:U,z \
		-v $(CURDIR)/entrypoint/dotfiles/.emacs.d/install-melpa-packages.el:/root/.emacs.d/install-melpa-packages.el:ro,z \
		--entrypoint /bin/bash \
		$(CONTAINER_NAME) \
		-c 'set -e; find /root/.emacs.d/elpa -mindepth 1 -delete; \
		    emacs --batch --load /root/.emacs.d/install-melpa-packages.el'
	cd $(CURDIR)/entrypoint/dotfiles/.emacs.d/elpa && \
		find . \( -iname '*.elc' -o -iname '*.eln' \) -delete && \
		git add -A -f .
	@echo "Done: reinstalled packages, stripped *.elc/*.eln, staged elpa -- review and commit."


html: image ## Build the html from the sphinx source
	printf "This documentation was generated from from commit " > book/docs/version.txt
	git rev-parse HEAD >> book/docs/version.txt
	$(CONTAINER_CMD) run -it --rm  \
                $(FILES_TO_MOUNT) \
                $(CONTAINER_NAME)


.PHONY: image-export
image-export: ## export the OCI image to a timestamped tar in the repo root
	$(CONTAINER_CMD) save $(CONTAINER_NAME) -o $(CONTAINER_NAME)-$(shell date +%m-%d-%Y_%H-%M-%S).tar

.PHONY: image-import
image-import: ## import an OCI image tar: make image-import FILE=foo.tar
	$(CONTAINER_CMD) load -i $(FILE)


.PHONY: help
help:
	@grep --extended-regexp '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
