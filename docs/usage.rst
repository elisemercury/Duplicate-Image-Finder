Using difPy
=====

.. _using difPy:

**difPy** is a Python package that automates the search for duplicate/similar images.

It searches for images in one (or more) different folder(s), compares the images it found and checks whether these are duplicate or similar images.

difPy compares the images based on their tensors i. e. the image content. This approach is different to classic image hash comparison and allows difPy to **not only search for duplicate images, but also for similar images**.

.. _installation:

Installation
------------

To use difPy, first install it using pip:

.. code-block:: console

   (.venv) $ pip install difPy

.. _usage:

Basic Usage
----------------

Single Folder Search
^^^^^^^^^^

Search for duplicate images in a single folder:

.. code-block:: python

   from difPy import dif
   search = dif("C:/Path/to/Folder/")

Multi-Folder Search
^^^^^^^^^^

Search for duplicate images in multiple folders:

.. code-block:: python

   from difPy import dif
   search = dif("C:/Path/to/Folder_A/", "C:/Path/to/Folder_B/", "C:/Path/to/Folder_C/", ...)

or add a ``list`` of folders:

.. code-block:: python

   from difPy import dif
   search = dif(["C:/Path/to/Folder_A/", "C:/Path/to/Folder_B/", "C:/Path/to/Folder_C/", ... ])


Folder paths must be specified as either standalone Python strings, or within a Python `list`. difPy will compare the **union** of all files within the specified folders.

By default, difPy leverages its :ref:`Fast Search Algorithm (FSA)`.

.. _cli_usage:

CLI Usage
----------------

difPy can be invoked through a CLI interface by using the following commands:

.. code-block:: python

   python dif.py -D "C:/Path/to/Folder/"

   python dif.py -D "C:/Path/to/Folder_A/" "C:/Path/to/Folder_B/" "C:/Path/to/Folder_C/"   

It supports the following arguments:

.. code-block:: python
   
   dif.py [-h] -D DIRECTORY [-Z OUTPUT_DIRECTORY] [-f {True,False}]
          [-r {True,False}] [-s SIMILARITY] [-px PX_SIZE] [-mv MOVE_TO]
          [-le {True,False}] [-p {True,False}] [-o {True,False}]
          [-d {True,False}] [-sd {True,False}] [-l {True,False}]

.. csv-table::
   :header: Cmd,Parameter,Cmd,Parameter
   :widths: 5, 10, 5, 10
   :class: tight-table

   ``-D``,directory,``-p``,show_progress
   ``-Z``,output_directory,``-o``,show_output
   ``-f``,fast_search,``-mv``,move_to
   ``-r``,recursive,``-d``,delete
   ``-s``,similarity,``-sd``,silent_del
   ``-px``,px_size,``-l``,logs
   ``-le``,limit_extensions,,

When running from the CLI, the output of difPy is written to files and saved in the working directory by default. To change the default output directory, specify the ``-Z / -output_directory`` parameter. The "xxx" in the output filenames is a unique timestamp:

.. code-block:: python

   difPy_results_xxx.json
   difPy_lower_quality_xxx.csv
   difPy_stats_xxx.json

.. _output:

Output
----------------

difPy returns various types of output that you may use depending on your use case:

Matched Images
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

Lower Quality Images
^^^^^^^^^^

A **list** of duplicates/similar images that have the **lowest quality** among match groups:

.. code-block:: python

   search.lower_quality

   > Output:
   ["C:/Path/to/Image/duplicate_image1.jpg", 
    "C:/Path/to/Image/duplicate_image2.jpg", ...]

To find the lower quality images, difPy compares all image file sizes within a match group and selects all images that have lowest image file size among the group.

Process Statistics
^^^^^^^^^^

A **JSON formatted collection** with statistics on the completed difPy process:

.. code-block:: python

   search.stats

   > Output:
   {"directory" : ("C:/Path/to/Folder_A/", "C:/Path/to/Folder_B/", ... ),
    "duration" : {"start_date" : "2023-02-15",
                  "start_time" : "18:44:19",
                  "end_date" : "2023-02-15",
                  "end_time" : "18:44:38",
                  "seconds_elapsed" : 18.6113},
    "fast_search" : True,
    "recursive" : True,
    "match_mse" : 200,
    "px_size" : 50,
    "files_searched" : 1032,
    "matches_found" : {"duplicates" : 52,
                       "similar" : 0},
    "invalid_files" : {"count" : 4,
                       "logs" : {}},
    "deleted_files" : {"count" : 4,
                       "logs" : []},
    "skipped_files" : {"count" : 0,
                       "logs" : []} }

The ``invalid_files`` logs are only outputted if the ``logs`` parameter is set to ``True``. See the :ref:`logs` section for more details.

.. _Supported File Types:

Supported File Types
----------------

difPy supports most popular image formats. Nevertheless, since it relies on the Pillow library for image decoding, the supported formats are restricted to the ones listed in the* `Pillow Documentation`_. Unsupported file types will by marked as invalid and included in the :ref:`invalid_files` output.

.. _Pillow Documentation: https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html

.. _Fast Search Algorithm (FSA):

Fast Search Algorithm (FSA)
--------

.. note::

   🆕 difPy >= v3.x supports Fast Search Algorithm (FSA).

difPy's Fast Search Algorithm (FSA) can provide significant performance increases and time complexity reduction when searching for duplicates.

FSA can be enabled/disabled with the :ref:`fast_search` parameter.

About FSA
^^^^^^^^^^

With the classic difPy algorithm, each image would be compared to every other successive image (by order of images found in the directories). Comparing every image is a very precise option, but leads to high time complexity. When searching for duplicates, this time complexity can be reduced by applying FSA. With FSA, difPy compares an image until it finds a duplicate. This duplicate is classified as duplicate and then excluded from the succeeding search, leading to a lower average number of comparisons.

   *Example: in the first round, difPy searches for duplicates to imageA and finds imageB and imageC. In the next rounds, the search for duplicates of imageB and imageC will be skipped, since they are all duplicates and no further comparison is required.*

Due to its nature, FSA is very efficient when run on duplicate searches, but it is **not advised to be used when searching for similar images**, as the result might be inaccurate. **When searching for similar images, difPy's classic algorithm should be used by setting** :ref:`fast_search` **to** ``False``.

   *Example: imageA might be similar to imageB and imageC, but this does not imply that imageB is similar to imageC. Nevertheless, FSA would assume imageB and imageC to be equally similar and would therefore potentially return wrong results.*

**When searching for similar images, difPy automatically disables FSA** to ensure accurate search results. This applies when :ref:`similarity` is set to ``'similar'`` **or** if :ref:`similarity` is manually set to a value ``> 0``.

How to Speed Up difPy?
^^^^^^^^^^

difPy's processing speed can increase or decrease, depending on which parameter configurations are used. Speeding up the comparison process can be especially useful, when using difPy to compare a large number of images (>1'000 images). Below you will find some tips on which configurations can make difPy's processing faster:

* Enable :ref:`fast_search` when searching for duplicates
* Enable :ref:`limit_extensions`
* Set :ref:`px_size` <= 50. Note: the lower the ``px_size``, the less precise the comparison will be. It is not recommended to go below a ``px_size`` of 20.