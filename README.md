### Duplicate Image Finder (difPy)

----

![PyPIv](https://img.shields.io/pypi/v/difPy)
![PyPI status](https://img.shields.io/pypi/status/difPy)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/difPy)
![PyPI - License](https://img.shields.io/pypi/l/difPy)
<img src="https://img.shields.io/badge/dif-Py-blue?style=flat&logo=python&labelColor=white&logoWidth=20.svg/"></a>

*difPy* is a python library that can be used to identify duplicates within a given set of images. In contrast to other
libraries, *difPy* does not use machine learning or other complex techniques to identify duplicates, but simply relies on
the *mean squared error* (*MSE*) when comparing the color codes on each pixel. This method provides a fast but still quite
reliable way to identify duplicate images.

*difPy* also ships the command line tool *difpy* that uses the *difPy library* to implement some common operations like:

* Identifying duplicates within a user specified set of image files
* Deleting duplicate images
* Moving duplicate or unique images to another location


### Installation

----

*difPy* can be installed via [pip](https://pypi.org/project/difPy/):

```console
[user@host ~]$ pip3 install --user difPy
```

Make sure that `~/.local/bin` is part of your `$PATH` environment variable, as the `difpy` executable
script will be placed within this location.


### Description

----

*difPy* searches for images in one or more folders, compares the images it finds and checks whether these are duplicates.
By default, *difPy* outputs it's results as a *JSON* formatted report file that contains information on the identified
duplicates. Other operations may be selected by specifying the corresponding command line switches.

Notice that *difpy's* operation mode slightly differs when specifying one, or multiple paths as arguments. When only one
path was specified, *difpy* searches this path for image files and compares them to each other. Recursive search can be
used to find image files in subfolders too. When specifying multiple paths however, *difpy* only compares images across
these paths. This means that specifying `path1 path2 path3` as arguments compares `path1` to `path2` and `path1` to `path3`.
If you want instead to compare all images to each other, use a shared directory and recursive search instead.

*difPy* does not compare images based on their hashes. It compares them based on their tensors i. e. the image content -
this allows *difPy* to not only search for duplicate images, but also for similar images. The threshold from which on
images should be considered duplicates can be adjusted by the user.


### Usage Examples

----

Comparing `102` images in a single folder:

```console
[user@host ~]$ difpy Sample/
[+] Preparing images in /home/user/Sample
100%|######################################################| 102/102 [00:05<00:00, 18.06it/s]
[+] Comparing 10404 images.
100%|###############################################| 10404/10404 [00:00<00:00, 11430.98it/s]
[+] difpy found 100 duplicates in 0:00:06.565350.
[+] Results written to 2022-12-03 21:41:53.632870.json
```

*difpy* identified `100` duplicates, but performed many compares for it. You can speed up the
procedure by using the `--fast` option. With `--fast` specified, when an image is identified
as duplicate, it is no longer compared to other images. This can lead to missing detection
for some edge cases (image `A` similar to image `B`, `B` similar to `C` but `A` not similar to `C`),
but this should be neglectable for most situations (*difpy* still says it performs `10404` comparisons,
but most of them are skipped):

```console
[user@host ~]$ difpy --fast Sample/
[+] Preparing images in /home/user/Sample
100%|######################################################| 102/102 [00:05<00:00, 17.97it/s]
[+] Comparing 10404 images.
100%|##############################################| 10404/10404 [00:00<00:00, 352920.32it/s]
[+] difpy found 100 duplicates in 0:00:05.711823.
[+] Results written to 2022-12-03 21:46:42.968639.json
```

You may also enable multi-threading to achieve a speedup:

```console
[user@host ~]$ difpy --threads 4 Sample/
[+] Preparing images in /home/user/Sample
100%|######################################################| 102/102 [00:03<00:00, 26.95it/s]
[+] Comparing 10404 images.
100%|################################################| 10404/10404 [00:08<00:00, 1240.73it/s]
[+] difpy found 0 duplicates in 0:00:12.292961.
[+] Results written to 2022-12-03 21:49:31.248227.json
```

Finally, you may want to move duplicate and unique images to different folders:

```console
[user@host ~]$ difpy --fast --move-duplicates Dups/ --move-uniq Uniq Sample/
[+] Preparing images in /home/user/Sample
100%|######################################################| 102/102 [00:05<00:00, 17.78it/s]
[+] Comparing 10404 images.
100%|##############################################| 10404/10404 [00:00<00:00, 291348.12it/s]
[+] difpy found 100 duplicates in 0:00:05.822249.
[+] Results written to 2022-12-03 22:46:03.656267.json
[+] 2 images moved to /home/user/Uniq
[+] 100 images moved to /home/user/Dups
```

## Other Projects

----

* [Web application for filtering duplicates using difPy](https://github.com/prateekralhan/Streamlit-based-Duplicate-Images-Finder)
* [Photosdup - MacOS duplicate image finder](https://github.com/peter-sk/photosdup)
