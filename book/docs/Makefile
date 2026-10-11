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

.PHONY: help Makefile spellcheck

# Non-interactive spellcheck (Option A, 2026-10-12): aspell `list` over the .rst
# prose, reusing mvp_dict.pws.  It is NO LONGER a prerequisite of the Sphinx
# targets, so the doc build runs headless (the old `aspell check` opened an
# interactive curses UI and failed with "Stdin not a terminal" in CI / nested
# containers).  Run it on its own: `make spellcheck`.  (tools/spellcheck.sh)
spellcheck:
	../../tools/spellcheck.sh

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	cd _static/ && make
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	cd _static/ && cp *.png ../_build/html/_static/
