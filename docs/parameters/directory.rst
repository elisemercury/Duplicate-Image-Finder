directory (str, list)
^^^^^^^^^^^^

difPy supports single and multi-folder search.

**Single Folder Search**:

.. code-block:: python

   import difPy
   dif = difPy.build("C:/Path/to/Folder/")
   search = difPy.search(dif)

**Multi Folder Search**:

.. code-block:: python

   import difPy
   dif = difPy.build(["C:/Path/to/Folder_A/", "C:/Path/to/Folder_B/", "C:/Path/to/Folder_C/", ... ])
   search = difPy.search(dif)

Folder paths can be specified as standalone Python strings, or within a list.