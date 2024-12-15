.. _search.move_to:

search.move_to
^^^^^^^^^^

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

destination_path (str)
++++++++++++

Directory of where the lower quality files should me moved. Should be given as Python ``string``.