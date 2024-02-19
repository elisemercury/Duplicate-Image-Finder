processes (int)
^^^^^^^^^^^^

.. warning::
   Recommended not to change default value. Only adjust this value if you know what you are doing.

difPy leverages `Multiprocessing`_ to speed up the image comparison process, meaning multiple comparison tasks will be performed in parallel. The ``processes`` parameter defines the maximum number of worker processes (i. e. parallel tasks) to perform when multiprocessing. The higher the parameter, the more performance can be achieved, but in turn, the more computing resources will be required. To learn more, please refer to the `Python Multiprocessing documentation`_. 

.. _Multiprocessing: https://docs.python.org/3/library/multiprocessing.html

.. _Python Multiprocessing documentation: https://docs.python.org/3/library/multiprocessing.html#multiprocessing.pool.Pool

By default, ``processes`` is set to `os.cpu_count()`_. This means that difPy will spawn as many processes as number of CPUs in your machine, which can lead to increased performance, but can also cause a **big computing overhead** depending on the size of your dataset. To reduce the required computing power, it is recommended to reduce this value.

.. _os.cpu_count(): https://docs.python.org/3/library/os.html#os.cpu_count

**Manual setting**: ``processes`` can be manually adjusted by setting it to any ``int``. It is dependant on values supported by the ``process`` parameter in the Python Multiprocessing package. To learn more about this parameter, please refer to the `Python Multiprocessing documentation`_.