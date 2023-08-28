<span align="center">
  <img src="static/difPy_logo_3.png" width="300" title="Example Output: Duplicate Image Finder">
</span>

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

> :point_right: :new: **difPy v4-beta** is out! difPy v4 is up to **10x as fast** as previous difPy versions. Check out the [release notes](https://github.com/elisemercury/Duplicate-Image-Finder/releases/) for details. 

> :open_hands: Our motto? We :heart: Open Source! **Contributions and new ideas for difPy are always welcome** - check our [Contributor Guidelines](https://github.com/elisemercury/Duplicate-Image-Finder/wiki/Contributing-to-difPy) for more information.

Read more on how the algorithm of difPy works in my Medium article [Finding Duplicate Images with Python](https://towardsdatascience.com/finding-duplicate-images-with-python-71c04ec8051).

Check out the [difPy package on PyPI.org](https://pypi.org/project/difPy/)

-------

## Description
difPy searches for images in **one or more different folders**, compares the images it found and checks whether these are duplicates. It then outputs the **image files classified as duplicates** as well as the **images having the lowest resolutions**, so you know which of the duplicate images are safe to be deleted. You can then either delete them manually, or let difPy delete them for you.

difPy does not compare images based on their hashes. It compares them based on their tensors i. e. the image content - this allows difPy to **not only search for duplicate images, but also for similar images**.

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
dif = difPy.build("C:/Path/to/Folder/")
search = difPy.search(dif)
``` 
To search for duplicates **within multiple folders**:

```python
import difPy
dif = difPy.build(["C:/Path/to/Folder_A/", "C:/Path/to/Folder_B/", "C:/Path/to/Folder_C/", ... ])
search = difPy.search(dif)
``` 

Folder paths can be specified as standalone Python strings, or within a list. `difPy.build()` first builds a collection of images by scanning the provided folders and generating image tensors. `difPy.search()` then starts the search for duplicate image.

:notebook: For a **detailed usage guide**, please view the official **[difPy Usage Documentation](https://difpy.readthedocs.io/)**.

## Output
difPy returns various types of output that you may use depending on your use case: 

### I. Search Result Dictionary
A **JSON formatted collection** of duplicates/similar images (i. e. **match groups**) that were found, where the keys are a **randomly generated unique id** for each image file:

```python
search.result

> Output:
{20220819171549 : {"location" : "C:/Path/to/Image/image1.jpg",
                   "matches" : {30270813251529 : "location": "C:/Path/to/Image/matched_image1.jpg",
                                                 "mse": 0.0},
                               {72214282557852 : "location": "C:/Path/to/Image/matched_image2.jpg",
                                                 "mse": 0.0},
                   ... }
 ...
}
``` 

### II. Lower Quality Files
A **JSON formatted collection** of duplicates/similar images that have the **lowest quality** among match groups: 

```python
search.lower_quality

> Output:
{"lower_quality" : ["C:/Path/to/Image/duplicate_image1.jpg", 
                    "C:/Path/to/Image/duplicate_image2.jpg", ...]}
``` 

Lower quality images then can be moved to a different location:

```python
search.move_to(search, destination_path="C:/Path/to/Destination/")
```
Or deleted:

```python
search.delete(search, silent_del=False)
```

### III. Statistics

A **JSON formatted collection** with statistics on the completed difPy processes:

```python
search.stats

> Output:
{"directory" : ("C:/Path/to/Folder_A/", "C:/Path/to/Folder_B/", ... ),
 "process" : {"build" : {"duration" : {"start" : "2023-08-28T21:22:48.691008",
                                       "end" : "2023-08-28T21:23:59.104351",
                                       "seconds_elapsed" : "70.4133"},
                         "parameters" : {"recursive" : True,
                                         "in_folder" : False,
                                         "limit_extensions" : True,
                                         "px_size" : 50}},
              "search" : {"duration" : {"start" : "2023-08-28T21:23:59.106351",
                                        "end" : "2023-08-28T21:25:17.538015",
                                        "seconds_elapsed" : "78.4317"},
                          "parameters" : {"similarity_mse" : 0}
                          "files_searched" : 5225,
                          "matches_found" : {"duplicates" : 5,
                                             "similar" : 0}}}
"invalid_files" : {"count" : 230,
                   "logs" : {...}}})
```

## Additional Parameters
difPy supports the following parameters:

```python
difPy.build(*directory, recursive=True, in_folder=False, limit_extensions=True, 
px_size=50, show_progress=False, logs=True)
```

```python
difPy.search(difpy_obj, similarity='duplicates', show_progress=False, logs=True)
```

:notebook: For a **detailed usage guide**, please view the official **[difPy Usage Documentation](https://difpy.readthedocs.io/)**.

## CLI Usage
difPy can also be invoked through the CLI by using the following commands:

```python
python dif.py #working directory

python dif.py -D "C:/Path/to/Folder/"

python dif.py -D "C:/Path/to/Folder_A/" "C:/Path/to/Folder_B/" "C:/Path/to/Folder_C/"
```

> :point_right: Windows users can add difPy to their [PATH system variables](https://www.computerhope.com/issues/ch000549.htm) by pointing it to their difPy package installation folder containing the [`difPy.bat`](https://github.com/elisemercury/Duplicate-Image-Finder/difPy/difPy.bat) file. This adds `difPy` as a command in the CLI and will allow direct invocation of `difPy` from anywhere on the device.

difPy CLI supports the following arguments:

```python
dif.py [-h] [-D DIRECTORY] [-Z OUTPUT_DIRECTORY] [-r {True,False}] [-s SIMILARITY] [-px PX_SIZE] 
       [-mv MOVE_TO] [-le {True,False}] [-p {True,False}] [-d {True,False}] [-sd {True,False}] 
       [-l {True,False}]
```

| | Parameter | | Parameter |
| :---: | ------ | :---: | ------ | 
| `-D` | directory | `-p` | show_progress |  
| `-Z` | output_directory | `-mv` | move_to |
| `-r`| recursive | `-d` | delete |
| `-s`| similarity | `-sd` | silent_del |
| `-px` | px_size | `-l` | logs |
| `-le` | limit_extensions |  | |

When no directory parameter is given in the CLI, difPy will **run on the current working directory**.

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