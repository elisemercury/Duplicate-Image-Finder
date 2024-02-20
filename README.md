<p align="center">
  <img src="static/difPy_logo_3.png" width="300" title="Example Output: Duplicate Image Finder">
</p>

# Duplicate Image Finder (difPy)

[![PyPIv](https://img.shields.io/pypi/v/difPy)](https://pypi.org/project/difPy/)
[![PyPI status](https://img.shields.io/pypi/status/difPy)](https://pypi.org/project/difPy/)
[![Documentation Status](https://readthedocs.org/projects/difpy/badge/?version=latest)](https://difpy.readthedocs.io/en/latest/?badge=latest)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/difPy)](https://pypi.org/project/difPy/)
[![Downloads](https://static.pepy.tech/badge/difpy)](https://pepy.tech/project/difpy)
[![PyPI - License](https://img.shields.io/pypi/l/difPy)](https://github.com/elisemercury/Duplicate-Image-Finder/blob/main/LICENSE.txt)
[<img src="https://img.shields.io/badge/dif-Py-blue?style=flat&logo=python&labelColor=white&logoWidth=20.svg/"></a>](https://github.com/elisemercury/Duplicate-Image-Finder/)

**Tired of going through all images in a folder and comparing them manually to check if they are duplicates?**

:white_check_mark: The Duplicate Image Finder (difPy) Python package **automates** this task for you!

```python
pip install difPy
```

> :point_right: :new: **difPy v4** is out! difPy v4 comes with up to **10x more performance** than previous difPy versions. Check out the [release notes](https://github.com/elisemercury/Duplicate-Image-Finder/releases/) for details. 

> :open_hands: Our motto? We :heart: Open Source! **Contributions and new ideas for difPy are always welcome** - check our [Contributor Guidelines](https://difpy.readthedocs.io/en/latest/contributing.html) for more information.

Read more on how the algorithm of difPy works in my Medium article [Finding Duplicate Images with Python](https://towardsdatascience.com/finding-duplicate-images-with-python-71c04ec8051).

Check out the [difPy package on PyPI.org](https://pypi.org/project/difPy/)

-------

## Description
difPy searches for images in **one or more different folders**, compares the images it found and checks whether these are duplicates. It then outputs the **image files classified as duplicates** as well as the **images having the lowest resolutions**, so you know which of the duplicate images are safe to be deleted. You can then either delete them manually, or let difPy delete them for you.

difPy does not compare images based on their hashes. It compares them based on their tensors i. e. the image content - this allows difPy to **not only search for duplicate images, but also for similar images**.

difPy leverages Python's **multiprocessing capabilities** and is therefore able to perform at high performance even on large datasets. 

:notebook: For a **detailed usage guide**, please view the official **[difPy Usage Documentation](https://difpy.readthedocs.io/)**.

## Table of Contents
1. [Basic Usage](https://github.com/elisemercury/Duplicate-Image-Finder#basic-usage)
2. [Output](https://github.com/elisemercury/Duplicate-Image-Finder#output)
3. [Additional Parameters](https://github.com/elisemercury/Duplicate-Image-Finder#additional-parameters)
4. [CLI Usage](https://github.com/elisemercury/Duplicate-Image-Finder#cli-usage)
5. [difPy Web App](https://github.com/elisemercury/Duplicate-Image-Finder#difpy-web-app)

## Basic Usage
To make difPy search for duplicates **within one folder**:

```python
import difPy
dif = difPy.build('C:/Path/to/Folder/')
search = difPy.search(dif)
``` 
To search for duplicates **within multiple folders**:

```python
import difPy
dif = difPy.build(['C:/Path/to/Folder_A/', 'C:/Path/to/Folder_B/', 'C:/Path/to/Folder_C/', ... ])
search = difPy.search(dif)
``` 

Folder paths can be specified as standalone Python strings, or within a list. With `difPy.build()`, difPy first scans the images in the provided folders and builds a collection of images by generating image tensors. `difPy.search()` then starts the search for duplicate images.

:notebook: For a **detailed usage guide**, please view the official **[difPy Usage Documentation](https://difpy.readthedocs.io/)**.

## Output
difPy returns various types of output that you may use depending on your use case: 

### I. Search Result Dictionary
A **JSON formatted collection** of duplicates/similar images (i. e. **match groups**) that were found. Each match group has a primary image (the key of the dictionary) which holds the list of its duplicates including their filename and MSE (Mean Squared Error). The lower the MSE, the more similar the primary image and the matched images are. Therefore, an MSE of 0 indicates that two images are exact duplicates.

```python
search.result

> Output:
{'C:/Path/to/Image/image1.jpg' : [['C:/Path/to/Image/duplicate_image1a.jpg', 0.0], 
                                  ['C:/Path/to/Image/duplicate_image1b.jpg', 0.0]],
 'C:/Path/to/Image/image2.jpg' : [['C:/Path/to/Image/duplicate_image2a.jpg', 0.0]],
 ...
}
``` 

### II. Lower Quality Files
A **list** of duplicates/similar images that have the **lowest quality** among match groups: 

```python
search.lower_quality

> Output:
['C:/Path/to/Image/duplicate_image1.jpg', 
 'C:/Path/to/Image/duplicate_image2.jpg', ...]
``` 

Lower quality images then can be **moved** to a different location:

```python
search.move_to(destination_path='C:/Path/to/Destination/')
```
Or **deleted**:

```python
search.delete(silent_del=False)
```

### III. Process Statistics

A **JSON formatted collection** with statistics on the completed difPy processes:

```python
search.stats

> Output:
{'directory': ['C:/Path/to/Folder_A/', 'C:/Path/to/Folder_B/', ... ],
 'process': {'build': {'duration': {'start': '2024-02-18T19:52:39.479548',
                                    'end': '2024-02-18T19:52:41.630027',
                                    'seconds_elapsed': 2.1505},
                       'parameters': {'recursive': True,
                                      'in_folder': False,
                                      'limit_extensions': True,
                                      'px_size': 50,
                                      'processes': 5},
                        'total_files': {'count': 3232},
                        'invalid_files': {'count': 0, 
                                          'logs': {}}},
             'search': {'duration': {'start': '2024-02-18T19:52:41.630027',
                                     'end': '2024-02-18T19:52:46.770077',
                                     'seconds_elapsed': 5.14},
                        'parameters': {'similarity_mse': 0,
                                       'rotate': True,
                                       'lazy': True,
                                       'processes': 5,
                                       'chunksize': None},
                        'files_searched': 3232,
                        'matches_found': {'duplicates': 3030, 
                                          'similar': 0}}}}
```

## Additional Parameters
difPy supports the following parameters:

```python
difPy.build(*directory, recursive=True, in_folder=False, limit_extensions=True, px_size=50, 
            show_progress=True, processes=None)
```

```python
difPy.search(difpy_obj, similarity='duplicates', rotate=True, lazy=True, show_progress=True, 
             processes=None, chunksize=None)
```

:notebook: For a **detailed usage guide**, please view the official **[difPy Usage Documentation](https://difpy.readthedocs.io/)**.

## CLI Usage
difPy can also be invoked through the CLI by using the following commands:

```python
python dif.py #working directory

python dif.py -D 'C:/Path/to/Folder/'

python dif.py -D 'C:/Path/to/Folder_A/' 'C:/Path/to/Folder_B/' 'C:/Path/to/Folder_C/'
```

> :point_right: Windows users can add difPy to their [PATH system variables](https://www.computerhope.com/issues/ch000549.htm) by pointing it to their difPy package installation folder containing the [`difPy.bat`](https://github.com/elisemercury/Duplicate-Image-Finder/difPy/difPy.bat) file. This adds `difPy` as a command in the CLI and will allow direct invocation of `difPy` from anywhere on the device.

difPy CLI supports the following arguments:

```python
dif.py [-h] [-D DIRECTORY [DIRECTORY ...]] [-Z OUTPUT_DIRECTORY] 
       [-r {True,False}] [-i {True,False}] [-le {True,False}] 
       [-px PX_SIZE]  [-s SIMILARITY] [-ro {True,False}]
       [-la {True,False}] [-proc PROCESSES] [-ch CHUNKSIZE] 
       [-mv MOVE_TO] [-d {True,False}] [-sd {True,False}]
       [-p {True,False}]
```

| | Parameter | | Parameter |
| :---: | ------ | :---: | ------ | 
| `-D` | directory | `-la` | lazy |
| `-Z` | output_directory | `-proc` | processes | 
| `-r`| recursive | `-ch` | chunksize |
| `-i`| in_folder | `-mv` | move_to |
| `-le` | limit_extensions | `-d` | delete |
| `-px` | px_size | `-sd` | silent_del |
| `-s`| similarity | `-p` | show_progress | 
| `-ro` | rotate | 

If no directory parameter is given in the CLI, difPy will **run on the current working directory**.

When running from the CLI, the output of difPy is written to files and **saved in the working directory** by default. To change the default output directory, specify the `-Z / -output_directory` parameter. The "xxx" in the output filenames is the current timestamp:

```python
difPy_xxx_results.json
difPy_xxx_lower_quality.json
difPy_xxx_stats.json
```

:notebook: For a **detailed usage guide**, please view the official **[difPy Usage Documentation](https://difpy.readthedocs.io/)**.

## difPy Web App

difPy can also be accessed via a browser. With difPy Web, you can compare **up to 200 images** and download a **deduplicated ZIP file** - all powered by difPy. [Read more](https://github.com/elisemercury/difPy-app). 

:iphone: **Try the new [difPy Web App](https://difpy.app/)**!

<p align="center">
  <a href="https://difpy.app/"><img src="docs/static/assets/difPyweb_demo.gif" width="700" title="Demo: difPy Web App"></a>
</p>

-------

<p align="center"><b>
:heart: Open Source
</b></p>