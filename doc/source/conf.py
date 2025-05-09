# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import sys
import os

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "StructuralGT"
copyright = "2025, Reagents of the University of Michigan"
author = "Alain Kadar"
release = "0.2"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
 "sphinx.ext.autosummary",
 "sphinxcontrib.bibtex",
]

sys.path.insert(0, os.path.abspath("../../"))

# For sphinxcontrib.bibtex (as of v2.0).
bibtex_bibfiles = ["reference/StructuralGT.bib"]

templates_path = ["_templates"]
exclude_patterns = []

autodoc_mock_imports = [
        "StructuralGT._average_nodal_connectivity_cast",
        "StructuralGT._boundary_betweenness_cast",
        "StructuralGT._random_boundary_betweenness_cast",
        "StructuralGT._vertex_boundary_betweenness_cast",
        ]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"

autodoc_member_order = "bysource"
autodoc_default_options = {
 "inherited-members": True,
 "show-inheritance": True,
}
