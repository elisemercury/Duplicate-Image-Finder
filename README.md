# Duplicate Image Finder (difPy)
**Tired of going through all images in a folder and comparing them manually to check if they are duplicates?**

:white_check_mark: The Duplicate Image Finder (difPy) Python package **automates** this task for you!

```python
pip install difPy
```

Read more on how the algorithm of the DIF works in my Medium article [Finding Duplicate Images with Python](https://towardsdatascience.com/finding-duplicate-images-with-python-71c04ec8051)

Check out the [difPy package on PyPI.org](https://pypi.org/project/difPy/)

## Description
The DIF searches for images in a specified target folder, compares the images it found and checks whether these are duplicates. It then outputs the **image files classified as duplicates** and the **filenames of the duplicate images having the lower resolution**, so you know which of the duplicate images are safe to be deleted. You can then either delete them manually, or let the DIF delete them for you.

<p align="center">
  <img src="example_output.png" width="600" title="Example Output: Duplicate Image Finder">
</p>

## Basic Usage
Use the following function to make DIF search for duplicates in the specified folder:

```python
from difPy import dif
compare_images("C:/Path/to/Folder/")
``` 
Folder path must be specified as a Python string.

## Additional Parameters
The ``compare_images`` function has the following optional parameters:

```python
compare_images(directory, show_imgs=True, similarity="normal", px_size=50, delete=False)
```

### show_imgs (bool)

Per default, the DIF will output only the filename of the duplicate images it found. If you want the duplicate images to be shown in the console output, change this value to ``True``.

```False```= (default) outputs filename of the duplicate/similar images found

```True``` = outputs a sample and the filename

### similarity (str)

Depending on which use-case you want to apply DIF for, the granularity for the classification of the images can be adjusted.

The DIF can f. e. search for exact matching duplicate images, or images that look similar, but are not necessarily duplicates.

``"normal"`` = (recommended, default) searches for duplicates (with a certain tolerance)

``"high"`` = searches for duplicate images with extreme precision, f. e. for use with images that contain a lot of text     

``"low"`` = searches for similar images

### px_size (int)

! Recommended not to change default value

Absolute size in pixels (width x height) of the images before being compared.
The higher the px_size, the more computational ressources and time required.     
                           
### delete (bool)

! Please use with care, as this cannot be undone

When set to ``True``, the lower resolution duplicate images that were found by the DIF are automatically deleted from the folder.   
                           
