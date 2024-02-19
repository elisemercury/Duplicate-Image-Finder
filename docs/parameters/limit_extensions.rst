limit_extensions (bool)
++++++++++++

.. warning::
   difPy result accuracy can not be guaranteed for file formats not covered by "limit_extensions".

By default, difPy only searches for images with a predefined filetype. This speeds up the process, since difPy does not have to attempt to decode files it might not support. Nonetheless, you can let difPy try to decode other file types by setting ``limit_extensions`` to ``False``.

.. note::

   Predefined image types includes: ``apng``, ``bw``, ``cdf``, ``cur``, ``dcx``, ``dds``, ``dib``, ``emf``, ``eps``, ``fli``, ``flc``, ``fpx``, ``ftex``, ``fits``, ``gd``, ``gd2``, ``gif``, ``gbr``, ``icb``, ``icns``, ``iim``, ``ico``, ``im``, ``imt``, ``j2k``, ``jfif``, ``jfi``, ``jif``, ``jp2``, ``jpe``, ``jpeg``, ``jpg``, ``jpm``, ``jpf``, ``jpx``, ``jpeg``, ``mic``, ``mpo``, ``msp``, ``nc``, ``pbm``, ``pcd``, ``pcx``, ``pgm``, ``png``, ``ppm``, ``psd``, ``pixar``, ``ras``, ``rgb``, ``rgba``, ``sgi``, ``spi``, ``spider``, ``sun``, ``tga``, ``tif``, ``tiff``, ``vda``, ``vst``, ``wal``, ``webp``, ``xbm``, ``xpm``.

``True`` = (default) difPy's search is limited to a set of predefined image types

``False`` = difPy searches through all the input files

difPy supports most popular image formats. Nevertheless, since it relies on the Pillow library for image decoding, the supported formats are restricted to the ones listed in the `Pillow Documentation`_. Unsupported file types will by marked as invalid and included in the process statistics output under ``invalid_files`` (see :ref:`Process Statistics`).

.. _Pillow Documentation: https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html