.. _output:

Output
----------------

difPy returns various types of output:

.. _search.result:

Search Result
^^^^^^^^^^

A **dictionary** of duplicates/similar images (i. e. **match groups**) that were found. Each match group has a primary image (the key of the dictionary) which holds the list of its duplicates including their filename and MSE (Mean Squared Error). The lower the MSE, the more similar the primary image and the matched images are. Therefore, an MSE of 0 indicates that two images are exact duplicates.

.. code-block:: python

   search.result

   > Output:
   {'C:/Path/image1.jpg' : [['C:/Path/duplicate_image1a.jpg', 0.0], 
                            ['C:/Path/duplicate_image1b.jpg', 0.0]],
    'C:/Path/image2.jpg' : [['C:/Path/duplicate_image2a.jpg', 0.0]],
   ...
   }

When :ref:`in_folder` is set to ``True``, the result output is slightly modified and matches are grouped in their separate folders, with the key of the dictionary being the folder path.

.. code-block:: python

   search.result

   > Output:
   {'C:/Path1/' : {'C:/Path1/image1.jpg' : [['C:/Path1/duplicate_image1a.jpg', 0.0], 
                                            ['C:/Path1/duplicate_image1b.jpg', 0.0]],
                   'C:/Path1/image2.jpg' : [['C:/Path1/duplicate_image2a.jpg', 0.0]],
    'C:/Path2/' : {'C:/Path2/image1.jpg' : [['C:/Path2/duplicate_image1a.jpg', 0.0]],
   ...
   }

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

.. _search.stats:

Search Statistics
^^^^^^^^^^

A **JSON formatted collection** with statistics on the completed difPy process:

.. code-block:: python

   search.stats

   > Output:
   {'directory': ['C:/Path1/', 'C:/Path2/', ... ],
    'process': {'build': {'duration': {'start': '2024-02-18T19:52:39.479548',
                                       'end': '2024-02-18T19:52:41.630027',
                                       'seconds_elapsed': 2.1505},
                          'parameters': {'recursive': True,
                                         'in_folder': False,
                                         'limit_extensions': True,
                                         'px_size': 50,
                                         'processes': 5}},
                'search': {'duration': {'start': '2024-02-18T19:52:41.630027',
                                        'end': '2024-02-18T19:52:46.770077',
                                        'seconds_elapsed': 5.14},
                           'parameters': {'similarity_mse': 0,
                                          'rotate': True,
                                          'same_dim': True,
                                          'processes': 5,
                                          'chunksize': None},
                           'files_searched': 3228,
                           'matches_found': {'duplicates': 3030, 
                                             'similar': 0}}},
    'total_files': 3232,
    'invalid_files': {'count': 4, 
                      'logs': {'C:/Path/invalid_File.pdf': 'Unsupported file type', 
                               ... }}}}
