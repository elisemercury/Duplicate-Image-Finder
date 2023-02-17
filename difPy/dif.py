"""
difPy - Python package for finding duplicate or similar images within folders 
https://github.com/elisemercury/Duplicate-Image-Finder
"""
import skimage.color
from glob import glob
import matplotlib.pyplot as plt
import uuid
import numpy as np
import cv2
import os
import time
from pathlib import Path
import argparse
import json
import warnings
warnings.filterwarnings('ignore')

class dif:
    # Class that runs the difPy algortihm on file like objects

    def __init__(self, *directory, fast_search=True, recursive=True, similarity="normal", px_size=50, show_progress=True, show_output=False, delete=False, silent_del=False):
        print("difPy process initializing...", end="\r")
        self.directory = _validate._directory_exist(directory)
        _validate._directory_unique(self.directory)
        self.recursive = _validate._recursive(recursive)
        self.similarity = _validate._similarity(similarity)
        self.fast_search = _validate._fast_search(fast_search, self.similarity)
        self.px_size = _validate._px_size(px_size)
        self.delete, self.silent_del = _validate._delete(delete, silent_del)
        self.show_output = _validate._show_output(show_output)
        self.show_progress = _validate._show_progress(show_progress)

        start_time = time.time()  # TODO check if can be put into run
        self.result, self.lower_quality, total_count, match_count, invalid_files = dif._run(self)
        end_time = time.time()

        time_elapsed = np.round(end_time - start_time, 4)
        self.stats = dif._generate_stats(self, start_time=time.localtime(start_time), end_time=time.localtime(end_time), time_elapsed=time_elapsed, 
                                         total_searched=total_count, total_matches=match_count, total_invalid=len(invalid_files))

        print(f"Found {match_count} pair(s) of duplicate/similar image(s) in {time_elapsed} seconds.")

        if delete:
            # optional: delete lower_quality images
            if len(self.lower_quality) != 0:
                _help._delete_imgs(set(self.lower_quality), silent_del=self.silent_del)
    
    def _run(self):
        # Function that runs the difPy algortihm
        for count, dir in enumerate(self.directory):
            if count == 0:
                directory_files = _help._list_all_files(dir, self.recursive)
                id_by_location = _compute._id_by_location(directory_files, id_by_location=None)
            else:
                if len(self.directory) >= 2:
                    if not dir in directory_files:
                        directory_files = _help._list_all_files(dir, self.recursive)
                        id_by_location = _compute._id_by_location(directory_files, id_by_location=id_by_location)
                else:
                    break
        imgs_matrices, invalid_files = _compute._imgs_matrices(id_by_location, self.px_size, self.show_progress)
        result, exlude_from_search, total_count, match_count = _search._matches(imgs_matrices, id_by_location, self.similarity, self.show_output, self.show_progress, self.fast_search)
        lower_quality = _search._lower_quality(result)
        return result, lower_quality, total_count, match_count, invalid_files

    def _generate_stats(self, start_time, end_time, time_elapsed, total_searched, total_matches, total_invalid):
        # Function that generates a dictionary for statistics around the completed difPy process
        stats = {"directory": self.directory,
                 "duration": {"start_date": time.strftime("%Y-%m-%d", start_time),
                              "start_time": time.strftime("%H:%M:%S", start_time),
                              "end_date": time.strftime("%Y-%m-%d", end_time),
                              "end_time": time.strftime("%H:%M:%S", end_time),
                              "seconds_elapsed": time_elapsed},
                 "fast_search": self.fast_search,
                 "recursive": self.recursive,
                 "match_mse": self.similarity,
                 "files_searched": total_searched,
                 "matches_found": total_matches,
                 "invalid_files": total_invalid}
        return stats

