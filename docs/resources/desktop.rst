.. _desktop:

.. note::
    ✨🚀  `Join the difPy for Desktop beta tester program <https://difpy.short.gy/desktop-beta-rtd>`_ now and be among to first to test the new difPy desktop app!

difPy for Desktop
----------------

difPy for Desktop brings image deduplication as an easy to use app to your desktop. We are now accepting beta tester sign ups and will soon be starting our first tester access wave.

.. _dsk_installation:

Installation
^^^^^^^^^^

difPy for desktop is available as beta version for Windows and Mac.

➡️ Download the difPy v1.0-beta app for Windows (*currently only available for beta testers*)

➡️ Download the difPy v1.0-beta app for MacOs (*currently only available for beta testers*)

.. _dsk_basic_usage:

Basic Usage
^^^^^^^^^^

The difPy search process is divided into two steps: (1) import and (2) search. First folders need to be selected an imported, and then the search must be configured and can be started. 

A new search can be started by clicking the "New Search" button in the center of the screen. 

.. _dsk_import:

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

.. _dsk_search:

Configure Search
++++++++++++

The difPy search can be configured to search for:

* duplicate or

* similar images

**Duplicate**: When difPy searches for duplicates, it searches foe exact matches and the mean squared error (MSE) is set to 0. The result will only contain matches of images that are exact duplicates of each other. Whenever you are searching for duplicate images with different file formats (i. e. imageA.png is a duplicate of imageB.jpg), it is recommended to set the search similarity to "similar".

**Similar**: When searching for similar images, the MSE is set to 5. The results will contain images that have a MSE of 5 or less (i. e. it will include duplicate matches and similar matches). Currently the similarity MSE value can not be customized in the desktop app. If you need a different MSE value, please use the command line version of difPy.

**Rotate**: When configuring the search, you can also select whether to **rotate** the images on comparison or not. If selected, difPy will rotate the images by 90°, 180°, or 270° at each comparison.

.. _dsk_results:

Search Results
++++++++++++

When difPy has completed the search, the results will be displayed, incl. the number of duplicate and/or similar matches it found.

You can either:

* **View the Search Logs** for more information about the search process

* **View the Search Results** and manage your duplicate images in the difPy **Image Viewer**. See :ref:`image_viewer` for more information.

.. _image_viewer:

Image Viewer
^^^^^^^^^^

The difPy image viewer allows you to view the duplicate images and easily manage them. The Image Viewer lets you go through each group of matches, see the resolutions of each of the images so that you know which ones are safe to delete. 

For each image, you you have the option to open it, move them it a new folder, or delete it.

If you want to delete all lower resolution matches at once, you can use the "Bulk Actions..." dropdown menu and select the bulk action you would like to take.

.. _dsk_advanced_settings:

Advanced Settings
^^^^^^^^^^

From the difPy settings on the main menu, you can access advances search settings. 

.. warning::
    It is not recommended to change the advanced settings unless you know what you are doing.

**Proceses**: Defines the maximum number of worker processes (i. e. parallel tasks) to perform when multiprocessing. The more processes, the faster the search, but the more processing power the app will use. See :ref:`processes` for more information.

**Chunksize**: The number of image sets that should be compared at once per process. The higher the chunksize, the faster the search, but the more memory the app will use. See :ref:`chunksize` for more information.

The ``process`` and ``chunksize`` are only used when difPy receives more than 5k images to process. With large datasets, it can make sense to adjust these parameters. For example, in order to lower the overall CPU overhead, you could lower ``processes``. In order to decrease memory usage, you could decrease ``chunksize``. The higher both parameters, the more performance you will gain, but the more resources the app will use.

.. _dsk_limitations:

Limitations
^^^^^^^^^^

* Using the difPy desktop app for large datasets can lead to slower processing times. For better performance, with large datasets (> 10k images) it is recommended to use the command line version / Python package of difPy instead. See `here <https://pypi.org/project/difPy/>`_ for more information.

* The desktop app is currently only available for Windows and Mac.

* The desktop app is currently in beta and may contain bugs. If you encounter any issues, please report them on the GitHub repository.

.. _dsk_feedback:

Give Feedback / Report Bug
^^^^^^^^^^

Did you encounter an issue with the difPy desktop app? 🐞 Please report it `here <https://github.com/elisemercury/difpy-for-desktop/issues/new>`_.

Do you have feedback about the difPy desktop app? Anything you think could be improved? 🗨️ Share your feedback with us `here <https://github.com/elisemercury/difpy-for-desktop/discussions/new?category=feedback>`_.