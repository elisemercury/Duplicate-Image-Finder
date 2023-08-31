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

difPy supports searching for duplicate and similar images within a single or multiple directories. difPy first needs to be initialized and build its image repository with :ref:`difPy.build`. After the ``dif`` object had been created, by invoking :ref:`difPy.search`, difPy starts the search for matching images. 

Single Folder Search
^^^^^^^^^^

Search for duplicate images in a single folder:

.. code-block:: python

   import difPy
   dif = difPy.build("C:/Path/to/Folder/")
   search = difPy.search(dif)

Multi Folder Search
^^^^^^^^^^

Search for duplicate images in multiple folders:

.. code-block:: python

   import difPy
   dif = difPy.build("C:/Path/to/Folder_A/", "C:/Path/to/Folder_B/", "C:/Path/to/Folder_C/", ...)
   search = difPy.search(dif)

or add a ``list`` of folders:

.. code-block:: python

   import difPy
   dif = difPy.build(["C:/Path/to/Folder_A/", "C:/Path/to/Folder_B/", "C:/Path/to/Folder_C/", ... ])
   search = difPy.search(dif)


Folder paths must be specified as either standalone Python strings, or in a Python list. 

difPy can search for duplicates in the union of all folders, or only among the folders and subdirectories itself. See :ref:`in_folder`.

difPy leverages **multiprocessing** for both the build and the search process.

.. _cli_usage:

CLI Usage
----------------

difPy can be invoked through a CLI interface by using the following commands:

.. code-block:: python

   python dif.py #working directory

   python dif.py -D "C:/Path/to/Folder/"

   python dif.py -D "C:/Path/to/Folder_A/" "C:/Path/to/Folder_B/" "C:/Path/to/Folder_C/"

.. note::

   Windows users can add difPy to their `PATH system variables <https://www.computerhope.com/issues/ch000549.htm>`_ by pointing it to their difPy package installation folder containing the `difPy.bat <https://github.com/elisemercury/Duplicate-Image-Finder/difPy/difPy.bat>`_ file. This adds ``difPy`` as a command in the CLI and will allow direct invocation of difPy from anywhere on the machine. The default difPy installation folder will look similar to ``C:\Users\User\AppData\Local\Programs\Python\Python311\Lib\site-packages\difPy`` (Windows 11).

difPy in the CLI supports the following arguments:

.. code-block:: python
   
   dif.py [-h] [-D DIRECTORY [DIRECTORY ...]] [-Z OUTPUT_DIRECTORY] 
          [-r {True,False}] [-i {True,False}] [-le {True,False}] 
          [-px PX_SIZE] [-p {True,False}] [-s SIMILARITY] 
          [-mv MOVE_TO] [-d {True,False}] [-sd {True,False}] 
          [-l {True,False}]

.. csv-table::
   :header: Cmd,Parameter,Cmd,Parameter
   :widths: 5, 10, 5, 10
   :class: tight-table

   ``-D``,directory,``-le``,limit_extensions
   ``-Z``,output_directory,``-p``,show_progress
   ``-r``,recursive,``-mv``,move_to
   ``-i``,in_folder,``-d``,delete
   ``-s``,similarity,``-sd``,silent_del
   ``-px``,px_size,``-l``,logs

If no directory parameter is given in the CLI, difPy will **run on the current working directory**.

The output of difPy is written to files and **saved in the working directory** by default. To change the default output directory, specify the ``-Z / -output_directory`` parameter. The "xxx" in the output filenames is the current timestamp:

.. code-block:: python

   difPy_xxx_results.json
   difPy_xxx_lower_quality.json
   difPy_xxx_stats.json

.. _output:

Output
----------------

difPy returns various types of output:

I. Search Result Dictionary
^^^^^^^^^^
A **JSON formatted collection** of duplicates/similar images (i. e. **match groups**) that were found, where the keys are a **randomly generated unique id** for each image file:

.. code-block:: python

   search.result

   > Output:
   {20220819171549 : {"location" : "C:/Path/to/Image/image1.jpg",
                      "matches" : {30270813251529 : "location": "C:/Path/to/Image/matched_image1.jpg",
                                                    "mse": 0.0},
                                  {72214282557852 : "location": "C:/Path/to/Image/matched_image2.jpg",
                                                    "mse": 0.0},
                      ... }
    ...
   }

II. Lower Quality Files
^^^^^^^^^^

A **JSON formatted collection** of duplicates/similar images that have the **lowest quality** among match groups: 

.. code-block:: python

   search.lower_quality

   > Output:
   {"lower_quality" : ["C:/Path/to/Image/duplicate_image1.jpg", 
                     "C:/Path/to/Image/duplicate_image2.jpg", ...]}

To find the lower quality images, difPy compares all image file sizes within a match group and selects all images that have lowest image file size among the group.

Lower quality images then can be **moved** to a different location (see :ref:`search.ove_to`):

.. code-block:: python
   
   search.move_to(search, destination_path="C:/Path/to/Destination/")

Or **deleted** (see :ref:`search.delete`):

.. code-block:: python

   search.delete(search, silent_del=False)


.. _Process Statistics:

III. Process Statistics
^^^^^^^^^^

A **JSON formatted collection** with statistics on the completed difPy process:

.. code-block:: python

   search.stats

   > Output:
   {"directory" : ("C:/Path/to/Folder_A/", "C:/Path/to/Folder_B/", ... ),
    "process" : {"build" : {"duration" : {"start" : "2023-08-28T21:22:48.691008",
                                          "end" : "2023-08-28T21:23:59.104351",
                                          "seconds_elapsed" : "70.4133"},
                            "parameters" : {"recursive" : True,
                                            "in_folder" : False,
                                            "limit_extensions" : True,
                                            "px_size" : 50}},
                 "search" : {"duration" : {"start" : "2023-08-28T21:23:59.106351",
                                           "end" : "2023-08-28T21:25:17.538015",
                                           "seconds_elapsed" : "78.4317"},
                           "parameters" : {"similarity_mse" : 0}
                           "files_searched" : 5225,
                           "matches_found" : {"duplicates" : 5,
                                              "similar" : 0}}}
    "invalid_files" : {"count" : 230,
                       "logs" : {...}}}