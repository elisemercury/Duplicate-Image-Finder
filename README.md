# Duplicate Image Finder (difPy)

![PyPIv](https://img.shields.io/pypi/v/difPy)
![PyPI status](https://img.shields.io/pypi/status/difPy)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/difPy)
[![Downloads](https://static.pepy.tech/badge/difpy)](https://pepy.tech/project/difpy)
![PyPI - License](https://img.shields.io/pypi/l/difPy)
<img src="https://img.shields.io/badge/dif-Py-blue?style=flat&logo=python&labelColor=white&logoWidth=20.svg/"></a>

**Tired of going through all images in a folder and comparing them manually to check if they are duplicates?**

:white_check_mark: The Duplicate Image Finder (difPy) Python package **automates** this task for you!

```python
pip install difPy
```
> :point_right: [NEW] difPy v3.0.0 has ben released! Count on signifcant **performance increases**, **new features** and **bug fixes**. Check out the [release notes](https://github.com/elisemercury/Duplicate-Image-Finder/releases/) for a detailed listing. 

> :open_hands: Our motto? We :heart: Open Source! **Contributions and new ideas for difPy are always welcome** - check our [contributor guidelines](https://github.com/elisemercury/Duplicate-Image-Finder/wiki/Contributing-to-difPy) for more information.

Read more on how the algorithm of difPy works in my Medium article [Finding Duplicate Images with Python](https://towardsdatascience.com/finding-duplicate-images-with-python-71c04ec8051).

Check out the [difPy package on PyPI.org](https://pypi.org/project/difPy/)

-------

## Description
DifPy searches for images in **one or more different folders**, compares the images it found and checks whether these are duplicates. It then outputs the **image files classified as duplicates** as well as the **images having the lowest resolutions**, so you know which of the duplicate images are safe to be deleted. You can then either delete them manually, or let difPy delete them for you.

<p align="center">
  <img src="example_output.png" width="400" title="Example Output: Duplicate Image Finder">
</p>

DifPy does not compare images based on their hashes. It compares them based on their tensors i. e. the image content - this allows difPy to **not only search for duplicate images, but also for similar images**.

## Basic Usage
Use the following function to make difPy search for duplicates within one specific folder and its subfolders:

```python
from difPy import dif
search = dif("C:/Path/to/Folder/")
``` 
To search for duplicates within mutliple folders and their subfolders:

```python
from difPy import dif
search = dif("C:/Path/to/Folder_A/", "C:/Path/to/Folder_B/", "C:/Path/to/Folder_C/", ...)
``` 
Folder paths must be specified as a Python string.

:notebook: For a **detailed usage guide**, please view the official **[difPy Usage Documentation](https://github.com/elisemercury/Duplicate-Image-Finder/wiki/difPy-Usage-Documentation)**.

## Output
DifPy returns various types of output that you may use depending on your use case: 

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
A **list** of duplicates/similar images that have the **lowest quality** among match groups: 

```python
search.lower_quality

> Output:
["C:/Path/to/Image/duplicate_image1.jpg", 
 "C:/Path/to/Image/duplicate_image2.jpg", ...]
``` 

A **JSON formatted collection** with statistics on the completed difPy process:

```python
search.stats

> Output:
{"directory" : ("C:/Path/to/Folder_A/", "C:/Path/to/Folder_B/", ... ),
 "duration" : {"start_date": "2023-02-15",
               "start_time" : "18:44:19",
               "end_date" : "2023-02-15",
               "end_time" : "18:44:38",
               "seconds_elapsed" : 18.6113},
 "recursive" : True,
 "match_mse" : 200,
 "files_searched" : 1032,
 "matches_found" : 852,
 "invalid_files" : 4}
``` 

## Additional Parameters
DifPy supports the following parameters:

```python
dif(*directory, recursive=True, similarity="normal", px_size=50, 
    show_progress=True, show_output=False, delete=False, silent_del=False)
```

:notebook: For a **detailed usage guide**, please view the official **[difPy Usage Documentation](https://github.com/elisemercury/Duplicate-Image-Finder/wiki/difPy-Usage-Documentation)**.

## CLI Usage
You can make use of difPy through a CLI interface by using the following commands:

```python
python dif.py -D "C:/Path/to/Folder/"

python dif.py -D"C:/Path/to/Folder_A/" "C:/Path/to/Folder_B/" "C:/Path/to/Folder_C/"
```
It supports the following arguments:

```python
dif.py [-h] -D DIRECTORY [-Z [OUTPUT_DIRECTORY]] 
       [-r [{True,False}]] [-s [{low,normal,high,int}]] [-px [PX_SIZE]] 
       [-p [{True,False}]] [-o [{True,False}]]
       [-d [{True,False}]] [-sd [{True,False}]]
```

:bell: Since [version v3.0.0](https://github.com/elisemercury/Duplicate-Image-Finder/releases/tag/v3.0.0), the CLI parameter `directory` has changed to `-D` and `silend_del` to `-sd`.


| | Parameter | | Parameter |
| :---: | ------ | :---: | ------ | 
| `-D` | directory | `-p` | show_progress |  
| `-Z` | output_directory | `-o` | show_output |
| `-r`| recursive | `-d` | delete |
| `-s` | similarity | `-D` | silent_del |
| `-px` | px_size | 

When running from the CLI, the output of difPy is  written to files and saved in the working directory by default. To change the default output directory, specify the `-Z / -output_directory` parameter. The "xxx" in the output filenames is a unique timestamp:

```python
difPy_results_xxx.json
difPy_lower_quality_xxx.csv
difPy_stats_xxx.json
```

:notebook: For a **detailed usage guide**, please view the official **[difPy Usage Documentation](https://github.com/elisemercury/Duplicate-Image-Finder/wiki/difPy-Usage-Documentation)**.

## Related Projects

The below sections features third-party work that has been **built with** or **inspired by** difPy. We would like to express a big thank you for any contributions made to difPy.

<p align="center"><b>
:thought_balloon: Also want to be featured in the "Related Projects" section? Check our <a href="https://github.com/elisemercury/Duplicate-Image-Finder/wiki/Contributing-to-difPy#be-featured-as-difpy-related-project">contributor guidelines</a> to find out how!
</b></p>

### I. DifPy as Webapp - by @prateekralhan

[A Streamlit based Webapp to find duplicate images from single/multiple directories](https://github.com/prateekralhan/Streamlit-based-Duplicate-Images-Finder) - :dna: **built with difPy**

**Single Directory** 📸✅
![demo1](https://user-images.githubusercontent.com/29462447/174408835-438234d9-5ff6-4159-a5e3-b908d885a8bc.gif)

**Two directories** 📸✅
![demo2](https://user-images.githubusercontent.com/29462447/174408842-5128838f-bf8f-43da-97d2-30a3264eb7af.gif)

### II. Mac Photos Tool to find Duplicates (photosdup) - by @peter-sk

[Tool to scan a Mac Photos library for duplicates, thumbnails etc.](https://github.com/peter-sk/photosdup) - :sparkles: **inspired by difPy**

-------

<p align="center"><b>
:thought_balloon: Also want to be featured in the "Related Projects" section? Check our <a href="https://github.com/elisemercury/Duplicate-Image-Finder/wiki/Contributing-to-difPy#be-featured-as-difpy-related-project">contributor guidelines</a> to find out how!
</b></p>

-------

<p align="center"><b>
We :heart: Open Source 
</b></p>