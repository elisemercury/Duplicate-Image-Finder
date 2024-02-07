'''
difPy - Python package for finding duplicate and similar images.
2024 Elise Landman
https://github.com/elisemercury/Duplicate-Image-Finder
'''
from glob import glob
from multiprocessing import Pool
from uuid import uuid4
import numpy as np
from PIL import Image
from distutils.util import strtobool
import os
from datetime import datetime
from pathlib import Path
import argparse
import json
import warnings
from itertools import combinations
from collections import defaultdict

class search:
    '''
    A class used to search for matches in a difPy image repository
    '''
    def __init__(self, difpy_obj, similarity='duplicates', rotate=True, lazy=True, show_progress=True, logs=True, processes=None, maxtasksperchild=None, chunksize=1000):
        '''
        Parameters
        ----------
        difPy_obj : difPy.dif.build
            difPy object containing the build image repository
        similarity : 'duplicates', 'similar', float (optional)
            Image comparison similarity threshold (mse) (default is 'duplicates', 0)
        rotate : bool (optional)
            Rotates images on comparison (default is True)
        lazy : bool (optional)
            Compares image dimensions. If not equal, images are automatically classified as not similar/duplicates (default is True)
        show_progress : bool (optional)
            Show the difPy progress bar in console (default is True)
        logs : bool (optional)
            Collect stats on the difPy process (default is True) ## TODO add new params
        '''
        # Validate input parameters
        self.__difpy_obj = difpy_obj
        self.__similarity = _validate_param._similarity(similarity)
        self.__rotate = _validate_param._rotate(rotate)
        self.__lazy = _validate_param._lazy(lazy)
        self.__show_progress = _validate_param._show_progress(show_progress)
        self.__processes = _validate_param._processes(processes)
        self.__maxtasksperchild = _validate_param._maxtasksperchild(maxtasksperchild)
        self.__chunksize = _validate_param._chunksize(chunksize)
        self.__in_folder = self.__difpy_obj.stats['process']['build']['parameters']['in_folder']

        print("Initializing search...", end='\r')
        self.result, self.lower_quality, self.stats = self._main()
        return

    def _main(self):
        # Function that runs the search workflow
        start_time = datetime.now()
        
        if self.__in_folder:
            # Search directories separately
            result = self._search_infolder()
            result = self._format_result_infolder(result)
            lower_quality, duplicate_count, similar_count = self._search_metadata_infolder(result)
        else:
            # Search union of all directories
            result = self._search_union()
            result = self._format_result_union(result)
            # Compare image qualities and computes process metadata
            lower_quality, duplicate_count, similar_count = self._search_metadata_union(result)

        end_time = datetime.now()

        # Generate process stats
        stats = _generate_stats().search(build_stats=self.__difpy_obj.stats, start_time=start_time, end_time=end_time, similarity = self.__similarity, rotate=self.__rotate, lazy=self.__lazy, processes=self.__processes, maxtasksperchild=self.__maxtasksperchild, files_searched=len(self.__difpy_obj._tensor_dictionary), duplicate_count=duplicate_count, similar_count=similar_count)

        return result, lower_quality, stats
    
    def _format_result_union(self, result):
        # Helper function that replaces the image IDs in the result dictionary by their filename
        updated_result = dict()
        for key, value in result.items():
            # Replace the key with the corresponding value from dict2
            new_key = self.__difpy_obj._filename_dictionary.get(key, key)
            # Replace the values in the inner lists with corresponding values from dict2
            new_value = [[self.__difpy_obj._filename_dictionary.get(inner[0], inner[0]), inner[1]] for inner in value]
            # Update the new dictionary
            updated_result[new_key] = new_value
        return updated_result

    def _format_result_infolder(self, result):
        # Helper function that replaces the image IDs in the result dictionary by their filename
        updated_result = dict()
        for group_id in result.keys():
            for key, value in result[group_id].items():
                # Replace the key with the corresponding value from dict2
                new_key = self.__difpy_obj._filename_dictionary.get(key, key)
                # Replace the values in the inner lists with corresponding values from dict2
                new_value = [[self.__difpy_obj._filename_dictionary.get(inner[0], inner[0]), inner[1]] for inner in value]
                # Update the new dictionary
                if group_id not in updated_result.keys():
                    updated_result.update({group_id : {}})
                updated_result[group_id][new_key] = new_value
        return updated_result


    def _search_union(self):
        # Search union of all directories
        result_raw = list()
        result_count = 0
        id_combinations = list(combinations(list(self.__difpy_obj._tensor_dictionary.keys()), 2))
        total = len(id_combinations)
        self.__count = 0

        with Pool(processes=5) as pool:
            output = pool.map(self._find_matches, id_combinations)
        for i in output:
            if i:
                result_raw, result_count = self._add_to_result(result_raw, i, result_count, total)
        self.__count += 1       
        if self.__show_progress:
            _help_progress._show_bar(self.__count, 1, task=f'searching files')

        if self.__in_folder:
            pass
        else:
            result = self._group_result_union(result_raw)

        return result

    def _search_metadata_union(self, result):
        # Helper function that compares image qualities and computes process metadata
        duplicate_count, similar_count = 0, 0
        lower_quality = np.array([])
        if self.__similarity == 0:
            for img in result.keys():
                match_group = [img]
                duplicate_count += len(result[img])
                for img_matches in result[img]:
                    # compare image quality
                    match_group.append(img_matches[0])
                match_group = self._sort_imgs_by_size(match_group)
                lower_quality = np.concatenate((lower_quality, match_group[1:]), axis = None)
        else:
            for img in result.keys():
                match_group = [img]
                for img_matches in result[img]:
                    # create list of all imgs in group
                    match_group.append(img_matches[0])
                    # count duplicate/similar
                    if img_matches[1] == 0:
                        duplicate_count += 1
                    else:
                        similar_count += 1    
                # compare img quality
                match_group = self._sort_imgs_by_size(match_group)
                lower_quality = np.concatenate((lower_quality, match_group[1:]), axis = None)
        
        lower_quality = {'lower_quality': list(set(lower_quality))}
        return lower_quality, duplicate_count, similar_count    

    def _search_metadata_infolder(self, result):
        # Helper function that compares image qualities and computes process metadata
        duplicate_count, similar_count = 0, 0
        lower_quality = np.array([])
        if self.__similarity == 0:
            for group_id in result.keys():
                for img in result[group_id].keys():
                    match_group = [img]
                    duplicate_count += len(result[group_id][img])
                    for img_matches in result[group_id][img]:
                        # compare image quality
                        match_group.append(img_matches[0])
                    match_group = self._sort_imgs_by_size(match_group)
                    lower_quality = np.concatenate((lower_quality, match_group[1:]), axis = None)
        else:
            for group_id in result.keys():
                for img in result[group_id].keys():
                    match_group = [img]
                    for img_matches in result[group_id][img]:
                        # create list of all imgs in group
                        match_group.append(img_matches[0])
                        # count duplicate/similar
                        if img_matches[1] == 0:
                            duplicate_count += 1
                        else:
                            similar_count += 1    
                    # compare img quality
                    match_group = self._sort_imgs_by_size(match_group)
                    lower_quality = np.concatenate((lower_quality, match_group[1:]), axis = None)
            
        lower_quality = {'lower_quality': list(set(lower_quality))}
        return lower_quality, duplicate_count, similar_count  

    def _search_infolder(self):
        # Search directories separately
        result_raw = list()
        result_count = 0
        grouped_img_ids = [img_ids for group_id, img_ids in self.__difpy_obj._group_to_id_dictionary.items()]
        total = len(self.__difpy_obj._group_to_id_dictionary.items())
        self.__count = 0

        with Pool(processes=5) as pool:
            for ids in grouped_img_ids:
                id_combinations = list(combinations(ids, 2))
                output = pool.map(self._find_matches, id_combinations)
                for i in output:
                    if i:
                        result_raw, result_count = self._add_to_result(result_raw, i, result_count, total)
                self.__count += 1        
                if self.__show_progress:
                    _help_progress._show_bar(self.__count, 1, task=f'searching files')

        #print(result_raw)
        result = self._group_result_infolder(result_raw)
        print(result)
        return result

    def _generate_stats(self, **kwargs):
        # Function that generates search stats
        stats = self.__difpy_obj._stats
        seconds_elapsed = np.round((kwargs['end_time'] - kwargs['start_time']).total_seconds(), 4)
        stats['process'].update({'search' : {}})
        stats['process']['search'].update({'duration' : {'start': kwargs['start_time'].isoformat(),
                                                         'end' : kwargs['end_time'].isoformat(),
                                                         'seconds_elapsed' : seconds_elapsed 
                                                        }})
        stats['process']['search'].update({'parameters' : {'similarity_mse': self.__similarity,
                                                           'rotate' : self.__rotate,
                                                           'processes' : self.__processes,
                                                           'maxtasksperchild' : self.__maxtasksperchild                                                           
                                                          }})
        stats['process']['search'].update({'files_searched' : len(self.__difpy_obj._tensor_dictionary)})
        
        stats['process']['search'].update({'matches_found' : {'duplicates': kwargs['duplicate_count'],
                                                              'similar' : kwargs['similar_count']
                                                             }})        
        return stats

    def _sort_imgs_by_size(self, img_list):
        # Function for sorting a list of images based on their file sizes
        imgs_sizes = []
        for img in img_list:
            img_size = (os.stat(str(img)).st_size, img)
            imgs_sizes.append(img_size)
        sort_by_size = [file for size, file in sorted(imgs_sizes, reverse=True)]
        return sort_by_size

    def _find_matches(self, ids):
        id_A = ids[0]
        id_B = ids[1]
        tensor_A = self.__difpy_obj._tensor_dictionary[id_A]
        tensor_B = self.__difpy_obj._tensor_dictionary[id_B] 
        tensor_shape_A = self.__difpy_obj._id_to_shape_dictionary[id_A]
        tensor_shape_B = self.__difpy_obj._id_to_shape_dictionary[id_B]

        compare = _compare_imgs(tensor_shape_A, tensor_shape_B, tensor_A, tensor_B)
        if self.__lazy:
            if compare._compare_shape():
                if compare._check_equality():
                    return (id_A, id_B, 0.0) # mse will always be 0
                else:
                    mse = compare._compute_mse(rotate=self.__rotate)
                    if mse <= self.__similarity:
                        return (id_A, id_B, mse)
            else:
                return False
        else:
            if compare._check_equality():
                return (id_A, id_B, 0.0) # mse will always be 0
            else:
                mse = compare._compute_mse(rotate=self.__rotate)
                if mse <= self.__similarity:
                    return (id_A, id_B, mse)            

    def _add_to_result(self, result_raw, output, result_count, total):
        result_raw.append(output)

        return result_raw, result_count

    def _group_result_union(self, tuple_list):
        result = defaultdict(list)
        already_added = set()
        for k, *v in tuple_list:
            if v[0] not in already_added:
                result[k].append(v)
                already_added.add(v[0])

        result = dict(result)
        del already_added
        return result

    def _group_result_infolder(self, tuple_list):
        result = defaultdict(list)
        already_added = set()
        for k, *v in tuple_list:
            k_group = self.__difpy_obj._id_to_group_dictionary[k]
            if k_group not in result:
                result.update({k_group:{}})
            if v[0] not in already_added:
                result[k_group].update({k : []})
                result[k_group][k].append(v)
                #result[k].append(v)
                already_added.add(v[0])

        result = dict(result)
        del already_added
        return result

