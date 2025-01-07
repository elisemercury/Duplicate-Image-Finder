.. _Supported File Types:

Supported File Types
----------------

difPy supports most popular image formats. Nevertheless, since it relies on the Pillow library for image decoding, the supported formats are restricted to the ones listed in the `Pillow Documentation`_. Unsupported file types will by marked as invalid and included in the process statistics output under ``invalid_files`` (see :ref:`Process Statistics`).

.. _Pillow Documentation: https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html