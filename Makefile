all: clean image html

image:
	podman build -t modelviewprojection-html .

html:
	podman run -it --rm -v ./output/:/output/:Z modelviewprojection-html


clean:
	rm -rf output/*

shell:
	podman run -it --rm \
		--entrypoint /bin/bash \
		-v ./output/:/output/:Z \
		modelviewprojection-html