class _generate_stats:
    def __init__(self):
        self.stats = dict()

    def build(self, **kwargs):
        seconds_elapsed = np.round((kwargs['end_time'] - kwargs['start_time']).total_seconds(), 4)
        invalid_files = kwargs['invalid_files']
        for file in kwargs['skipped_files']:
            invalid_files.update({str(Path(file)) : 'FileSkipped: file type was skipped.'})
        self.stats.update({'directory' : kwargs['directory']})
        self.stats.update({'process' : {'build': {}}})   
        self.stats['process']['build'].update({'duration' : {'start': kwargs['start_time'].isoformat(),
                                                        'end' : kwargs['end_time'].isoformat(),
                                                        'seconds_elapsed' : seconds_elapsed
                                                       }})
        self.stats['process']['build'].update({'parameters': {'recursive' : kwargs['recursive'],
                                                         'in_folder' : kwargs['in_folder'],
                                                         'limit_extensions' : kwargs['limit_extensions'],
                                                         'px_size' : kwargs['px_size'],
                                                         'processes' : kwargs['processes'],
                                                         'maxtasksperchild' : kwargs['maxtasksperchild']
                                                        }})
        
        self.stats.update({'invalid_files': {'count' : len(invalid_files),
                                        'logs' : invalid_files}})
        
        return self.stats

    def search (self, **kwargs):
        # Function that generates search stats
        stats = kwargs['build_stats']
        seconds_elapsed = np.round((kwargs['end_time'] - kwargs['start_time']).total_seconds(), 4)
        stats['process'].update({'search' : {}})
        stats['process']['search'].update({'duration' : {'start': kwargs['start_time'].isoformat(),
                                                         'end' : kwargs['end_time'].isoformat(),
                                                         'seconds_elapsed' : seconds_elapsed 
                                                        }})
        stats['process']['search'].update({'parameters' : {'similarity_mse': kwargs['similarity'],
                                                           'rotate' : kwargs['rotate'],
                                                           'lazy' : kwargs['lazy'],
                                                           'processes' : kwargs['processes'],
                                                           'maxtasksperchild' : kwargs['maxtasksperchild']                                                           
                                                          }})
        stats['process']['search'].update({'files_searched' : kwargs['files_searched']})
        
        stats['process']['search'].update({'matches_found' : {'duplicates': kwargs['duplicate_count'],
                                                              'similar' : kwargs['similar_count']
                                                             }})        
        return stats


