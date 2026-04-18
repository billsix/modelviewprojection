.DEFAULT_GOAL := shell

# Modify these to 0 if you want a quicker build and don't
# need the features
BUILD_DOCS ?= 1
USE_EMACS ?= 1
USE_IMGUI ?= 1
USE_JUPYTER ?= 1
USE_SPYDER ?= 1
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
                $(GNUPG_MOUNT) \
		$(DNF_CACHE_TO_MOUNT)

USE_X = -e DISPLAY=$(DISPLAY) \
	-v /tmp/.X11-unix:/tmp/.X11-unix \
	--security-opt label=type:container_runtime_t
WAYLAND_FLAGS_FOR_CONTAINER = -e "XDG_SESSION_TYPE=wayland" \
                              -e "WAYLAND_DISPLAY=${WAYLAND_DISPLAY}" \
                              -e "XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR}" \
                              -v "${XDG_RUNTIME_DIR}:${XDG_RUNTIME_DIR}"


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
                         --build-arg USE_IMGUI=$(USE_IMGUI) \
                         --build-arg USE_JUPYTER=$(USE_JUPYTER) \
                         --build-arg USE_SPYDER=$(USE_SPYDER) \
                         --build-arg USE_X_WINDOWS=$(USE_X_WINDOWS) \
                         $(ELPA_MOUNT) \
                         -t $(CONTAINER_NAME) \
                         $(PACKAGE_CACHE) \
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


html: image ## Build the html from the sphinx source
	printf "This documentation was generated from from commit " > book/docs/version.txt
	git rev-parse HEAD >> book/docs/version.txt
	$(CONTAINER_CMD) run -it --rm  \
                $(FILES_TO_MOUNT) \
                $(CONTAINER_NAME)


image-export: ## export the OCI image
	podman save $(CONTAINER_NAME) -o $(CONTAINER_NAME)-$(shell date +%m-%d-%Y_%H-%M-%S).tar

image-import: ## import the OCI image, "make image-import FILE=foo.tar"
	podman load -i $(FILE)


.PHONY: help
help:
	@grep --extended-regexp '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
