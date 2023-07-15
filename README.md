# Fast Diff Py

## Motivation 
Why does this project exist? A Quick googling and one finds that there exist plentiful programs and libraries to solve this problem. Well I wanted to write my own implementation and quite frankly, I simply forgot to do the simple thing every programmer should do:  
**Google First - Implement Second** - So here I am with a half functioning implementation of my own accord.   

In its current form 1.7.2023, the project is most suited to run on a device with a decent number of cores and very little RAM. At the moment, the workers don't store all images in RAM but keep reloading them from disk leading to IO bound performance. Considering a Dataset of ~20Gb of images condenses down to at most 100Mb of RAM used, it is a rather stupid endeavor.    
Additionally, since I wanted the algorithm to be able to retain its progress when stopped, I opted to use a Database to handle persistent storage of the results. Once again - stupid. Under the constraint of opperating with less than a 1Gb of RAM this would have made sense, but like this it is simply a very idiotic endeavor.   
The Database simply slows down the progress of the system. Testing with 1000 Images on a 128 Core System with 500Gb RAM, the database interactions ended up becoming the bottleneck with only 32 workers (so at most 1/4 of the system used.)

## So what _does_ this project solve then?

The _only_ thing this implementation is good at, is solving the O(n^2) problem of comparing all to all images. This is something I wasn't able to find implemented by any other fast library. However here we are once again constrained by the database where it would be possible to do everything in RAM and using only python datastructures, so lists, dicts and numpy arrays.    
I leave this project as a cautionary tale, and it might still give some inspiration to someone who wants to use the all to all comparisons instead of finding neat encodings to solve the problem of finding similar images in O(n).


## Methods and Classes:
The Main Class of Concern is `FastDifPy`. It contains the functions to perform the main tasks. 
In Addition, there are two Database Implementations available. `SQLiteDatabase` (default) and `MariaDBDatabase`.

Some Testing I did showed, that for small sets of images (~500) with 16 cores, SQLite outperforms MariaDB by 6% to 50% depending on the configuration and algorithms used.
For larger datasets `MariaDB` _might_ be faster, but I stopped testing since I found the other repos.

### Configuration options:
- `cfg_path`: Path where config is stored
- `update_timeout`: Time interval after which the config on the file system is updated.
- `retain_config`: If the config should be written to the file system.
- `thumbnail_size_x`, `thumbnail_size_y`: Size to reduce the images down to.
- `p_root_dir_a`: Directory to search images in 
- `p_root_dir_b`: Second directory to compare against (if not set, images will be compared against themselves in single directory.)
- `thumb_dir_a`: Thumbnail directory in directory_a (ro)
- `thumb_dir_b`: Thumbnail directory in directory_b (ro)
- `has_dir_b`: If the second directory is populated or not (ro)
- `similarity_threshold`: MSE of two thumbnails below which they are deemed duplicates
- `ignore_names`: list of filenames which are not indexed
- `ignore_paths`: list of paths which are not indexed 
- `enough_images_to_compare`: Set by `index_dirs` function used to short circuit out in the loops if there's not enough to compare
- `supported_file_types`: List of file endings including the '.' of supported file types
- `less_optimized`: If a less optimized version of the second loop should be used (doesn't reuse already loaded image.)
- `retry_limit`: Number of times to search for a new thumbnail name before an error is thrown.
- `verbose`: If the child processes print a lot.
- `state`: Current state of the algorithm. (Indexing done, First loop, Second loop ...)
- `fl_compute_thumbnails`: If the thumbnails should be precomputed and written to disk in the first loop
- `fl_compute_hash`: If file hashes of the images should be computed in the first loop
- `fl_shift_amount`: How much the bits of the image channels RGB should be shifted
- `fl_cpu_proc`: Number of cpu processes to spawn for first loop.
- `fl_inserted_counter`: Number of images already processed.
- `fl_use_workers`: If an enqueue and dequeue worker should be used instead of having the main process handle it. (Requires Thread Safe DB.)
- `database`: Contains the dict created by `create_config_dump` method of databases.
- `retain_db`: If the database config should be stored (maybe undesirable because of password for mariadb)
- `max_queue_size`: Maximum Size of queues created for child processes.
- `sl_matching_hash`: If images with matching file hash should even be compared for MSE
- `sl_has_thumb`: If the thumbnails exist and don't need to be computed.
- `sl_matching_aspect`: If the aspect ratio of the images must match before they are compared with MSE
- `sl_make_diff_plots`: If Plots containing two images which have lower MSE than threshold should be made
- `sl_plot_output_dir`: Directory where plots are stored.
- `sl_gpu_proc`: Number of GPU processes for second loop (requires cupy)
- `sl_cpu_proc`: Number of CPU processes for second loop
- `sl_queue_status`: Contains the progress info for the second loop (should not be touched)
- `sl_base_a`: If the fixed images are coming from directory a (should not be touched)
- `sl_use_workers`: If an enqueue and dequeue worker should be used instead of having the main process handle it. (Requires Thread Safe DB.
- `sl_use_special_b_algo`: If a different algorithm for the fixed images should be used for the second loop if we have a directory b (causes a slight speed up by reusing processes at the end of the loop.)
- `cli_args`: Used for the storage of the command line arguments, used for progress recovery. (should not be touched)
- `ram_cache`: Preload all images into RAM after they have been shrunken down. On most modern systems with ~16Gb of RAM, and 64x64 thumbnail size and < 500k images should fit into ram. This speeds up the second loop. 
- `max_allowed_ram_usage` Maximum amount of RAM usage before the library automatically chooses to switch to no ram cache and sql db. (Currently not implemented.)

### Example
```python
db = FastDifPy(directory_a="/path/to/folder")
db.index_the_dirs()
db.estimate_disk_usage()

db.first_loop_iteration(compute_hash=True, amount=4, cpu_proc=16)

db.second_loop_iteration(only_matching_aspect=False,
                         make_diff_plots=False,
                         diff_location="/path/to/plot/folder",
                         similarity_threshold=200.0,
                         cpu_proc=16)

db.print_preprocessing_errors()

clusters, low_quality = db.get_duplicates()
db.clean_up()
```

The first loop computes the thumbnails and compresses the images, the second loop performs the all to all comparison. 
To mimic the plots generated by the [Duplicate-Image-Finder](https://github.com/elisemercury/Duplicate-Image-Finder), plots can be generated and are stored in the provided directory. This seemed like a more useful solution than opening potentially thousands of plots.

An additional capability of this project is the config. Everything in db.config is stored periodically to Disk and allows for the recovery of an interrupted process. At the time, there's no implementation of the recovery function (also since it might depend on the use case for a given user). But, provided no custom config path is used, the `FastDiffPyConfig` can be instantiated and from its attributes the current progress state recovered.   
The config simply needs to be set as an attribute and then the database reconnected. Progress recovery is not fully implemented however there are the basic tools for it.


## Further TODOs:
- Implement RAM Only version with progress saved periodically to disk
- Optimize SQL Queries
- Add better handling for ungraceful shutdown of loops in the database
- Add functionality to extract hash based duplicates
- Add arbitrary hash function support
- Add arbitrary all to all comparison function support.



### Similar Projects:
- [Duplicate-Image-Finder](https://github.com/elisemercury/Duplicate-Image-Finder) (the project this is based on)
- [imagededup](https://github.com/idealo/imagededup)