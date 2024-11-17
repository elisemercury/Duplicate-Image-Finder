.. _search.lower_quality:

Lower Quality Files
^^^^^^^^^^

A **list** of duplicates/similar images that have the **lowest resolution** among match groups: 

.. code-block:: python

   search.lower_quality

   > Output:
   ['C:/Path/duplicate_image1.jpg', 
    'C:/Path/duplicate_image2.jpg', ...]

To find the lower quality images, difPy compares the **image resolutions** (pixel width x pixel height) within a match group and selects all images that have lowest image file resolutions among the group.

Lower quality images then can be **moved** to a different location (see :ref:`search.move_to`):

.. code-block:: python
   
   search.move_to(destination_path='C:/Path/to/Destination/')

Or **deleted** (see :ref:`search.delete`):

.. code-block:: python

   search.delete(silent_del=False)