class _validate:

    def _directory_exist(directory):
        # Function that _validates the input directories
        for dir in directory:
            dir = Path(dir)
            if not os.path.isdir(dir):
                raise FileNotFoundError(f'Directory "{str(dir)}" does not exist')
        return directory

    def _directory_unique(directory):
        if len(set(directory)) != len(directory):
            raise ValueError('Invalid directory parameters: an attempt to compare a directory with itself.')

    def _fast_search(fast_search, similarity):
        # Function that _validates the 'show_output' input parameter
        if not isinstance(fast_search, bool):
            raise Exception('Invalid value for "fast_search" parameter.')
        if similarity > 200:
            fast_search = False
        return fast_search

    def _show_output(show_output):
        # Function that _validates the 'show_output' input parameter
        if not isinstance(show_output, bool):
            raise Exception('Invalid value for "show_output" parameter.')
        return show_output

    def _show_progress(show_progress):
        # Function that _validates the 'show_progress' input parameter
        if not isinstance(show_progress, bool):
            raise Exception('Invalid value for "show_progress" parameter.')
        return show_progress 
    
    def _recursive(recursive):
        # Function that _validates the 'recursive' input parameter
        if not isinstance(recursive, bool):
            raise Exception('Invalid value for "recursive" parameter.')
        return recursive
    
    def _similarity(similarity):
        # Function that _validates the 'similarity' input parameter
        if similarity not in ["low", "normal", "high"]: 
            try:
                similarity = float(similarity)
                if similarity < 0:
                  raise Exception('Invalid value for "similarity" parameter.')  
                else:
                    return similarity
            except:
                raise Exception('Invalid value for "similarity" parameter.')
        else: 
            if similarity == "low":
                similarity = 1000
            # search for exact duplicate images, extremly sensitive, MSE < 0.1
            elif similarity == "high":
                similarity = 0.1
            # normal, search for duplicates, recommended, MSE < 200
            else:
                similarity = 200
            return similarity
    
    def _px_size(px_size):
        # Function that _validates the 'px_size' input parameter   
        if px_size < 10 or px_size > 5000:
            raise Exception('Invalid value for "px_size" parameter.')
        return px_size
    
    def _delete(delete, silent_del):
        # Function that _validates the 'delete' and the 'silent_del' input parameter
        if not isinstance(delete, bool):
            raise Exception('Invalid value for "delete" parameter.')
        if not isinstance(silent_del, bool):
            raise Exception('Invalid value for "silent_del" parameter.')
        return delete, silent_del

class _compute:

    def _id_by_location(directory_files, id_by_location):
        # Function that creates a collection of 'ids : image_location'
        img_ids = []
        for i in range(0, len(directory_files)):
            img_id = uuid.uuid4().int
            while img_id in img_ids:
                img_id = uuid.uuid4().int
            img_ids.append(img_id)

        if id_by_location == None:
            id_by_location = dict(zip(img_ids, directory_files)) 
        else:
            id_by_location.update(dict(zip(img_ids, directory_files)))
        return id_by_location

    def _imgs_matrices(id_by_location, px_size, show_progress=False):
        # Function that creates a collection of {id: matrix} for each image found
        count = 0
        total_count = len(id_by_location)
        imgs_matrices = {}
        invalid_files = []
        try:
            for id, file in id_by_location.items():
                if show_progress:
                    _help._show_progress(count, total_count, task='preparing files')
                if os.path.isdir(file):
                    count += 1
                else:
                    try:
                        img = cv2.imdecode(np.fromfile(file, dtype=np.uint8), cv2.IMREAD_COLOR)
                        if type(img) == np.ndarray:
                            img = img[..., 0:3]
                            img = cv2.resize(img, dsize=(px_size, px_size), interpolation=cv2.INTER_CUBIC)
                            if len(img.shape) == 2:
                                img = skimage.color.gray2rgb(img)
                            imgs_matrices[id] = img
                    except:
                        invalid_files.append(id)
                    finally:
                        count += 1
            for id in invalid_files:
                id_by_location.pop(id, None)
            return imgs_matrices, invalid_files
        except KeyboardInterrupt:
            raise KeyboardInterrupt

    def _mse(img_A, img_B):
        # Function that calulates the mean squared error (mse) between two image matrices
        mse = np.sum((img_A.astype("float") - img_B.astype("float")) ** 2)
        mse /= float(img_A.shape[0] * img_A.shape[1])
        return mse

