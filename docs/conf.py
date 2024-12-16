# Configuration file for the Sphinx documentation builder.

# -- Project information

project = 'difPy Guide'
copyright = '2024, Elise Landman'
author = 'Elise Landman'

release = 'v4.1.3'
version = 'v4.1.3'

# -- General configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'sphinx_rtd_theme',
    #-- 'sphinxcontrib.googleanalytics'
]

# -- googleanalytics_id = 'G-X002SSZTWC'

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
}
intersphinx_disabled_domains = ['std']

templates_path = ['_templates']

# -- Options for HTML output

html_theme = 'sphinx_rtd_theme'

html_static_path = ['_static']
html_logo = "static/logos/logo.png"
html_theme_options = {
    'logo_only': True,
    'display_version': False,
}

# -- Options for EPUB output
epub_show_urls = 'footnote'

def setup(app):
   app.add_css_file('static/css/custom.css')