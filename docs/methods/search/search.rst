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

.. include:: /parameters/similarity.rst
   
.. _lazy:

.. include:: /parameters/lazy.rst

.. _rotate:

.. include:: /parameters/rotate.rst

.. _show_progress2:

.. include:: /parameters/show_progress.rst

.. _processes2:

.. include:: /parameters/processes.rst

.. _chunksize:

.. include:: /parameters/chunksize.rst

.. _logs2:

.. include:: /parameters/deprecated/logs.rst