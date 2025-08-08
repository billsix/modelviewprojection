.DEFAULT_GOAL := help

PODMAN_CMD = podman
CONTAINER_NAME = modelviewprojection-html
SPYDER_CONTAINER_NAME = modelviewprojection-spyder
FILES_TO_MOUNT = -v ./assignments:/mvp/assignments/:Z \
		-v ./book:/mvp/book/:Z \
		-v ./entrypoint/entrypoint.sh:/entrypoint.sh:Z \
		-v ./entrypoint/format.sh:/format.sh:Z \
		-v ./pyproject.toml:/mvp/pyproject.toml:Z \
		-v ./pytest.ini:/mvp/pytest.ini:Z \
		-v ./setup.py:/mvp/setup.py:Z \
		-v ./src:/mvp/src/:Z \
		-v ./tests/:/mvp/tests/:Z \
		-v ./output/:/output/:Z
USE_X = -e DISPLAY=$(DISPLAY) \
	-v /tmp/.X11-unix:/tmp/.X11-unix


.PHONY: all
all: clean image html ## Build the HTML and PDF from scratch in Debian Bulleye

.PHONY: image
image: ## Build a podman image in which to build the book
	printf "This documentation was generated from from commit " > book/docs/version.txt
	git rev-parse HEAD >> book/docs/version.txt
	$(PODMAN_CMD) build -t $(CONTAINER_NAME) .

.PHONY: spyderimage
spyderimage: image  ## Build a podman image in which to run the demos
	$(PODMAN_CMD) build -t $(SPYDER_CONTAINER_NAME) -f Dockerfile.spyder


.PHONY: html
html: image ## Build the html from the sphinx source
	$(PODMAN_CMD) run -it --rm  \
		$(FILES_TO_MOUNT) \
		$(CONTAINER_NAME)


.PHONY: clean
clean: ## Delete the output directory, cleaning out the HTML and the PDF
	rm -rf output/*

.PHONY: shell
shell: image ## Get Shell into a ephermeral container made from the image
	$(PODMAN_CMD) run -it --rm \
		--entrypoint /bin/bash \
		$(FILES_TO_MOUNT) \
		-v ./entrypoint/shell.sh:/shell.sh:Z \
		$(CONTAINER_NAME) \
		/shell.sh

.PHONY: jupyter
jupyter: image ## Get Shell into a ephermeral container made from the image
	$(PODMAN_CMD) run -it --rm \
		--entrypoint /bin/bash \
		$(FILES_TO_MOUNT) \
		-v ./entrypoint/jupyter.sh:/jupyter.sh:Z \
		$(USE_X) \
		$(CONTAINER_NAME) \
		/jupyter.sh



spyder: spyderimage ## Run Spyder
	$(PODMAN_CMD) run -it --rm \
		--entrypoint /bin/bash \
		$(FILES_TO_MOUNT) \
		-v ./entrypoint/spyder.sh:/spyder.sh:Z \
		$(USE_X) \
		$(SPYDER_CONTAINER_NAME) \
		/spyder.sh



.PHONY: help
help:
	@grep --extended-regexp '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
