similarity (str, int)
++++++++++++

difPy compares the images to find duplicates or similarities, based on the MSE (Mean Squared Error) between both image tensors. The target similarity rate i. e. MSE value is set with the ``similarity`` parameter. 

``"duplicates"`` = (default) searches for duplicates. MSE threshold is set to ``0``.

``"similar"`` = searches for similar images. MSE threshold is set to ``5``.

The search for similar images can be useful when searching for duplicate files that might have different file **types** (i. e. imageA.png has a duplicate imageA.jpg) and/or different file **sizes** (f. e. imageA.png (100MB) has a duplicate imageA.png (50MB)). In these cases, the MSE between the two image tensors might not be exactly == 0, hence they would not be classified as being duplicates even though in reality they are. Setting ``similarity`` to ``"similar"`` searches for duplicates with a certain tolerance, increasing the likelihood of finding duplicate images of different file types and sizes. Depending on which ``similarity`` level is chosen, the ``lazy`` parameter should be adjusted accordingly (see :ref:`lazy`).

.. figure:: static/assets/choosing_similarity.png 
   :width: 520
   :height: 390
   :alt: Setting the "similarity" & "lazy" Parameter
   :align: center

   Setting the "similarity" and "lazy" parameter

**Manual setting**: the match MSE threshold can be adjusted manually by setting the ``similarity`` parameter to any ``int`` or ``float``. difPy will then search for images that match an MSE threshold **equal to or lower than** the one specified.