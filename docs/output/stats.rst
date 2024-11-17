A **JSON formatted collection** with statistics on the completed difPy process:

.. code-block:: python

   search.stats

   > Output:
   {'directory': ['C:/Path1/', 'C:/Path2/', ... ],
    'process': {'build': {'duration': {'start': '2024-02-18T19:52:39.479548',
                                       'end': '2024-02-18T19:52:41.630027',
                                       'seconds_elapsed': 2.1505},
                          'parameters': {'recursive': True,
                                         'in_folder': False,
                                         'limit_extensions': True,
                                         'px_size': 50,
                                         'processes': 5}},
                'search': {'duration': {'start': '2024-02-18T19:52:41.630027',
                                        'end': '2024-02-18T19:52:46.770077',
                                        'seconds_elapsed': 5.14},
                           'parameters': {'similarity_mse': 0,
                                          'rotate': True,
                                          'lazy': True,
                                          'processes': 5,
                                          'chunksize': None},
                           'files_searched': 3228,
                           'matches_found': {'duplicates': 3030, 
                                             'similar': 0}}},
    'total_files': 3232,
    'invalid_files': {'count': 4, 
                      'logs': {'C:/Path/invalid_File.pdf': 'Unsupported file type', 
                               ... }}}}