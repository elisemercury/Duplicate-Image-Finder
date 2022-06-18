# Duplicate Image Finder (difPy)

![PyPIv](https://img.shields.io/pypi/v/difPy)
![PyPI status](https://img.shields.io/pypi/status/difPy)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/difPy)
![PyPI - License](https://img.shields.io/pypi/l/difPy)

**Tired of going through all images in a folder and comparing them manually to check if they are duplicates?**

:white_check_mark: The Duplicate Image Finder (difPy) Python package **automates** this task for you!

```python
pip install difPy
```
> :point_right: difPy v2.x  has some **major updates** and **new features**. Check out the [release notes](https://github.com/elisemercury/Duplicate-Image-Finder/releases/) for a detailed listing.

> :open_hands: You find difPy is missing a feature? **Contributions are always welcome** - check our [contributor guidelines](https://github.com/elisemercury/Duplicate-Image-Finder/wiki/Contributing-to-difPy) for more information.

Read more on how the algorithm of difPy works in my Medium article [Finding Duplicate Images with Python](https://towardsdatascience.com/finding-duplicate-images-with-python-71c04ec8051).

Check out the [difPy package on PyPI.org](https://pypi.org/project/difPy/)

## Description
DifPy searches for images in **one or two different folders**, compares the images it found and checks whether these are duplicates. It then outputs the **image files classified as duplicates** and the **filenames of the duplicate images having the lower resolution**, so you know which of the duplicate images are safe to be deleted. You can then either delete them manually, or let difPy delete them for you.

<p align="center">
  <img src="example_output.png" width="400" title="Example Output: Duplicate Image Finder">
</p>

## Basic Usage
Use the following function to make difPy search for duplicates in one specified folder:

```python
from difPy import dif
search = dif("C:/Path/to/Folder/")
``` 
To search for duplicates within two folders:

```python
from difPy import dif
search = dif("C:/Path/to/Folder_A/", "C:/Path/to/Folder_B/")
``` 
Folder paths must be specified as a Python string.

## Output
DifPy gives two types of output that you may use depending on your use case: 

A **dictionary** of duplicates/similar images that were found: 

```python
search.result

> Output:
{"image1" : {"location" : "C:/Path/to/Image/image1.jpg"},
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
 "similarity_grade" : "normal",
 "similarity_mse" : 200,
 "total_images_searched" : 1032,
 "total_images_found" : 1024}
``` 

## Additional Parameters
DifPy has the following optional parameters:

```python
dif(directory_A, directory_B, similarity="normal", px_size=50, 
    sort_output=False, show_output=False, show_progress=False, delete=False, silent_del=False)
```
### similarity (str)

Depending on which use-case you want to apply difPy for, the granularity for the classification of the images can be adjusted.

DifPy can f. e. search for exact matching duplicate images, or images that look similar, but are not necessarily duplicates.

``"normal"`` = (recommended, default) searches for duplicates (with a certain tolerance)

``"high"`` = searches for duplicate images with extreme precision, f. e. for use with images that contain a lot of text     

``"low"`` = searches for similar images

### px_size (int)

! Recommended not to change default value

Absolute size in pixels (width x height) of the images before being compared.
The higher the px_size, the more computational ressources and time required. 
   
### sort_output (bool)

Per default, difPy will output the filenames of the duplicate images within a dictionary by the order in which they were found. If you want the duplicate images to be ordered alphabetically then set sort_output to `true`.

```False```= (default) output filenames of the duplicate/similar images by order they were found 

```True``` = outputs filesnames of duplicate/similar images in alphabetic order

### show_output (bool)

Per default, difPy will output only the filename of the duplicate images it found. If you want the duplicate images to be shown in the console output, change this value to ``True``.

```False```= (default) outputs filename of the duplicate/similar images found

```True``` = outputs a sample and the filename

### show_progress (bool)

Per default, difPy will set this progress bar to ``False``. If you want to see where your lengthy processing is, change this value to ``True``.

```False```= (default) no progress bar is shown

```True``` = outputs a progress bar

### delete (bool)

! Please use with care, as this cannot be undone

When set to ``True``, the lower resolution duplicate images that were found by difPy are deleted from the folder. Asks for user confirmation before deleting the images. To skip the user confimation, set silent_del to ```True```.  
                           
### silent_del (bool)

! Please use with care, as this cannot be undone

When set to ``True``, the user confirmation is skipped and the lower resolution duplicate images that were found by difPy are automatically deleted from the folder.

## Similar Work 
[A Streamlit based Webapp to find duplicate images from single/multiple directories based on difPy](https://github.com/prateekralhan/Streamlit-based-Duplicate-Images-Finder)

##### Single Directory 📸✅
![demo1](https://user-images.githubusercontent.com/29462447/174408835-438234d9-5ff6-4159-a5e3-b908d885a8bc.gif)

##### Two directories 📸✅
![demo2](https://user-images.githubusercontent.com/29462447/174408842-5128838f-bf8f-43da-97d2-30a3264eb7af.gif)



