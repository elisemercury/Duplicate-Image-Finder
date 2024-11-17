Using difPy
=====

.. _using difPy:

**difPy** is a Python package that automates the search for duplicate/similar images.

.. _installation:

Installation
------------

To use difPy, first install it using pip:

.. code-block:: console

   (.venv) $ pip install difPy

View difPy on `PyPi <https://pypi.org/project/difPy/>`_.

.. _usage:

Basic Usage
----------------

difPy is split into two main processes: 

* ``build`` which builds the image repository from the directories provided (:ref:`difPy.build`) and 
* ``search`` which performs the actual search operation (:ref:`difPy.search`). 

First we need to build the ``dif`` object:

.. code-block:: python

   import difPy
   dif = difPy.build("C:/Path/to/Folder/")

And then we can perform one or more different searches on the same ``dif`` object:

.. code-block:: python

   search_duplicates = difPy.search(dif, similarity="duplicates")
   search_similar = difPy.search(dif, similarity= "similar")

We can obtain the search results as follows (see :ref:`output`):

.. code-block:: python

   search_duplicates.result
   search_similar.result

difPy supports searching for duplicate and similar images within a single or multiple directories.

I. Single Folder Search
^^^^^^^^^^

Search for duplicate images in a single folder:

.. code-block:: python

   import difPy
   dif = difPy.build('C:/Path/to/Folder/')
   search = difPy.search(dif)

II. Multi Folder Search
^^^^^^^^^^

Search for duplicate images in multiple folders:

.. code-block:: python

   import difPy
   dif = difPy.build('C:/Path/to/Folder_A/', 'C:/Path/to/Folder_B/', 'C:/Path/to/Folder_C/', ...)
   search = difPy.search(dif)

or add a ``list`` of folders:

.. code-block:: python

   import difPy
   dif = difPy.build(['C:/Path/to/Folder_A/', 'C:/Path/to/Folder_B/', 'C:/Path/to/Folder_C/', ... ])
   search = difPy.search(dif)


Folder paths must be specified as either standalone Python strings, or in a Python list. 

difPy can search for duplicates in the union of all folders it finds, or only for duplicates within separate/isolated directories. See :ref:`in_folder`.

difPy leverages **multiprocessing** for both the build and the search process.

.. raw:: html

   <hr>

.. _cli_usage:

CLI Usage
----------------

difPy can be invoked through a CLI interface by using the following commands:

.. code-block:: python

   python dif.py #working directory

   python dif.py -D 'C:/Path/to/Folder/'

   python dif.py -D 'C:/Path/to/Folder_A/' 'C:/Path/to/Folder_B/' 'C:/Path/to/Folder_C/'

.. note::

   Windows users can add difPy to their `PATH system variables <https://www.computerhope.com/issues/ch000549.htm>`_ by pointing it to their difPy package installation folder containing the `difPy.bat <https://github.com/elisemercury/Duplicate-Image-Finder/blob/main/difPy/difPy.bat>`_ file. This adds ``difPy`` as a command in the CLI and will allow direct invocation of difPy from anywhere on the machine. The default difPy installation folder will look similar to ``C:\Users\User\AppData\Local\Programs\Python\Python311\Lib\site-packages\difPy`` (Windows 11).

difPy in the CLI supports the following arguments:

.. code-block:: python
   
   dif.py [-h] [-D DIRECTORY [DIRECTORY ...]] [-Z OUTPUT_DIRECTORY] 
          [-r {True,False}] [-i {True,False}] [-le {True,False}] 
          [-px PX_SIZE]  [-s SIMILARITY] [-ro {True,False}]
          [-la {True,False}] [-proc PROCESSES] [-ch CHUNKSIZE] 
          [-mv MOVE_TO] [-d {True,False}] [-sd {True,False}]
          [-p {True,False}]

.. csv-table::
   :header: Cmd,Parameter,Cmd,Parameter
   :widths: 5, 10, 5, 10
   :class: tight-table

   ``-D``,:ref:`directory`,``-la``,:ref:`lazy`
   ``-Z``,output_directory,``-proc``,:ref:`processes`
   ``-r``,:ref:`recursive`,``-ch``,:ref:`chunksize`
   ``-i``,:ref:`in_folder`,``-mv``,move_to (see :ref:`search.move_to`)
   ``-le``,:ref:`limit_extensions`,``-d``,delete (see :ref:`search.delete`)
   ``-px``,:ref:`px_size`,``-sd``,:ref:`silent_del`
   ``-s``,:ref:`similarity`,``-p``,:ref:`show_progress`
   ``-ro``,:ref:`rotate`,

If no directory parameter is given in the CLI, difPy will **run on the current working directory**.

The output of difPy is written to files and **saved in the working directory** by default. To change the default output directory, specify the ``-Z / -output_directory`` parameter. The "xxx" in the output filenames is the current timestamp:

.. code-block:: python

   difPy_xxx_results.json
   difPy_xxx_lower_quality.txt
   difPy_xxx_stats.json

.. raw:: html

   <hr>

.. _parameters:

Parameters
----------------

.. include:: /parameters.rst

.. raw:: html

   <hr>

.. _output:

Output
----------------

difPy returns various types of output:

.. _search.result:

I. Search Result Dictionary
^^^^^^^^^^

.. include:: /output/result.rst

.. include:: /output/result_infolder.rst

.. _search.lower_quality:

II. Lower Quality Files
^^^^^^^^^^

.. include:: /output/lower_quality.rst

.. _search.stats:

III. Process Statistics
^^^^^^^^^^

.. include:: /output/stats.rst
