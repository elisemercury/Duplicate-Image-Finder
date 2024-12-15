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