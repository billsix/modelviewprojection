.DEFAULT_GOAL := help

.PHONY: all
all: clean image html ## Build the HTML and PDF from scratch in Debian Bulleye

.PHONY: image
image: ## Build a Podman image in which to build the book
	podman build -t modelviewprojection-html .

.PHONY: html
html: image ## Build the html from the sphinx source
	printf "This documentation was generated from from commit " > book/docs/version.txt
	git rev-parse HEAD >> book/docs/version.txt
	podman run -it --rm -v ./output/:/output/:Z modelviewprojection-html


.PHONY: clean
clean: ## Delete the output directory, cleaning out the HTML and the PDF
	rm -rf output/*

.PHONY: shell
shell: image ## Get Shell into a ephermeral container made from the image
	podman run -it --rm \
		--entrypoint /bin/bash \
		-v ./output/:/output/:Z \
		modelviewprojection-html

.PHONY: help
help:
	@grep --extended-regexp '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