class _compare_imgs:
    def __init__(self, tensor_shape_A, tensor_shape_B, tensor_A, tensor_B):
        self.tensor_shape_A = tensor_shape_A
        self.tensor_shape_B = tensor_shape_B
        self.tensor_A = tensor_A
        self.tensor_B = tensor_B

    def _compute_mse(self, rotate=True):
        if rotate:
            mse_list = []
            for rot in range(0, 3):
                if rot == 0:
                    mse = np.square(np.subtract(self.tensor_A, self.tensor_B)).mean()
                    mse_list.append(mse)
                elif rot <= 3:
                    self.tensor_B = np.rot90(self.tensor_B)
                    mse = np.square(np.subtract(self.tensor_A, self.tensor_B)).mean()
                    mse_list.append(mse)
            min_mse = min(mse_list)  
            return min_mse
        else:
            mse = np.square(np.subtract(self.tensor_A, self.tensor_B)).mean()
            return mse

    def _compare_shape(self):
        if (self.tensor_shape_A==self.tensor_shape_B):
            return True
        else:
            return False

    def _check_equality(self):
        if (self.tensor_A==self.tensor_B).all():
            return True
        else:
            return False

    

############################################################


class build:
    '''
    A class used to initialize difPy and build its image repository
    '''
    def __init__(self, *directory, recursive=True, in_folder=False, limit_extensions=True, px_size=50, show_progress=True, processes=None, maxtasksperchild=None):
        '''
        Parameters
        ----------
        directory : str, list
            Paths of the directories or the files to be searched
        recursive : bool (optional)
            Search recursively within the directories (default is True)
        in_folder : bool (optional)
            If False, searches for matches in the union of directories (default is False)
            If True, searches for matches only among subdirectories
        limit_extensions : bool (optional)
            Limit search to known image file extensions (default is True)
        px_size : int (optional)
            Image compression size in pixels (default is 50)
        show_progress : bool (optional)
            Show the difPy progress bar in console (default is True)
        processes : int (optional)
            Maximum number of simultaneous processes when multiprocessing.
        maxtasksperchild : int (optional)
            Maximum number of tasks completed by each child process when multiprocessing.
        '''
        # Validate input parameters
        self.__directory = _validate_param._directory(directory)
        self.__recursive = _validate_param._recursive(recursive)
        self.__in_folder = _validate_param._in_folder(in_folder, recursive)
        self.__limit_extensions = _validate_param._limit_extensions(limit_extensions)
        self.__px_size = _validate_param._px_size(px_size)
        self.__show_progress = _validate_param._show_progress(show_progress)
        self.__processes = _validate_param._processes(processes)
        self.__maxtasksperchild = _validate_param._maxtasksperchild(maxtasksperchild)

        self._tensor_dictionary, self._id_to_shape_dictionary, self._filename_dictionary, self._id_to_group_dictionary, self._group_to_id_dictionary, self._invalid_files, self.stats = self._main()

        #print(self._group_to_id_dictionary)
        return

    def _main(self):
        # Function that runs the build workflow
        if self.__show_progress:
            count = 0
            total_count = 3
            _help_progress._show_bar(count, total_count, task='preparing files')

        start_time = datetime.now()
        valid_files, skipped_files = self._get_files()
        if self.__show_progress:
            count += 1
            _help_progress._show_bar(count, total_count, task='preparing files')
        
        tensor_dictionary, id_to_shape_dictionary, filename_dictionary, id_to_group_dictionary, group_to_id_dictionary, invalid_files = self._build_image_dictionaries(valid_files)    

        end_time = datetime.now()
        if self.__show_progress:
            count += 1
            _help_progress._show_bar(count, total_count, task='preparing files')
        

        stats = _generate_stats().build(start_time=start_time, end_time=end_time, invalid_files=invalid_files, skipped_files=skipped_files, directory=self.__directory, recursive=self.__recursive, in_folder=self.__in_folder, limit_extensions=self.__limit_extensions, px_size=self.__px_size, processes=self.__processes, maxtasksperchild=self.__maxtasksperchild)

        #stats = self._generate_stats(start_time=start_time, end_time=end_time, #invalid_files=invalid_files, skipped_files=skipped_files)
        if self.__show_progress:
            count += 1
            _help_progress._show_bar(count, total_count, task='preparing files')

        return tensor_dictionary, id_to_shape_dictionary, filename_dictionary, id_to_group_dictionary, group_to_id_dictionary, invalid_files, stats

    def _get_files(self):
        # Function that searches for files in the input directories
        valid_files_all = []
        skipped_files_all = np.array([])
        if self.__in_folder:
            # Search directories separately
            directories = []
            for dir in self.__directory:
                if os.path.isdir(dir):
                    directories += glob(str(dir) + '/**/', recursive=self.__recursive)
                elif os.path.isfile(dir):
                    files.append(dir)
            for dir in directories:
                files = glob(str(dir) + '/*', recursive=self.__recursive)
                valid_files, skip_files = self._validate_files(files)
                valid_files_all.append(valid_files)
                if len(skip_files) > 0:
                    skipped_files_all = np.concatenate((skipped_files_all, skip_files), axis=None)

        else:
            # Search union of all directories
            for dir in self.__directory:
                if os.path.isdir(dir):
                    files = glob(str(dir) + '/**', recursive=self.__recursive)
                elif os.path.isfile(dir):
                    files = (dir, )
                valid_files, skip_files = self._validate_files(files)
                valid_files_all = np.concatenate((valid_files_all, valid_files), axis=None)
                if len(skip_files) > 0:
                    skipped_files_all = np.concatenate((skipped_files_all, skip_files), axis=None)
        return valid_files_all, skipped_files_all

    def _validate_files(self, directory): 
        # Function that validates a file's filetype
        valid_files = np.array([os.path.normpath(file) for file in directory if not os.path.isdir(file)])        
        if self.__limit_extensions:
            valid_files, skip_files = self._filter_extensions(valid_files)
        else:
            warnings.warn('"limit_extensions" is set to False: difPy accuracy is not guaranteed.')
            skip_files = []
        return valid_files, skip_files

    def _filter_extensions(self, directory_files):
        # Function that filters by files with a specific filetype
        valid_extensions = np.array(['apng', 'bw', 'cdf', 'cur', 'dcx', 'dds', 'dib', 'emf', 'eps', 'fli', 'flc', 'fpx', 'ftex', 'fits', 'gd', 'gd2', 'gif', 'gbr', 'icb', 'icns', 'iim', 'ico', 'im', 'imt', 'j2k', 'jfif', 'jfi', 'jif', 'jp2', 'jpe', 'jpeg', 'jpg', 'jpm', 'jpf', 'jpx', 'jpeg', 'mic', 'mpo', 'msp', 'nc', 'pbm', 'pcd', 'pcx', 'pgm', 'png', 'ppm', 'psd', 'pixar', 'ras', 'rgb', 'rgba', 'sgi', 'spi', 'spider', 'sun', 'tga', 'tif', 'tiff', 'vda', 'vst', 'wal', 'webp', 'xbm', 'xpm'])
        extensions = list()
        for file in directory_files:
            try:
                ext = file.split(".")[-1].lower()
                extensions.append(ext)
            except:
                extensions.append("_")
        keep_files = directory_files[np.isin(extensions, valid_extensions)]
        skip_files = directory_files[np.logical_not(np.isin(extensions, valid_extensions))]
        return keep_files, skip_files
    
    def _build_image_dictionaries(self, valid_files):
        # Function that builds dictionaries of image tensors and metadata
        tensor_dictionary = dict()
        id_to_shape_dictionary = dict()
        filename_dictionary = dict()
        invalid_files = dict()
        id_to_group_dictionary = dict()
        group_to_id_dictionary = dict()
        count = 0
        if self.__in_folder:
            # Directories separately
            for j in range(0, len(valid_files)):
                group_id = f"group_{j}"
                group_img_ids = []
                with Pool(processes=self.__processes, maxtasksperchild=self.__maxtasksperchild) as pool:
                    file_nums = [(i, valid_files[j][i]) for i in range(len(valid_files[j]))]
                    for output in pool.starmap(self._generate_tensor, file_nums):
                        if isinstance(output, dict):
                            invalid_files.update(output)
                            count += 1
                        else:
                            img_id = uuid4().int
                            while img_id in filename_dictionary:
                                img_id = uuid4().int
                            filename = output[0]
                            tensor = output[1]
                            shape = output[2]
                            group_img_ids.append(img_id)
                            id_to_group_dictionary.update({img_id : group_id})
                            id_to_shape_dictionary.update({img_id : shape})
                            filename_dictionary.update({img_id : valid_files[j][filename]})
                            tensor_dictionary.update({img_id : tensor})
                            count += 1                         
                group_to_id_dictionary.update({group_id : group_img_ids})
        
        else:
            # Union of all directories
            with Pool(processes=self.__processes, maxtasksperchild=self.__maxtasksperchild) as pool:
                file_nums = [(i, valid_files[i]) for i in range(len(valid_files))]
                for output in pool.starmap(self._generate_tensor, file_nums):
                    if isinstance(output, dict):
                        invalid_files.update(output)
                        count += 1
                    else:
                        img_id = uuid4().int
                        while img_id in filename_dictionary:
                            img_id = uuid4().int
                        filename = output[0]
                        tensor = output[1]
                        shape = output[2]
                        id_to_shape_dictionary.update({img_id : shape})
                        filename_dictionary.update({img_id : valid_files[filename]})
                        tensor_dictionary.update({img_id : tensor})
                        count += 1         
             
        return tensor_dictionary, id_to_shape_dictionary, filename_dictionary, id_to_group_dictionary, group_to_id_dictionary, invalid_files

    def _generate_tensor(self, num, file):
        # Function that generates a tensor of an image
        try:
            img = Image.open(file)
            if img.getbands() != ('R', 'G', 'B'):
                img = img.convert('RGB')
            shape = np.asarray(img).shape # new
            img = img.resize((self.__px_size, self.__px_size), resample=Image.BICUBIC)
            img = np.asarray(img)
            return (num, img, shape)
        except Exception as e:
            if e.__class__.__name__== 'UnidentifiedImageError':
                return {str(Path(file)) : 'UnidentifiedImageError: file could not be identified as image.'}
            else:
                return {str(Path(file)) : str(e)}



        

