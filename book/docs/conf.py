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

# import sys
# sys.path.insert(0, os.path.abspath('.'))

# on_rtd is whether we are on readthedocs.org, this line of code grabbed from docs.readthedocs.org
on_rtd = os.environ.get("READTHEDOCS", None) == "True"

if not on_rtd:  # only import and set the theme if we're building docs locally
    import sphinx_rtd_theme

    html_theme = "sphinx_rtd_theme"
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

    # Override default css to get a larger width for local build
    def setup(app):
        # app.add_javascript("custom.js")
        app.add_css_file("css/my_theme.css")

else:
    # Override default css to get a larger width for ReadTheDoc build
    html_context = {
        "css_files": [
            "https://media.readthedocs.org/css/sphinx_rtd_theme.css",
            "https://media.readthedocs.org/css/readthedocs-doc-embed.css",
            "_static/css/my_theme.css",
        ],
    }


# -- Project information -----------------------------------------------------

project = "Model View Projection"
copyright = "2020-2024, William Emerison Six"
author = "William Emerison Six"

# The full version, including alpha/beta/rc tags
release = "0.0.1"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.

imgmath_image_format = "svg"
imgmath_font_size = 20  # for font size 14
imgmath_latex_preamble = "\\usepackage{amsmath}\n" + "\\usepackage{xcolor}\n"

extensions = ["sphinx.ext.imgmath"]

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

html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
