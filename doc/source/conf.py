# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'StructuralGT'
copyright = '2023, Reagents of the University of Michigan'
author = 'Alain Kadar'
release = '2.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx.ext.autosummary","sphinxcontrib.bibtex",]

# For sphinxcontrib.bibtex (as of v2.0).
bibtex_bibfiles = ["reference/StructuralGT.bib"]

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']

autodoc_member_order = 'bysource'
autodoc_default_options = {
    "inherited-members": True,
    "show-inheritance": True,
}