class _validate_param:
    '''
    A class used to validate difPy input parameters.
    '''
    def _directory(directory):
        # Function that validates the 'directory' parameter

        # Check the type of directory parameter provided
        if len(directory) == 0:
            raise ValueError('Invalid directory parameter: no directory provided.')
        if all(isinstance(dir, list) for dir in directory):
            directory = np.array([item for sublist in directory for item in sublist])
        elif all(isinstance(dir, str) for dir in directory):
            directory = np.array(directory) 
        else:
            raise ValueError('Invalid directory parameter: directories must be of type LIST or STRING.')
        
        # Check if the directory exists
        for dir in directory:
            dir = Path(dir)
            if not (os.path.isdir(dir) or os.path.isfile(dir)):
                raise FileNotFoundError(f'Directory "{str(dir)}" does not exist')
            
        # Check if the directories provided are unique
        if len(set(directory)) != directory.size:
            raise ValueError('Invalid directory parameters: invalid attempt to compare a directory with itself.')
        
        return sorted(directory)

    def _recursive(recursive):
        # Function that validates the 'recursive' input parameter
        if not isinstance(recursive, bool):
            raise Exception('Invalid value for "recursive" parameter: must be of type BOOL.')
        return recursive

    def _in_folder(in_folder, recursive):
        # Function that validates the 'in_folder' input parameter
        if not isinstance(in_folder, bool):
            raise Exception('Invalid value for "in_folder" parameter: must be of type BOOL.')
        elif not recursive and in_folder:
            warnings.warn('Parameter "in_folder" cannot be "True" if "recursive" is set to "False". "in_folder" will be ignored.')
            in_folder = False
        return in_folder
    
    def _limit_extensions(limit_extensions):
        # Function that validates the 'limit_extensions' input parameter
        if not isinstance(limit_extensions, bool):
            raise Exception('Invalid value for "limit_extensions" parameter: must be of type BOOL.')
        return limit_extensions

    def _similarity(similarity):
        # Function that validates the 'similarity' input parameter
        if similarity in ['low', 'normal', 'high']:
            raise Exception('Since difPy v3.0.8, "similarity" parameter only accepts "duplicates" and "similar" as input options.')  
        elif similarity not in ['duplicates', 'similar']: 
            try:
                similarity = float(similarity)
                if similarity < 0:
                  raise Exception('Invalid value for "similarity" parameter: must be >= 0.')  
                else:
                    return similarity
            except:
                raise Exception('Invalid value for "similarity" parameter: must be "duplicates", "similar" or of type INT or FLOAT.')
        else: 
            if similarity == 'duplicates':
                # search for duplicate images
                similarity = 0
            elif similarity == 'similar':
                # search for similar images
                similarity = 5
            return similarity

    def _px_size(px_size):
        # Function that validates the 'px_size' input parameter   
        if not isinstance(px_size, int):
            raise Exception('Invalid value for "px_size" parameter: must be of type INT.')
        if px_size < 10 or px_size > 5000:
            raise Exception('Invalid value for "px_size" parameter: must be between 10 and 5000.')
        return px_size

    def _rotate(rotate):
        # Function that validates the 'rotate' input parameter   
        if not isinstance(rotate, bool):
            raise Exception('Invalid value for "rotate" parameter: must be of type BOOL.')
        return rotate         

    def _lazy(lazy):
        # Function that validates the 'lazy' input parameter
        if not isinstance(lazy, bool):
            raise Exception('Invalid value for "lazy" parameter: must be of type BOOL.')
        return lazy

    def _show_progress(show_progress):
        # Function that validates the 'show_progress' input parameter
        if not isinstance(show_progress, bool):
            raise Exception('Invalid value for "show_progress" parameter: must be of type BOOL.')
        return show_progress 

    def _processes(processes):
        # Function that validates the 'processes' input parameter
        if not isinstance(processes, int):
            if not processes == None:
                raise Exception('Invalid value for "processes" parameter: must be of type INT.')
        return processes     

    def _maxtasksperchild(maxtasksperchild):
        # Function that validates the 'maxtasksperchild' input parameter
        if not isinstance(maxtasksperchild, int):
            if not maxtasksperchild == None:
                raise Exception('Invalid value for "maxtasksperchild" parameter: must be of type INT.')
        return maxtasksperchild        

    def _chunksize(chunksize):
        # Function that validates the 'chunksize' input parameter
        if not isinstance(chunksize, int):
            if not chunksize == None:
                raise Exception('Invalid value for "chunksize" parameter: must be of type INT.')
        return chunksize        

    def _silent_del(silent_del):
        # Function that _validates the 'delete' and the 'silent_del' input parameter
        if not isinstance(silent_del, bool):
            raise Exception('Invalid value for "silent_del" parameter: must be of type BOOL.')
        return silent_del
    
    def _file_list(file_list):
        # Function that _validates the 'file_list' input parameter
        if not isinstance(file_list, list):
            raise Exception('Invalid value: please input a valid difPy search object.')
        return file_list
    
    def _move_to(dir):
        # Function that _validates the 'move_to' input parameter
        if not isinstance(dir, str):
            raise Exception('Invalid value for "move_to" parameter: must be of type STR')
        else:
            dir = Path(dir)
            if not os.path.exists(dir):
                try:
                    os.makedirs(dir)
                except:
                    raise Exception(f'Invalid value for "move_to" parameter: "{str(dir)}" does not exist.')
            elif not os.path.isdir(dir):
                raise ValueError(f'Invalid value for "move_to" parameter: "{str(dir)}" is not a directory.')
        return dir 

