.. _difPy.search:

difPy.search
^^^^^^^^^^

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
++++++++++++

The required ``difPy_obj`` parameter should be pointing to the ``dif`` object that was built during the invocation of :ref:`difPy.build`. 

.. _similarity: 

similarity (str, int)
++++++++++++

difPy compares the images to find duplicates or similarities, based on the MSE (Mean Squared Error) between both image tensors. The target similarity rate i. e. MSE value is set with the ``similarity`` parameter. 

``"duplicates"`` = (default) searches for duplicates. MSE threshold is set to ``0``.

``"similar"`` = searches for similar images. MSE threshold is set to ``5``.

The search for similar images can be useful when searching for duplicate files that might have different file **types** (i. e. imageA.png has a duplicate imageA.jpg) and/or different file **sizes** (f. e. imageA.png (100MB) has a duplicate imageA.png (50MB)). In these cases, the MSE between the two image tensors might not be exactly == 0, hence they would not be classified as being duplicates even though in reality they are. Setting ``similarity`` to ``"similar"`` searches for duplicates with a certain tolerance, increasing the likelihood of finding duplicate images of different file types and sizes. Depending on which ``similarity`` level is chosen, the ``lazy`` parameter should be adjusted accordingly (see :ref:`lazy`).

.. figure:: docs/static/assets/choosing_similarity.png
   :width: 540
   :height: 390
   :alt: Setting the "similarity" & "lazy" Parameter
   :align: center

   Setting the "similarity" and "lazy" parameter

**Manual setting**: the match MSE threshold can be adjusted manually by setting the ``similarity`` parameter to any ``int`` or ``float``. difPy will then search for images that match an MSE threshold **equal to or lower than** the one specified.
   
.. _lazy:

lazy (bool)
++++++++++++

By default, difPy searches using a Lazy algorithm. This algorithm assumes that the image matches we are looking for have **the same dimensions**, i. e.duplicate images have the same width and height. If two images do not have the same dimensions, they are automatically assumed to not be duplicates. Therefore, because these images are skipped, this algorithm can provide a significant **improvement in performance**.

``True`` = (default) applies the Lazy algorithm

``False`` = regular algorithm is used

**When should the Lazy algorithm not be used?**
The Lazy algorithm can speed up the comparison process significantly. Nonetheless, the algorithm might not be suited for your use case and might result in missing some matches. Depending on which ``similarity`` level is chosen, the ``lazy`` parameter should be adjusted accordingly (see :ref:`similarity`). Set ``lazy = False`` if you are searching for duplicate images with:

*  different **file types** (i. e. imageA.png is a duplicate of imageA.jpg)
*  and/or different **file sizes** (i. e. imageA.png (100MB) is a duplicate of imageA_compressed.png (50MB))

.. _rotate:

rotate (bool)
++++++++++++

By default, difPy will rotate the images on comparison. In total, 3 rotations are performed: 90°, 180° and 270° degree rotations.  

``True`` = (default) rotates images on comparison

``False`` = images are not rotated before comparison

show_progress (bool)
++++++++++++

See :ref:`show_progress`.

processes (int)
++++++++++++

See :ref:`processes`.

.. _chunksize:

chunksize (int)
++++++++++++

.. warning::
   Recommended not to change default value. Only adjust this value if you know what you are doing.

``chunksize`` is only used when dealing with image datasets of **more than 5k images**. See the ":ref:`Using difPy with Large Datasets`" section for further details.

difPy leverages a different comparison algorithm depending on the size of the input dataset. If the dataset contains more than 5k images, then the Chunking algorithm is used, which leverages generators and vectorization for more efficient computation with large datasets. The ``chunksize`` parameter defines how many chunks of image sets should be compared at once. Therefore, the higher the ``chunksize`` value, the faster the computation but the higher the memory consumption. 

The ``chunksize`` parameter is already **automatically set to an optimal value** relative to the size of the dataset. Nonetheless, it can also be adjusted manually, in order to provide more control over Multiprocessing strategies and memory consumption. 

By default, ``chunksize`` is set to ``None`` which implies: ``1'000'000 / number of images in dataset``. Parameter can only be >= 1.

**Manual setting**: ``chunksize`` can be manually adjusted by setting it to any ``int`` >= 1.