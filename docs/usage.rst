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

Parameters
----------------

.. _parameters:
.. _difPy.build:

difPy.build
^^^^^^^^^^

Before difPy can perform any search, it needs to build its image repository and transform the images in the provided directory into tensors. This is what is done when ``difPy.build()`` is invoked.

Upon completion, ``difPy.build()`` returns a ``dif`` object that can be used in :ref:`difPy.search` to start the search process.

``difPy.build`` supports the following parameters:

.. code-block:: python

   difPy.build(*directory, recursive=True, in_folder=False, limit_extensions=True, px_size=50, show_progress=True, processes=None)

.. csv-table::
   :header: Parameter,Input Type,Default Value,Other Values
   :widths: 10, 10, 10, 20
   :class: tight-table

   :ref:`directory`,"``str``, ``list``",,
   :ref:`recursive`,``bool``,``True``,``False``
   :ref:`in_folder`,"``bool``, ``False``",``True``
   :ref:`limit_extensions`,``bool``,``True``,``False``
   :ref:`px_size`,"``int``, ``float``",50, ``int``
   :ref:`show_progress`,``bool``,``True``,``False``
   :ref:`processes`,``int``,``None`` (``os.cpu_count()``), ``int``

.. note::

   If you want to reuse the image tensors generated by difPy, you can access the generated repository by calling ``difPy.build._tensor_dictionary``. To reverse the image IDs to the original filenames, use ``difPy.build._filename_dictionary``.

.. _directory:

.. include:: /parameters/directory.rst

.. _recursive:

.. include:: /parameters/recursive.rst

.. _in_folder:

.. include:: /parameters/in_folder.rst

.. _limit_extensions:

.. include:: /parameters/limit_extensions.rst

.. _px_size:

.. include:: /parameters/px_size.rst

.. _show_progress:

.. include:: /parameters/show_progress.rst

.. _processes:
 
.. include:: /parameters/processes.rst

.. _logs:

.. include:: /parameters/deprecated/logs.rst

.. raw:: html

   <hr>

.. _difPy.search:

difPy.search
^^^^^^^^^^

After the ``dif`` object has been built using :ref:`difPy.build`, the search can be initiated with ``difPy.search``. 

When invoking ``difPy.search()``, difPy starts comparing the images to find duplicates or similarities, based on the MSE (Mean Squared Error) between both image tensors. The target similarity rate i. e. MSE value is set with the :ref:`similarity` parameter.

After the search is completed, further actions can be performed using :ref:`search.move_to` and :ref:`search.delete`.

.. code-block:: python

   difPy.search(difPy_obj, similarity='duplicates', rotate=True, lazy=True, processes=None, chunksize=None, show_progress=False)

``difPy.search`` supports the following parameters:
 
.. csv-table::
   :header: Parameter,Input Type,Default Value,Other Values
   :widths: 10, 10, 10, 20
   :class: tight-table

   :ref:`difPy_obj`,"``difPy_obj``",,
   :ref:`similarity`,"``str``, ``int``",``'duplicates'``, "``'similar'``,  ``int``, ``float``"
   :ref:`lazy`,``bool``,``True``,``False``
   :ref:`rotate`,``bool``,``True``,``False``
   :ref:`show_progress2`,``bool``,``True``,``False``
   :ref:`processes`,``int``,``None`` (``os.cpu_count()``), ``int``
   :ref:`chunksize`,``int``,``None``, ``int``

.. _difPy_obj:

difPy_obj
++++++++++++

The required ``difPy_obj`` parameter should be pointing to the ``dif`` object that was built during the invocation of :ref:`difPy.build`. 

.. _similarity:

.. include:: /parameters/similarity.rst

.. _lazy:

.. include:: /parameters/lazy.rst

.. _rotate:

.. include:: /parameters/rotate.rst

.. _show_progress2:

.. include:: /parameters/show_progress.rst

.. _processes2:

.. include:: /parameters/processes.rst

.. _chunksize:

.. include:: /parameters/chunksize.rst

.. _logs2:

.. include:: /parameters/deprecated/logs.rst

.. raw:: html

   <hr>

.. _search.move_to:

search.move_to
^^^^^^^^^^

difPy can automatically move the lower quality duplicate/similar images it found to another directory. Images can be moved by invoking ``search.move_to``:

.. code-block:: python

   import difPy
   dif = difPy.build("C:/Path/to/Folder_A/")
   search = difPy.search(dif)
   search.move_to(destination_path="C:/Path/to/Destination/")

.. code-block:: console

   > Output
   Moved 756 files(s) to "C:/Path/to/Destination"

.. _destination_path:

.. include:: /parameters/destination_path.rst

.. raw:: html

   <hr>

.. _search.delete:

search.delete
^^^^^^^^^^

difPy can automatically delete the lower quality duplicate/similar images it found. Images can be deleted by invoking ``search.delete``:

.. note::

   Please use with care, as this cannot be undone.

.. code-block:: python

   import difPy
   dif = difPy.build("C:/Path/to/Folder_A/")
   search = difPy.search(dif)
   search.delete(silent_del=False)

.. code-block:: console

   > Output
   Deleted 756 files(s)

The images are deleted based on the ``lower_quality`` output as described under section :ref:`output`. After auto-deleting the images, every match group will be left with one single image: the image with the highest quality among its match group.

``delete`` asks for user confirmation before deleting the images. The user confirmation can be skipped by setting :ref:`silent_del` to ``True``.

.. _silent_del:

.. include:: /parameters/silent_del.rst

.. _output:

.. raw:: html

   <hr>

Output
----------------

difPy returns various types of output:

I. Search Result Dictionary
^^^^^^^^^^
A **dictionary** of duplicates/similar images (i. e. **match groups**) that were found. Each match group has a primary image (the key of the dictionary) which holds the list of its duplicates including their filename and MSE (Mean Squared Error). The lower the MSE, the more similar the primary image and the matched images are. Therefore, an MSE of 0 indicates that two images are exact duplicates.

.. include:: /output/result.rst


When :ref:`in_folder` is set to ``True``, the result output is slightly modified and matches are grouped in their separate folders, with the key of the dictionary being the folder path.

.. include:: /output/result_infolder.rst

II. Lower Quality Files
^^^^^^^^^^

A **list** of duplicates/similar images that have the **lowest quality** among match groups: 

.. include:: /output/lower_quality.rst

To find the lower quality images, difPy compares all image file sizes within a match group and selects all images that have lowest image file size among the group.

Lower quality images then can be **moved** to a different location (see :ref:`search.move_to`):

.. code-block:: python
   
   search.move_to(destination_path='C:/Path/to/Destination/')

Or **deleted** (see :ref:`search.delete`):

.. code-block:: python

   search.delete(silent_del=False)

.. _Process Statistics:

III. Process Statistics
^^^^^^^^^^

A **JSON formatted collection** with statistics on the completed difPy process:

.. include:: /output/stats.rst