class _search:

    def _matches(imgs_matrices, id_by_location, similarity, show_output, show_progress, fast_search):
        # Function that searches the images on duplicates/similarity matches
        progress_count = 0
        match_count = 0
        total_count = len(imgs_matrices)
        exclude_from_search = []
        result = {}

        for number_A, (id_A, matrix_A) in enumerate(imgs_matrices.items()):
            if show_progress:
                _help._show_progress(progress_count, total_count, task='comparing images')
            if id_A in exclude_from_search:
                progress_count += 1
            else:
                for number_B, (id_B, matrix_B) in enumerate(imgs_matrices.items()):
                    if number_B > number_A:
                        rotations = 0
                        while rotations <= 3:
                            if rotations != 0:
                                matrix_B = _help._rotate_img(matrix_B)
                            mse = _compute._mse(matrix_A, matrix_B)
                            if mse < similarity:
                                match_count += 1
                                if id_A not in result.keys():
                                    result[id_A] = {'location': str(Path(id_by_location[id_A])),
                                                    'matches': {id_B: {'location': str(Path(id_by_location[id_B])),
                                                                       'mse': mse }}}
                                else:
                                    result[id_A]['matches'][id_B] = {'location': str(Path(id_by_location[id_B])),
                                                                     'mse': mse }
                                if show_output:
                                    _help._show_img_figs(matrix_A, matrix_B, mse)
                                    _help._show_file_info(id_by_location[id_A], id_by_location[id_B])
                                if fast_search == True:
                                    exclude_from_search.append(id_B)
                                rotations = 4
                            else:
                                rotations += 1
                progress_count += 1
        return result, exclude_from_search, total_count, match_count

    def _lower_quality(result):
        # Function that creates a list of all image matches that have the lowest quality within the match group
        lower_quality = []
        for id, results in result.items():
            match_group = []
            match_group.append(result[id]['location'])
            for match_id in result[id]['matches']:
                match_group.append(result[id]['matches'][match_id]['location'])
            sort_by_size = _help._check_img_quality(match_group)
            lower_quality = lower_quality + sort_by_size[1:]
        return lower_quality

class _help:

    def _list_all_files(directory, recursive):
        # Function that creates a list of all files in the directory
        directory_files = list(glob(str(directory) + '/**', recursive=recursive))
        return directory_files

    def _show_img_figs(img_A, img_B, err):
        # Function that plots two compared image files and their mse
        fig = plt.figure()
        plt.suptitle("MSE: %.2f" % (err))
        # plot first image
        ax = fig.add_subplot(1, 2, 1)
        plt.imshow(img_A, cmap=plt.cm.gray)
        plt.axis("off")
        # plot second image
        ax = fig.add_subplot(1, 2, 2)
        plt.imshow(img_B, cmap=plt.cm.gray)
        plt.axis("off")
        # show the images
        plt.show()

    def _show_file_info(img_A, img_B):
        # Function for printing filename info of plotted image files
        img_A = "..." + str(img_A)[-45:]
        img_B = "..." + str(img_B)[-45:]
        print(f"""Duplicate files:\n{img_A} and \n{img_B}\n""")

    def _rotate_img(img):
        # Function for rotating an image matrix by a 90 degree angle
        img = np.rot90(img, k=1, axes=(0, 1))
        return img

    def _check_img_quality(img_list):
        # Function for sorting a list of images based on their file sizes
        imgs_sizes = []
        for img in img_list:
            img_size = (os.stat(str(img)).st_size, img)
            imgs_sizes.append(img_size)
        sort_by_size = [file for size, file in sorted(imgs_sizes, reverse=True)]
        return sort_by_size

    def _show_progress(count, total_count, task='processing images'):
        # Function that displays a progress bar during the search
        if count+1 == total_count:
            print(f"difPy {task}: [{count}/{total_count}] [{count/total_count:.0%}]", end="\r")
            print(f"difPy {task}: [{count+1}/{total_count}] [{(count+1)/total_count:.0%}]")          
        else:
            print(f"difPy {task}: [{count}/{total_count}] [{count/total_count:.0%}]", end="\r")

    def _delete_imgs(lower_quality_set, silent_del=False):
        # Function for deleting the lower quality images that were found after the search
        delete_count = 0
        if not silent_del:
            usr = input("Are you sure you want to delete all lower quality matched images? \n! This cannot be undone. (y/n)")
            if str(usr) == "y":
                delete_count += 1
                for file in lower_quality_set:
                    print("\nDeletion in progress...", end="\r")
                    try:
                        os.remove(file)
                        print("Deleted file:", file, end="\r")
                        delete_count += 1
                    except:
                        print("Could not delete file:", file, end="\r")       
            else:
                print("Image deletion canceled.")
                return
        else:
            delete_count += 1
            for file in lower_quality_set:
                print("\nDeletion in progress...", end="\r")
                try:
                    os.remove(file)
                    print("Deleted file:", file, end="\r")
                    delete_count += 1
                except:
                    print("Could not delete file:", file, end="\r")
        print(f"\n***\nDeleted {delete_count} image file(s).")

