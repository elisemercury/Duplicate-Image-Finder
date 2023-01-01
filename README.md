# Duplicate Image Finder (difPy)

![PyPIv](https://img.shields.io/pypi/v/difPy)
![PyPI status](https://img.shields.io/pypi/status/difPy)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/difPy)
![PyPI - License](https://img.shields.io/pypi/l/difPy)
<img src="https://img.shields.io/badge/dif-Py-blue?style=flat&logo=python&labelColor=white&logoWidth=20.svg/"></a>

**Tired of going through all images in a folder and comparing them manually to check if they are duplicates?**

:white_check_mark: The Duplicate Image Finder (difPy) Python package **automates** this task for you!

```python
pip install difPy
```
> :point_right: difPy v2.4.x  has some **major updates** and **new features**. Check out the [release notes](https://github.com/elisemercury/Duplicate-Image-Finder/releases/) for a detailed listing. 

> :open_hands: Our motto? The more users use difPy, the more issues and missing features can be detected, and the better the algorithm gets over time. **Contributions are always welcome** - check our [contributor guidelines](https://github.com/elisemercury/Duplicate-Image-Finder/wiki/Contributing-to-difPy) for more information.

Read more on how the algorithm of difPy works in my Medium article [Finding Duplicate Images with Python](https://towardsdatascience.com/finding-duplicate-images-with-python-71c04ec8051).

Check out the [difPy package on PyPI.org](https://pypi.org/project/difPy/)

-------

## Description
DifPy searches for images in **one or two different folders**, compares the images it found and checks whether these are duplicates. It then outputs the **image files classified as duplicates** and the **filenames of the duplicate images having the lower resolution**, so you know which of the duplicate images are safe to be deleted. You can then either delete them manually, or let difPy delete them for you.

<p align="center">
  <img src="example_output.png" width="400" title="Example Output: Duplicate Image Finder">
</p>

DifPy does not compare images based on their hashes. It compares them based on their tensors i. e. the image content - this allows difPy to not only search for duplicate images, but also for similar images.

## Basic Usage
Use the following function to make difPy search for duplicates within one specific folder and its subfolders:

```python
from difPy import dif
search = dif("C:/Path/to/Folder/")
``` 
To search for duplicates within two folders and their subfolders:

```python
from difPy import dif
search = dif("C:/Path/to/Folder_A/", "C:/Path/to/Folder_B/")
``` 
Folder paths must be specified as a Python string.

:notebook: For a **detailed usage guide**, please view the official **[difPy Usage Documentation](https://github.com/elisemercury/Duplicate-Image-Finder/wiki/difPy-Usage-Documentation)**.

## Output
DifPy gives two types of output that you may use depending on your use case: 

A **dictionary** of duplicates/similar images that were found, where the keys are a **unique id** for each image file:

```python
search.result

> Output:
{20220824212437767808 : {"filename" : "image1.jpg",
                         "location" : "C:/Path/to/Image/image1.jpg"},
                         "duplicates" : ["C:/Path/to/Image/duplicate_image1.jpg",
                                         "C:/Path/to/Image/duplicate_image2.jpg"]},
...
}
``` 

A **list** of duplicates/similar images that have the **lowest quality:** 

```python
search.lower_quality

> Output:
["C:/Path/to/Image/duplicate_image1.jpg", 
 "C:/Path/to/Image/duplicate_image2.jpg", ...]
``` 

DifPy can also generate a **dictionary** with statistics on the completed process:

```python
search.stats 

> Output:
{"directory_1" : "C:/Path/to/Folder_A/",
 "directory_2" : "C:/Path/to/Folder_B/",
 "duration" : {"start_date": "2022-06-13",
               "start_time" : "14:44:19",
               "end_date" : "2022-06-13",
               "end_time" : "14:44:38",
               "seconds_elapsed" : 18.6113},
 "recursive" : True,
 "similarity_grade" : "normal",
 "similarity_mse" : 200,
 "total_files_searched" : 1032,
 "total_dupl_sim_found" : 1024}
``` 

## Additional Parameters
DifPy has the following optional parameters:

```python
dif(directory_A, directory_B, recursive=True, similarity="normal", px_size=50, 
    show_progress=True, show_output=False, delete=False, silent_del=False)
```

:notebook: For a **detailed usage guide**, please view the official **[difPy Usage Documentation](https://github.com/elisemercury/Duplicate-Image-Finder/wiki/difPy-Usage-Documentation)**.

## CLI Usage
You can make use of difPy through the CLI interface by using the following commands:

```python
python dif.py -A "C:/Path/to/Folder_A/"

python dif.py -A "C:/Path/to/Folder_A/" -B "C:/Path/to/Folder_B/"
```
It supports the following arguments:

```python
dif.py [-h] -A DIRECTORY_A [-B [DIRECTORY_B]] [-Z [OUTPUT_DIRECTORY]] 
       [-r [{True,False}]] [-s [{low,normal,high,int}]] [-px [PX_SIZE]] 
       [-p [{True,False}]] [-o [{True,False}]] 
       [-d [{True,False}]] [-D [{True,False}]]
```

The output of difPy is then written to files and saved in the working directory by default, or to the folder specified in the `-Z / -output_directory` parameter. The "xxx" in the filename is a unique timestamp:

```python
difPy_results_xxx.json
difPy_lower_quality_xxx.txt
difPy_stats_xxx.json
```

:notebook: For a **detailed usage guide**, please view the official **[difPy Usage Documentation](https://github.com/elisemercury/Duplicate-Image-Finder/wiki/difPy-Usage-Documentation)**.

## Similar Work 

### I. DifPy as Webapp

[A Streamlit based Webapp to find duplicate images from single/multiple directories](https://github.com/prateekralhan/Streamlit-based-Duplicate-Images-Finder) - :dna: **based on difPy**

**Single Directory** 📸✅
![demo1](https://user-images.githubusercontent.com/29462447/174408835-438234d9-5ff6-4159-a5e3-b908d885a8bc.gif)

**Two directories** 📸✅
![demo2](https://user-images.githubusercontent.com/29462447/174408842-5128838f-bf8f-43da-97d2-30a3264eb7af.gif)

### II. Mac Photos Tool to find Duplicates (photosdup)

[Tool to scan a Mac Photos library for duplicates, thumbnails etc.](https://github.com/peter-sk/photosdup) - :sparkles: **inspired by difPy**

-------

***
<p align="center"><b>
:thought_balloon: Also want to be featured in the "Related Projects" section? Check our <a href="https://github.com/elisemercury/Duplicate-Image-Finder/wiki/Contributing-to-difPy#be-featured-as-difpy-related-project">contributor guidelines</a> to find out how!
</b></p>
