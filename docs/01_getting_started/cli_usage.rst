.. _cli usage:

CLI Usage
----------------

difPy can be invoked through a CLI interface by using the following commands:

.. code-block:: python

   python dif.py #working directory

   python dif.py -D 'C:/Path/to/Folder/'

   python dif.py -D 'C:/Path/to/Folder_A/' 'C:/Path/to/Folder_B/' 'C:/Path/to/Folder_C/'

.. note::

   Windows users can add difPy to their `PATH system variables <https://www.computerhope.com/issues/ch000549.htm>`_ by pointing it to their difPy package installation folder containing the `difPy.bat <https://github.com/elisemercury/Duplicate-Image-Finder/blob/main/difPy/difPy.bat>`_ file. This adds ``difPy`` as a command in the CLI and will allow direct invocation of difPy from anywhere on the machine. The default difPy installation folder will look similar to ``C:\Users\User\AppData\Local\Programs\Python\Python311\Lib\site-packages\difPy`` (Windows 11).

difPy in the CLI supports the following arguments:

.. code-block:: python
   
   dif.py [-h] [-D DIRECTORY [DIRECTORY ...]] [-Z OUTPUT_DIRECTORY] 
          [-r {True,False}] [-i {True,False}] [-le {True,False}] 
          [-px PX_SIZE]  [-s SIMILARITY] [-ro {True,False}]
          [-dim {True,False}] [-proc PROCESSES] [-ch CHUNKSIZE] 
          [-mv MOVE_TO] [-d {True,False}] [-sd {True,False}]
          [-p {True,False}]

.. csv-table::
   :header: Cmd,Parameter,Cmd,Parameter
   :widths: 5, 10, 5, 10
   :class: tight-table

   ``-D``,:ref:`directory`,``-la``,:ref:`same_dim`
   ``-Z``,output_directory,``-proc``,:ref:`processes`
   ``-r``,:ref:`recursive`,``-ch``,:ref:`chunksize`
   ``-i``,:ref:`in_folder`,``-mv``,move_to (see :ref:`search.move_to`)
   ``-le``,:ref:`limit_extensions`,``-d``,delete (see :ref:`search.delete`)
   ``-px``,:ref:`px_size`,``-sd``,:ref:`silent_del`
   ``-s``,:ref:`similarity`,``-p``,:ref:`show_progress`
   ``-ro``,:ref:`rotate`,

If no directory parameter is given in the CLI, difPy will **run on the current working directory**.

The output of difPy is written to files and **saved in the working directory** by default. To change the default output directory, specify the ``-Z / -output_directory`` parameter. The "xxx" in the output filenames is the current timestamp:

.. code-block:: python

   difPy_xxx_results.json
   difPy_xxx_lower_quality.txt
   difPy_xxx_stats.json