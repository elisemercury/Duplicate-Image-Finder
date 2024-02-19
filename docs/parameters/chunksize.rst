chunksize (int)
++++++++++++

.. warning::
   Recommended not to change default value. Only adjust this value if you know what you are doing.

``chunksize`` is only used when dealing with image datasets of **more than 5k images**. See the :ref:`_Concepts` section for further details.

difPy leverages a different comparison algorithm depending on the size of the input dataset. If the dataset contains more than 5k images, then the "batch algorithm" is used, which leverages generators and vectorization for more efficient computation with large datasets. It sets how many chunks of image sets should be compared at once. Therefore, the higher the chunksize value, the faster the computation but the higher the memory consumption. The ``chunksize`` parameter is already **automatically set to an optimal value** relative to the size of your dataset. Nonetheless, it can also be adjusted manually, in order to provide more control over Multiprocessing strategies and memory consumption. 

By default, ``chunksize`` is set to ``None`` which implies: ``1'000'000 / number of images in dataset``. Minimum value is 1.

**Manual setting**: ``chunksize`` can be manually adjusted by setting it to any ``int`` >= 1.