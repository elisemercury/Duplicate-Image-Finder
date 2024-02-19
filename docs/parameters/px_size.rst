px_size (int)
^^^^^^^^^^^^

.. note::

   Recommended not to change default value.

Absolute size in pixels (width x height) of the images before being compared. The higher the ``px_size``, the more precise the comparison, but in turn more computational resources are required for difPy to compare the images. The lower the ``px_size``, the faster, but the more imprecise the comparison process gets.

By default, ``px_size`` is set to ``50``.

**Manual setting**: ``px_size`` can be manually adjusted by setting it to any ``int``.