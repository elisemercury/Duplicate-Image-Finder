Parameters
=====

.. _parameters:

difPy supports the following parameters:

.. code-block:: python

   dif(directory*, fast_search=True, recursive=True, similarity='duplicates', px_size=50, move_to=None
       show_progress=True, show_output=False, delete=False, silent_del=False, logs=False)

.. csv-table::
   :header: Parameter,Input Type,Default Value,Other Values
   :widths: 20, 10, 10, 10
   :class: tight-table

   :ref:`directory`,"``str``, ``list``",,
   :ref:`fast_search`,``bool``,``True``,``False``
   :ref:`recursive`,``bool``,``True``,``False``
   :ref:`similarity`,"``str``, ``int``",``'duplicates'``, "``'similar'``, any ``int`` or ``float``"
   :ref:`px_size`,"``int``, ``float``",50,any ``int`` (not recommended to change default value)
   :ref:`show_progress`,``bool``,``True``,``False``
   :ref:`show_output`,``bool``,``False``,``True``
   :ref:`move_to`,``str``,``None``,folder path as ``str``
   :ref:`delete`,``bool``,``False``,"``True`` (use with care, cannot be undone)"
   :ref:`silent_del`,``bool``,``False``,"``True`` (use with care, cannot be undone)"
   :ref:`logs`,``bool``,``False``,``True``

.. _directory:

directory
------------

difPy supports single and multi-folder search.

For a detailed guide on how set the directory parameter for each use case, please refer to the :ref:`usage` section.

.. _fast_search:

fast_search
------------

.. note::

   🆕 difPy >= v3.x supports Fast Search Algorithm (FSA).

By default, when searching for duplicates, difPy will run the comparison process by using its :ref:`Fast Search Algorithm (FSA)`. This algorithm can provide significant performance increases and time complexity reduction. 

FSA can only be leveraged when searching for duplicates, not for similar images. Therefore, it will only be enabled if the :ref:`similarity` parameter is set to ``"duplicates"`` or if it is manually set to ``0``. Even if ``fast_search`` is set to ``True``, as long as the :ref:`similarity` parameter does not comply with the above requirements, FSA will be disabled by difPy, as it might otherwise lead to inaccurate results.

``True`` = (default) uses difPy's Fast Search Algorithm (FSA)

``False`` = uses difPy's regular search algorithm

.. _recursive:

recursive
------------

By default, difPy will search for duplicate images  recursively within the subfolders of the directory specified in the :ref:`directory` parameter. If set to ``False``, subfolders will not be scanned.

``True`` = (default) searches recursively through all subfolders in the directory paths

``False`` = disables recursive search through subfolders in the directory paths

.. _similarity:

similarity
------------

Depending on which use case you want to apply difPy for, the granularity for the classification of images can be adjusted.

difPy can f. e. search for exact matching duplicate images or search for images that are similar.

``"duplicates"`` = (default) searches for duplicates. MSE threshold is set to ``0``.

``"similar"`` = searches for similar images. MSE threshold is set to ``1000``.

**Manual setting**: the match MSE threshold can be adjusted manually by setting ``similarity`` parmeter to any ``int`` or ``float``. difPy will then search for images that match an MSE threshold **equal to or lower than** the one specified.

.. _px_size:

px_size
------------

.. note::

   Recommended not to change default value.

Absolute size in pixels (width x height) of the images before being compared. The higher the ``px_size``, the more computational resources and time required for difPy to compare the images. The lower the ``px_size``, the faster, but the more imprecise the comparison process gets.

By default, ``px_size`` is set to ``50``.

**Manual setting**: ``px_size`` can be manually adjusted by setting it to any ``int``.

.. _show_progress:

show_progress
------------

By default, difPy will show a progress bar of the running process.

``True`` = (default) displays the progress bar

``False`` = disables the progress bar

.. _show_output:

show_output
------------

By default, difPy will output its search result data as described under section :ref:`output`. Matched images can also be display in the console output by setting ``show_output`` to ``True``.

``False`` = (default) output as in section :ref:`output`

``True`` = displays the matched images and their filename in the console output

.. _move_to:

move_to
------------

difPy can automatically move the lower quality duplicate/similar images it found to another directory. Images can be moved by setting ``move_to`` to a desired destination folder.

The images are moved based on the ``lower_quality`` output as described under section :ref:`output`.

``None`` = (default) images are not moved

``"C:/Path/to/Destination/"`` = moves the lower quality image files to the destination folder

.. _delete:

delete
------------

.. note::

   Please use with care, as this cannot be undone.

When set to ``True``, the lower quality duplicate/similar image(s) that were found by difPy are deleted from the folder(s).

The images are deleted based on the ``lower_quality`` output as described under section :ref:`output`. After auto-deleting the images, every match group will be left with one single image: the image with the highest quality among its match group.

``delete`` asks for user confirmation before deleting the images. The user confirmation can be skipped by setting :ref:`silent_del` to ``True``.

.. _silent_del:

silent_del
------------

.. note::

   Please use with care, as this cannot be undone.

When set to ``True``, the user confirmation for :ref:`delete` is skipped and the lower resolution matched images that were found by difPy are automatically deleted from their folder(s).

.. _logs:

logs
------------

difPy outputs ``search.stats`` statistics after each process, as described in :ref:`output`. 

For informative of troubleshooting purposes, the ``logs`` parameter can be set to ``True`` so that the ``.stats`` output contains more details around the ``invalid_files`` and the ``deleted_files`` during the process:

.. code-block:: python

   search.stats

   > Output:
   {...,
   "invalid_files" : {"count" : 4,
                      "logs" : {"C:/Path/to/Images/inv_file.pdf" : "UnidentifiedImageError: file could not be identified as image.",
                                ... },
   "deleted_files" : {"count" : 25,
                      "logs" : ["C:/Path/to/Images/duplicate_image1.jpg", 
                                "C:/Path/to/Images/duplicate_image2.jpg", 
                                ... ]}}


``False`` = (default) logs output are disabled

``True`` = logs are enabled