class _help_progress:
    '''
    A helper class used for updating the difPy progress bar.
    '''
    def _show_bar(count, total_count, task='processing images'):
        # Function that displays a progress bar during the search
        if count == total_count:
            print(f'difPy {task}: [{count/total_count:.0%}]')
            #print(f'difPy {task}: [{count+1}/{total_count}] [{(count+1)/total_count:.0%}]')          
        else:
            print(f'difPy {task}: [{count/total_count:.0%}]', end='\r')
        
class _help_convert_type:
    '''
    A helper class used for converting variable types.
    '''
    def _str_to_int(x):
    # Function to make the CLI accept int and str type inputs for the similarity parameter
        try:
            return int(x)
        except:
            return x
        
if __name__ == '__main__':
    # Parameters for when launching difPy via CLI
    parser = argparse.ArgumentParser(description='Find duplicate or similar images with difPy - https://github.com/elisemercury/Duplicate-Image-Finder')
    parser.add_argument('-D', '--directory', type=str, nargs='+', help='Paths of the directories to be searched. Default is working dir.', required=False, default=[os.getcwd()])
    parser.add_argument('-Z', '--output_directory', type=str, help='Output directory path for the difPy result files. Default is working dir.', required=False, default=None)
    parser.add_argument('-r', '--recursive', type=lambda x: bool(strtobool(x)), help='Search recursively within the directories.', required=False, choices=[True, False], default=True)
    parser.add_argument('-i', '--in_folder', type=lambda x: bool(strtobool(x)), help='Search for matches in the union of directories.', required=False, choices=[True, False], default=False)    
    parser.add_argument('-le', '--limit_extensions', type=lambda x: bool(strtobool(x)), help='Limit search to known image file extensions.', required=False, choices=[True, False], default=True)
    parser.add_argument('-px', '--px_size', type=int, help='Compression size of images in pixels.', required=False, default=50)
    parser.add_argument('-p', '--show_progress', type=lambda x: bool(strtobool(x)), help='Show the real-time progress of difPy.', required=False, choices=[True, False], default=True)
    parser.add_argument('-s', '--similarity', type=_help_convert_type._str_to_int, help='Similarity grade (mse).', required=False, default='duplicates')
    parser.add_argument('-ro', '--rotate', type=lambda x: bool(strtobool(x)), help='Rotate images during comparison process.', required=False, choices=[True, False], default=True)    
    parser.add_argument('-la', '--lazy', type=lambda x: bool(strtobool(x)), help='Compares image dimensions before comparison process.', required=False, choices=[True, False], default=True)    
    parser.add_argument('-mv', '--move_to', type=str, help='Output directory path of lower quality images among matches.', required=False, default=None)
    parser.add_argument('-d', '--delete', type=lambda x: bool(strtobool(x)), help='Delete lower quality images among matches.', required=False, choices=[True, False], default=False)
    parser.add_argument('-sd', '--silent_del', type=lambda x: bool(strtobool(x)), help='Suppress the user confirmation when deleting images.', required=False, choices=[True, False], default=False)
    parser.add_argument('-proc', '--processes', type=_help_convert_type._str_to_int, help='Maximum number of simultaneous processes when multiprocessing.', required=False, default=None)
    parser.add_argument('-maxt', '--maxtasksperchild', type=_help_convert_type._str_to_int, help='Maximum number of tasks completed by each child process when multiprocessing.', required=False, default=None)
    
    args = parser.parse_args()

    # initialize difPy
    dif = build(args.directory, recursive=args.recursive, in_folder=args.in_folder, limit_extensions=args.limit_extensions, px_size=args.px_size, show_progress=args.show_progress, processes=args.processes, maxtasksperchild=args.maxtasksperchild)
    
    # perform search
    se = search(dif, similarity=args.similarity, rotate=args.rotate, lazy=args.lazy, processes=args.processes, maxtasksperchild=args.maxtasksperchild)

    # create filenames for the output files
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    result_file = f'difPy_{timestamp}_results.json'
    lq_file = f'difPy_{timestamp}_lower_quality.json'
    stats_file = f'difPy_{timestamp}_stats.json'

    # check if 'output_directory' parameter exists
    if args.output_directory != None:
        dir = args.output_directory
        if not os.path.exists(dir):
            os.makedirs(dir)
    else:
        dir = os.getcwd()

    # output 'search.results' to file
    with open(os.path.join(dir, result_file), 'w') as file:
        json.dump(se.result, file)

    # output 'search.stats' to file
    with open(os.path.join(dir, stats_file), 'w') as file:
        json.dump(se.stats, file)

    # check 'move_to' parameter
    if args.move_to != None:
        # move lower quality files
        se.move_to(args.move_to)

    # output 'search.lower_quality' to file
    with open(os.path.join(dir, lq_file), 'w') as file:
        json.dump(se.lower_quality, file)

    # check 'delete' parameter
    if args.delete:
        # delete search.lower_quality files
        se.delete(silent_del=args.silent_del)

    print(f'''\n{result_file}\n{lq_file}\n{stats_file}\n\nsaved in '{dir}'.''')