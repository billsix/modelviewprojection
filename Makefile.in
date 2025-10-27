.DEFAULT_GOAL := @DEFAULT_MAKE_GOAL@

BUILD_DOCS=@BUILD_DOCS_FLAG@
BUILD_PDF=@BUILD_PDF_FLAG@
BUILD_HTML=@BUILD_HTML_FLAG@
USE_X_WINDOWS=@USE_X_WINDOWS@
USE_EMACS=@USE_EMACS@
USE_IMGUI=@USE_IMGUI@
USE_JUPYTER=@USE_JUPYTER@
USE_SPYDER=@USE_SPYDER@

CONTAINER_CMD = podman
CONTAINER_NAME = modelviewprojection-html

PACKAGE_CACHE_ROOT = ~/.cache/packagecache/fedora/42

DNF_CACHE_TO_MOUNT = -v $(PACKAGE_CACHE_ROOT)/var/cache/libdnf5:/var/cache/libdnf5:Z \
	             -v $(PACKAGE_CACHE_ROOT)/var/lib/dnf:/var/lib/dnf:Z

FILES_TO_MOUNT = -v $(shell pwd):/mvp/:Z \
		-v ./entrypoint/entrypoint.sh:/entrypoint.sh:Z \
		-v ./entrypoint/format.sh:/format.sh:Z \
		-v ./output/:/output/:Z \
		-v ./entrypoint/.bashrc:/root/.bashrc:Z \
		$(DNF_CACHE_TO_MOUNT)

USE_X = -e DISPLAY=$(DISPLAY) \
	-v /tmp/.X11-unix:/tmp/.X11-unix \
	--security-opt label=type:container_runtime_t
WAYLAND_FLAGS_FOR_CONTAINER = -e "WAYLAND_DISPLAY=${WAYLAND_DISPLAY}" \
                              -e "XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR}" \
                              -v "${XDG_RUNTIME_DIR}:${XDG_RUNTIME_DIR}"


.PHONY: all
all: image ## Build the HTML and PDF from scratch in Debian Bulleye

.PHONY: image
image: ## Build a podman image in which to build the book
	# cache rpm packages
	mkdir -p $(PACKAGE_CACHE_ROOT)/var/cache/libdnf5
	mkdir -p $(PACKAGE_CACHE_ROOT)/var/lib/dnf
	# build the container
	$(CONTAINER_CMD) build  \
                         -t $(CONTAINER_NAME) \
                         $(DNF_CACHE_TO_MOUNT) \
                         .



ifeq ($(BUILD_HTML),1)
.PHONY: html
html: image ## Build the html from the sphinx source
	printf "This documentation was generated from from commit " > book/docs/version.txt
	git rev-parse HEAD >> book/docs/version.txt
	$(CONTAINER_CMD) run -it --rm  \
		$(FILES_TO_MOUNT) \
		$(CONTAINER_NAME)
endif


.PHONY: clean
clean: ## Delete the output directory, cleaning out the HTML and the PDF
	rm -rf output/*

.PHONY: shell
shell: image ## Get Shell into a ephermeral container made from the image
	$(CONTAINER_CMD) run -it --rm \
		--entrypoint /bin/bash \
		$(FILES_TO_MOUNT) \
		-v ./entrypoint/shell.sh:/shell.sh:Z \
		$(USE_X) \
		$(WAYLAND_FLAGS_FOR_CONTAINER) \
		$(CONTAINER_NAME) \
		/shell.sh

ifeq ($(USE_JUPYTER),1)
.PHONY: jupyter
jupyter: image ## Get Shell into a ephermeral container made from the image
	$(CONTAINER_CMD) run -it --rm \
		--entrypoint /bin/bash \
		$(FILES_TO_MOUNT) \
		-v ./entrypoint/jupyter.sh:/jupyter.sh:Z \
		$(USE_X) \
		$(WAYLAND_FLAGS_FOR_CONTAINER) \
		$(CONTAINER_NAME) \
		/jupyter.sh
endif


ifeq ($(USE_SPYDER),1)
spyder: image ## Run Spyder
	$(CONTAINER_CMD) run -it --rm \
		--entrypoint /bin/bash \
		$(FILES_TO_MOUNT) \
		-v ./entrypoint/spyder.sh:/spyder.sh:Z \
		$(USE_X) \
		$(WAYLAND_FLAGS_FOR_CONTAINER) \
		$(CONTAINER_NAME) \
		/spyder.sh
endif



.PHONY: help
help:
	@grep --extended-regexp '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