def _type_str_int(x):
    # TODO check if can be added to help class
    # Helper function to make the CLI accept int and str type inputs for the similarity parameter
    try:
        return int(x)
    except:
        return x

if __name__ == "__main__":
    # Parameters for when launching difPy via CLI
    parser = argparse.ArgumentParser(description='Find duplicate or similar images on your computer with difPy - https://github.com/elisemercury/Duplicate-Image-Finder')
    parser.add_argument("-D", "--directory", type=str, nargs='+', help='Directory to search for images.', required=True)
    parser.add_argument("-Z", "--output_directory", type=str, help='Output directory for the difPy result files. Default is working dir.', required=False, default=None)
    parser.add_argument("-f", "--fast_search", type=str, help='Choose whether difPy should use its fast search algorithm.', required=False, default=None)
    parser.add_argument("-r", "--recursive", type=bool, help='Scan subfolders for duplicate images', required=False, choices=[True, False], default=True)
    parser.add_argument("-s", "--similarity", type=_type_str_int, help='Similarity grade.', required=False, default='normal')
    parser.add_argument("-px", "--px_size", type=int, help='Compression size of images in pixels.', required=False, default=50)
    parser.add_argument("-p", "--show_progress", type=bool, help='Shows the real-time progress of difPy.', required=False, choices=[True, False], default=True)
    parser.add_argument("-o", "--show_output", type=bool, help='Shows the comapred images in real-time.', required=False, choices=[True, False], default=False)
    parser.add_argument("-d", "--delete", type=bool, help='Deletes all duplicate images with lower quality.', required=False, choices=[True, False], default=False)
    parser.add_argument("-sd", "--silent_del", type=bool, help='Supresses the user confirmation when deleting images.', required=False, choices=[True, False], default=False)
    args = parser.parse_args()

    # initialize difPy
    search = dif(*args.directory, fast_search=args.fast_search,
                recursive=args.recursive, similarity=args.similarity, px_size=args.px_size, 
                show_output=args.show_output, show_progress=args.show_progress, 
                delete=args.delete, silent_del=args.silent_del)

    # create filenames for the output files
    timestamp =str(time.time()).replace(".", "_")
    result_file = f"difPy_results_{timestamp}.json"
    lq_file = f"difPy_lower_quality_{timestamp}.csv"
    stats_file = f"difPy_stats_{timestamp}.json"

    if args.output_directory != None:
        dir = args.output_directory
    else:
        dir = os.getcwd()

    if not os.path.exists(dir):
        os.makedirs(dir)

    with open(os.path.join(dir, result_file), "w") as file:
        json.dump(search.result, file)

    with open(os.path.join(dir, lq_file), "w") as file:
        for element in search.lower_quality:
            file.write(f"{element},")

    with open(os.path.join(dir, stats_file), "w") as file:
        json.dump(search.stats, file)

    print(f"""\nSaved difPy results into folder '{dir}' and filenames:\n{result_file} \n{lq_file} \n{stats_file}""")