.. _search.delete:

search.delete
^^^^^^^^^^

difPy can automatically delete the lower quality duplicate/similar images it found. Images can be deleted by invoking ``delete`` on the difPy search:

.. warning::

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

silent_del (bool)
++++++++++++

.. note::

   Please use with care, as this cannot be undone.

When set to ``True``, the user confirmation for :ref:`search.delete` is skipped and the lower resolution matched images that were found by difPy are automatically deleted from their folder(s).