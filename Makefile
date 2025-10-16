.DEFAULT_GOAL := help

CONTAINER_CMD = podman
CONTAINER_NAME = modelviewprojection-html
SPYDER_CONTAINER_NAME = modelviewprojection-spyder
FILES_TO_MOUNT = -v $(shell pwd):/mvp/:Z \
		-v ./entrypoint/entrypoint.sh:/entrypoint.sh:Z \
		-v ./entrypoint/format.sh:/format.sh:Z \
		-v ./output/:/output/:Z \
		-v ./entrypoint/.bashrc:/root/.bashrc:Z

USE_X = -e DISPLAY=$(DISPLAY) \
	-v /tmp/.X11-unix:/tmp/.X11-unix \
	--security-opt label=type:container_runtime_t


.PHONY: all
all: clean image html ## Build the HTML and PDF from scratch in Debian Bulleye

.PHONY: image
image: ## Build a podman image in which to build the book
	$(CONTAINER_CMD) build -t $(CONTAINER_NAME) .

.PHONY: spyderimage
spyderimage: image  ## Build a podman image in which to run the demos
	$(CONTAINER_CMD) build -t $(SPYDER_CONTAINER_NAME) -f Dockerfile.spyder


.PHONY: html
html: image ## Build the html from the sphinx source
	printf "This documentation was generated from from commit " > book/docs/version.txt
	git rev-parse HEAD >> book/docs/version.txt
	$(CONTAINER_CMD) run -it --rm  \
		$(FILES_TO_MOUNT) \
		$(CONTAINER_NAME)


.PHONY: clean
clean: ## Delete the output directory, cleaning out the HTML and the PDF
	rm -rf output/*

.PHONY: shell
shell:  ## Get Shell into a ephermeral container made from the image
	$(CONTAINER_CMD) run -it --rm \
		--entrypoint /bin/bash \
		$(FILES_TO_MOUNT) \
		-v ./entrypoint/shell.sh:/shell.sh:Z \
		$(USE_X) \
		$(CONTAINER_NAME) \
		/shell.sh

.PHONY: jupyter
jupyter:  ## Get Shell into a ephermeral container made from the image
	$(CONTAINER_CMD) run -it --rm \
		--entrypoint /bin/bash \
		$(FILES_TO_MOUNT) \
		-v ./entrypoint/jupyter.sh:/jupyter.sh:Z \
		$(USE_X) \
		$(CONTAINER_NAME) \
		/jupyter.sh



spyder: ## Run Spyder
	$(CONTAINER_CMD) run -it --rm \
		--entrypoint /bin/bash \
		$(FILES_TO_MOUNT) \
		-v ./entrypoint/spyder.sh:/spyder.sh:Z \
		$(USE_X) \
		$(SPYDER_CONTAINER_NAME) \
		/spyder.sh



.PHONY: help
help:
	@grep --extended-regexp '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
