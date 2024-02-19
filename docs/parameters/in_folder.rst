in_folder (bool)
++++++++++++

By default, difPy will search for matches in the union of all directories specified in the :ref:`directory` parameter. To have difPy only search for matches within each folder separately, set ``in_folder`` to ``True``.

``True`` = searches for matches only among each individual directory, including subdirectories

``False`` = (default) searches for matches in the union of all directories