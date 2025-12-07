# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#

import os
import sys

sys.path.insert(0, os.path.abspath("."))


# on_rtd is whether we are on readthedocs.org, this line of code grabbed
# from docs.readthedocs.org
on_rtd = os.environ.get("READTHEDOCS", None) == "True"


html_theme = "furo"

html_static_path = ["_static"]

html_css_files = [
    "custom.css",  # Your override
]

html_theme_options = {
    "light_css_variables": {},
}


# -- Project information -----------------------------------------------------

project = "Model View Projection"
copyright = "2020-2025, William Emerison Six"
author = "William Emerison Six"

# The full version, including alpha/beta/rc tags
release = "0.0.2"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.

imgmath_image_format = "svg"
imgmath_font_size = 20  # for font size 14
imgmath_latex_preamble = "\\usepackage{amsmath}\n" + "\\usepackage{xcolor}\n"


latex_elements = {
    "preamble": r"""
\usepackage{graphicx}
\usepackage{float}
\makeatletter
\def\fps@figure{H}  % Force images to stay in their position
\setkeys{Gin}{width=0.5\textwidth}  % Set default image width
\makeatother
"""
}

extensions = [
    "sphinx.ext.imgconverter",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",  # Required for parsing field descriptions
    "sphinx.ext.viewcode",
    "sphinx.ext.mathjax",
    "sphinxcontrib.bibtex",
    "nbsphinx",
    "myst_nb",
]

nb_execution_timeout = 600 # timeout of ten minutes
myst_enable_extensions = [
    "colon_fence",
    "dollarmath",
]

bibtex_bibfiles = ["references.bib"]


# conf.py
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__, __call__, __add__, __sub__, __mul__, __rmul__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}

glossary_sort = True

imgconverter_converters = {
    "svg": "inkscape --without-gui --export-type=pdf --export-filename={out} {in}"
}


mathjax3_config = {
    "tex": {
        "inlineMath": [["$", "$"], ["\\(", "\\)"]],
        "displayMath": [["$$", "$$"], ["\\[", "\\]"]],
    },
}


# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#


# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
html_css_files = ["custom.css"]
