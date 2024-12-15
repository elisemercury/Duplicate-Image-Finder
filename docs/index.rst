difPy Guide
===================================

.. _difPy:

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Getting started

   /getting_started/installation
   /getting_started/basic_usage
   /getting_started/cli_usage
   /getting_started/output

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Methods and parameters

   /methods/build
   /methods/search
   /methods/search_moveto
   /methods/search_delete

.. toctree::
   :maxdepth: 2
   :caption: Contributing to difPy

   /contributing
   /support

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Further Resources

   /faq

.. image:: https://img.shields.io/badge/dif-Py-blue?style=flat&logo=python&labelColor=white&logoWidth=20.svg/"
   :target: https://github.com/elisemercury/Duplicate-Image-Finder

**difPy** is a Python package that automates the search for duplicate/similar images.

.. note::

   ✨ Update to `difPy v4 <https://pypi.org/project/difPy/>`_ for up to **10x performance increases** to previous versions! :ref:`What's new in v4?`

difPy searches for images in **one or more different directories**, compares the images it found and checks whether these are duplicates. It then outputs the **image files classified as duplicates** as well as the **images having the lowest resolutions**, so you know which of the duplicate images are safe to be deleted. You can then either delete them manually, or let difPy delete them for you.

difPy does not compare images based on their hashes. It compares them based on their tensors i. e. the image content. This allows difPy to **not only search for duplicate images, but also for similar images**.

difPy leverages Python's multiprocessing capabilities and is therefore able to perform at high performance even on large datasets. 

View difPy on `GitHub <https://github.com/elisemercury/Duplicate-Image-Finder>`_ and `PyPi <https://pypi.org/project/difPy/>`_.

Guide Content
--------

.. toctree::
   :maxdepth: 3

   usage
   contributing
   faq

------------

.. include:: /misc/support_difpy.rst