# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	cd _build/html && \
           find . -iname '*pyc' | xargs rm && \
	   mv _static static && \
           grep -ir '_static' * | cut -d ':' -f 1 | uniq | xargs sed -i -e 's/_static/static/g' && \
           mv _images images && \
           grep -ir '_images' * | cut -d ':' -f 1 | uniq | xargs sed -i -e 's/_images\//images\//g'
