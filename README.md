# Duplicate Image Finder (difPy)

**Tired of going through all images in a folder and comparing them manually to check if they are duplicates?**

:white_check_mark: The Duplicate Image Finder (difPy) Python package **automates** this task for you!

```python
pip install difPy
```
> :point_right: difPy v2.4.x  has some **major updates** and **new features**. Check out the [release notes](https://github.com/elisemercury/Duplicate-Image-Finder/releases/) for a detailed listing. 

> :open_hands: Our motto? The more users use difPy, the more issues and missing features can be detected, and the better the algorithm gets over time. **Contributions are always welcome** - check our [contributor guidelines](https://github.com/elisemercury/Duplicate-Image-Finder/wiki/Contributing-to-difPy) for more information.

Read more on how the algorithm of difPy works in my Medium article [Finding Duplicate Images with Python](https://towardsdatascience.com/finding-duplicate-images-with-python-71c04ec8051).

For a **detailed usage guide**, please view the official **[difPy Usage Documentation](https://github.com/elisemercury/Duplicate-Image-Finder/wiki/difPy-Usage-Documentation)**.

-------

## Description
DifPy searches for images in **one or two different folders**, compares the images it found and checks whether these are duplicates. It then outputs the **image files classified as duplicates** and the **filenames of the duplicate images having the lower resolution**, so you know which of the duplicate images are safe to be deleted. You can then either delete them manually, or let difPy delete them for you.

DifPy does not compare images based on their hashes. It compares them based on their tensors i. e. the image content - this allows difPy to not only search for duplicate images, but also for similar images.

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
 "total_dupl_sim_found" : 1024,
 "total_undecodable" : 5}
``` 

## Additional Parameters
DifPy has the following optional parameters:

```python
dif(directory_A, directory_B, recursive=True, similarity="normal", px_size=50, 
    show_progress=True, show_output=False, delete=False, silent_del=False)
```

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

The output of difPy is then written to files and saved in the working directory, where "xxx" is a unique timestamp:

```python
difPy_results_xxx.json
difPy_lower_quality_xxx.txt
difPy_stats_xxx.json
```

-------

For a **detailed usage guide**, please view the official **[difPy Usage Documentation](https://github.com/elisemercury/Duplicate-Image-Finder/wiki/difPy-Usage-Documentation)**.