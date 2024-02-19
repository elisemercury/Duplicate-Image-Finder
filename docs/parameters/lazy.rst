lazy (bool)
^^^^^^^^^^^^

By default, difPy searches using a "lazy" algorithm. This algorithm assumes that the matches we are looking for have the same dimensions, i. e. width and height lengths. If two images do not have the same dimensions, they are automatically assumed to not be duplicates/similar. Therefore, because these images are skipped, this algorithm can provide a significant improvement in performance.

**When should the "lazy" algorithm not be used?**
The "lazy" algorithm can speed up the comparison process significantly. Nonetheless, the algorithm might not be suited for your use case and might result in missing some matches. You should disable "lazy" if you are searching for:
* duplicates/similar images with different **file types** (i. e. imageA.png is a duplicate of imageA.jpg)
* duplicates/similar images with different **file sizes** (i. e. imageA.png (100MB) is a duplicate of imageA_compressed.png (50MB))

``True`` = (default) applies the "lazy" algorithm

``False`` = regular algorithm is used