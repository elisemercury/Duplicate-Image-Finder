lazy (bool)
++++++++++++

By default, difPy searches using a Lazy algorithm. This algorithm assumes that the image matches we are looking for have the same dimensions, i. e. same width and height of the duplicate images. If two images do not have the same dimensions, they are automatically assumed to not be duplicates. Therefore, because these images are skipped, this algorithm can provide a significant improvement in performance.

``True`` = (default) applies the Lazy algorithm

``False`` = regular algorithm is used

**When should the "lazy" algorithm not be used?**
The "lazy" algorithm can speed up the comparison process significantly. Nonetheless, the algorithm might not be suited for your use case and might result in missing some matches. Depending on which ``similarity`` level is chosen, the ``lazy`` parameter should be adjusted accordingly (see :ref:`lazy`). You should set ``lazy = False`` if you are searching for duplicate images with:

*  different **file types** (i. e. imageA.png is a duplicate of imageA.jpg)
*  and/or different **file sizes** (i. e. imageA.png (100MB) is a duplicate of imageA_compressed.png (50MB))