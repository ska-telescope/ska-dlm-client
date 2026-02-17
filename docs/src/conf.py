"""Configuration file for Sphinx."""
import os
import sys

sys.path.insert(0, os.path.abspath("../../src"))

project = "ska-dlm-client"
copyright = "2024, ICRAR"
author = "Mark Boulton <mark.boulton@uwa.edu.au>"
release = "1.2.3"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
    "myst_parser",
]

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
source_suffix = ['.rst', '.md']

exclude_patterns = []

html_css_files = [
    'css/custom.css',
]

html_theme = "ska_ser_sphinx_theme"
html_theme_options = {}

# autodoc_mock_imports = [
# ]

intersphinx_mapping = {'python': ('https://docs.python.org/3.10', None)}

nitpicky = True

# nitpick_ignore = [
# ]
