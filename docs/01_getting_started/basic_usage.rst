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

Single Folder Search
^^^^^^^^^^

Search for duplicate images in a single folder:

.. code-block:: python

   import difPy
   dif = difPy.build('C:/Path/to/Folder/')
   search = difPy.search(dif)

Multi Folder Search
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