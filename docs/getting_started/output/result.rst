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