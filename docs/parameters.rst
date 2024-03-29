Parameters
=====

.. _parameters:
.. _difPy.build:

difPy.build
------------

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

   If you want to reuse the image tensors generated by difPy in your own application, you can access the generated repository by calling ``difPy.build._tensor_dictionary``. To reverse the image IDs to the original filenames, use ``difPy.build._filename_dictionary``.

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
------------

After the ``dif`` object has been built using :ref:`difPy.build`, the search can be initiated with ``difPy.search``. 

When invoking ``difPy.search()``, difPy starts comparing the images to find duplicates or similarities, based on the MSE (Mean Squared Error) between both image tensors. The target similarity rate i. e. MSE value is set with the :ref:`similarity` parameter.

After the search is completed, further actions can be performed using :ref:`search.move_to` and :ref:`search.delete`.

.. code-block:: python

   difPy.search(difPy_obj, similarity='duplicates', lazy=True, rotate=True, processes=None, chunksize=None, show_progress=False, logs=True)

``difPy.search`` supports the following parameters:
 
.. csv-table::
   :header: Parameter,Input Type,Default Value,Other Values
   :widths: 10, 10, 10, 20
   :class: tight-table

   :ref:`difPy_obj`,"``difPy_obj``",,
   :ref:`similarity`,"``str``, ``int``",``'duplicates'``, "``'similar'``, any ``int`` or ``float``"
   :ref:`lazy`,``bool``,``True``,``False``
   :ref:`rotate`,``bool``,``True``,``False``
   :ref:`show_progress2`,``bool``,``True``,``False``
   :ref:`processes`,``int``,``None`` (``os.cpu_count()``), any ``int``
   :ref:`chunksize`,``int``,``None``, any ``int``

.. _difPy_obj:

difPy_obj 
^^^^^^^^^^^^

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
------------

difPy can automatically move the lower quality duplicate/similar images it found to another directory. Images can be moved by invoking ``move_to`` on the difPy search:

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
------------

difPy can automatically delete the lower quality duplicate/similar images it found. Images can be deleted by invoking ``delete`` on the difPy search:

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