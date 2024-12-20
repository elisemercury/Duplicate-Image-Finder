.. _desktop:

difPy for Desktop
----------------

difPy for Desktop brings image deduplication as an easy to use app to your desktop. We are now accepting beta tester sign ups and will soon be starting our first tester access wave.

✨🚀  `Join the difPy for Desktop beta tester program <https://difpy.short.gy/desktop-beta-rtd>`_ now and be among to first to test the new difPy desktop app!

Installation
^^^^^^^^^^

difPy for desktop is available as beta version for Windows and Mac.

➡️ Download the difPy v1.0-beta app for Windows (*currently only available for beta testers*)

➡️ Download the difPy v1.0-beta app for MacOs (*currently only available for beta testers*)

Basic Usage
^^^^^^^^^^

The difPy search process is divided into two steps: import and search. First folders need to be selected an imported, and then the search must be configured and can be started. 

A new search can be started by clicking the "New Search" button in the center of the screen. 

Import Folders
++++++++++++

You can import one or more folders at once by clicking the "Browse" button. You can also paste folder paths (separated by ";") directly into the text box.

When importing, you can select the following import modes:
* Recursive
* In-folder
* Pixel size (recommended not to change)

**Recursive**: defines whether difPy should search through the subfolders of the selected folders. If checked, difPy will search for matches in all subfolders.

**In-folder**: can only be selected if at least 2 folders have been imported. If selected, difPy will treat the folders as separate and only search for matches within the selected folders themselves.

**Pixel size**: recommended not to change default value. Defines the width and height to which the images are compressed to before the search. The higher, the more precise but the slower the search. Default value is 50. If more precision is needed, incrementing in small steps of 50, starting with 100.

Configure Search
++++++++++++

The difPy search can be configured to search for:
* duplicate or
* similar images

**Duplicate**: When difPy searches for duplicates, it searches foe exact matches and the mean squared error (MSE) is set to 0. The result will only contain matches of images that are exact duplicates of each other. Whenever you are searching for duplicate images with different file formats (i. e. imageA.png is a duplicate of imageB.jpg), it is recommended to set the search similarity to "similar".

**Similar**: When searching for similar images, the MSE is set to 5. The results will contain images that have a MSE of 5 or less (i. e. it will include duplicate matches and similar matches). 

.. note::
    Currently the similarity MSE value can not be customized in the desktop app. If you need a different MSE value, please use the command line version of difPy.

**Rotate**: When configuring the search, you can also select whether to **rotate** the images on comparison or not. If selected, difPy will rotate the images by 90°, 180°, or 270° at each comparison.

Advanced Settings
^^^^^^^^^^

From the difPy settings on the main menu, you can access advances search settings. 

.. warning::
    It is not recommended to change the advanced settings unless you know what you are doing.

**Proceses**: Defines the maximum number of worker processes (i. e. parallel tasks) to perform when multiprocessing. The more processes, the faster the search, but the more processing power the app will use. See :ref:`processes` for more information.

**Chunksize**: The number of image sets that should be compared at once per process. The higher the chunksize, the faster the search, but the more memory the app will use. See :ref:`chunksize` for more information.

The ``process`` and ``chunksize`` are only used when difPy receives more than 5k images to process. With large datasets, it can make sense to adjust these parameters. For example, in order to lower the overall CPU overhead, you could lower ``processes``. In order to decrease memory usage, you could decrease ``chunksize``. The higher both parameters, the more performance you will gain, but the more resources the app will use.

Limitations
^^^^^^^^^^

* Using the difPy desktop app for large datasets can lead to slower processing times. For better performance, with large datasets (> 10k images) it is recommended to use the command line version / Python package of difPy instead. See `here <https://pypi.org/project/difPy/>`_ for more information.

* The desktop app is currently only available for Windows and Mac.

* The desktop app is currently in beta and may contain bugs. If you encounter any issues, please report them on the GitHub repository.

Give Feedback / Report Bug
^^^^^^^^^^

Did you encounter an issue with the difPy desktop app? 🐞 Please report it `here <https://github.com/elisemercury/difpy-for-desktop/issues/new`_.

Do you have feedback about the difPy desktop app? Anything you think could be improved? 🗨️ Share your feedback with us `here <https://github.com/elisemercury/difpy-for-desktop/discussions/new?category=feedback>`_.