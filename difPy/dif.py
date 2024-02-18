'''
difPy - Python package for finding duplicate and similar images.
2024 Elise Landman
https://github.com/elisemercury/Duplicate-Image-Finder
'''
from glob import glob
from multiprocessing import Pool
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

class build:
    '''
    A class used to initialize difPy and build its image repository
    '''
    def __init__(self, *directory, recursive=True, in_folder=False, limit_extensions=True, px_size=50, show_progress=True, processes=5, **kwargs):
        '''
        Parameters
        ----------
        directory : str, list
            Paths of the directories or the files to be searched
        recursive : bool (optional)
            Search recursively within the directories (default is True)
        in_folder : bool (optional)
            If False, searches for matches in the union of directories (default is False)
            If True, searches for matches in separate/isolated directories
        limit_extensions : bool (optional)
            Limit search to known image file extensions (default is True)
        px_size : int (optional)
            Image compression size in pixels (default is 50)
        show_progress : bool (optional)
            Show the difPy progress bar in console (default is True)
        processes : int (optional)
            Number of worker processes for multiprocessing (see https://docs.python.org/3/library/multiprocessing.html#multiprocessing.pool.Pool)
        '''
        # Validate input parameters
        self.__directory = _validate_param._directory(directory)
        self.__recursive = _validate_param._recursive(recursive)
        self.__in_folder = _validate_param._in_folder(in_folder, recursive)
        self.__limit_extensions = _validate_param._limit_extensions(limit_extensions)
        self.__px_size = _validate_param._px_size(px_size)
        self.__show_progress = _validate_param._show_progress(show_progress)
        self.__processes = _validate_param._processes(processes)
        _validate_param._kwargs(kwargs)

        self._tensor_dictionary, self._id_to_shape_dictionary, self._filename_dictionary, self._id_to_group_dictionary, self._group_to_id_dictionary, self._invalid_files, self.stats = self._main()

        return

    def _main(self):
        # Function that runs the full Build workflow
        if self.__show_progress:
            count = 0
            total_count = 3
            _help._progress_bar(count, total_count, task='preparing files')

        start_time = datetime.now()
        # read files
        valid_files, skipped_files = self._get_files()
        if self.__show_progress:
            count += 1
            _help._progress_bar(count, total_count, task='preparing files')
        
        # build image dictionary from files
        tensor_dictionary, id_to_shape_dictionary, filename_dictionary, id_to_group_dictionary, group_to_id_dictionary, invalid_files = self._build_image_dictionaries(valid_files)    

        end_time = datetime.now()
        if self.__show_progress:
            count += 1
            _help._progress_bar(count, total_count, task='preparing files')
        
        # generate build statistics
        stats = _generate_stats().build(start_time=start_time, end_time=end_time, total_files=len(filename_dictionary), invalid_files=invalid_files, skipped_files=skipped_files, directory=self.__directory, recursive=self.__recursive, in_folder=self.__in_folder, limit_extensions=self.__limit_extensions, px_size=self.__px_size, processes=self.__processes)

        if self.__show_progress:
            count += 1
            _help._progress_bar(count, total_count, task='preparing files')

        return tensor_dictionary, id_to_shape_dictionary, filename_dictionary, id_to_group_dictionary, group_to_id_dictionary, invalid_files, stats

    def _get_files(self):
        # Function that searches for files in the input directories
        valid_files_all = []
        skipped_files_all = np.array([])
        if self.__in_folder:
            # search directories separately
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
            # search union of all directories
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
            warnings.warn('Parameter "limit_extensions" is set to False. difPy result accuracy can not be guaranteed for non-supported filetypes.', )
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
            # create build for directories separately
            for j in range(0, len(valid_files)):
                group_id = f"group_{j}"
                group_img_ids = []
                with Pool(processes=self.__processes) as pool:
                    file_nums = [(i, valid_files[j][i]) for i in range(len(valid_files[j]))]
                    for output in pool.starmap(self._generate_tensor, file_nums):
                        if isinstance(output, dict):
                            invalid_files.update(output)
                            count += 1
                        else:
                            img_id = count
                            filename = output[0]
                            tensor = output[1]
                            shape = output[2]
                            group_img_ids.append(img_id)
                            # update the dictionaries
                            id_to_group_dictionary.update({img_id : group_id})
                            id_to_shape_dictionary.update({img_id : shape})
                            filename_dictionary.update({img_id : valid_files[j][filename]})
                            tensor_dictionary.update({img_id : tensor})
                            count += 1                         
                group_to_id_dictionary.update({group_id : group_img_ids})
        
        else:
            # create build for Union of all directories
            with Pool(processes=self.__processes) as pool:
                file_nums = [(i, valid_files[i]) for i in range(len(valid_files))]
                for output in pool.starmap(self._generate_tensor, file_nums):
                    if isinstance(output, dict):
                        invalid_files.update(output)
                        count += 1
                    else:
                        img_id = count
                        filename = output[0]
                        tensor = output[1]
                        shape = output[2]
                        # update the dictionaries
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

class search:
    '''
    A class used to search for matches in a difPy image repository
    '''
    def __init__(self, difpy_obj, similarity='duplicates', rotate=True, lazy=True, show_progress=True, processes=5, chunksize=None, **kwargs):
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
            Only searches for duplicate/similar images that have the same dimensions (width x height in pixels) (default is True)
        show_progress : bool (optional)
            Show the difPy progress bar in console (default is True)
        processes : int (optional)
            Maximum number of simultaneous processes for multiprocessing (see https://docs.python.org/3/library/multiprocessing.html#multiprocessing.pool.Pool)
        chunksize : int (optional)
            This parameter is only relevant when working with large image datasets (> 5k images). Sets the batch size at which the job is simultaneously processed when multiprocessing. (see https://docs.python.org/3/library/multiprocessing.html#multiprocessing.pool.Pool.imap_unordered)

        '''
        # Validate input parameters
        self.__difpy_obj = difpy_obj
        self.__similarity = _validate_param._similarity(similarity)
        self.__rotate = _validate_param._rotate(rotate)
        self.__lazy = _validate_param._lazy(lazy)
        self.__show_progress = _validate_param._show_progress(show_progress)
        self.__processes = _validate_param._processes(processes)
        self.__chunksize = _validate_param._chunksize(chunksize)
        self.__in_folder = self.__difpy_obj.stats['process']['build']['parameters']['in_folder']
        _validate_param._kwargs(kwargs)

        print("Initializing search...", end='\r')
        self.result, self.lower_quality, self.stats = self._main()
        return

    def _main(self):
        # Function that runs the full Search workflow
        start_time = datetime.now()

        if self.__in_folder:
            # search directories separately
            result = self._search_infolder()
            result = self._format_result_infolder(result)
            lower_quality, duplicate_count, similar_count = self._search_metadata_infolder(result)
        else:
            # search union of all directories
            result = self._search_union()
            result = self._format_result_union(result)
            # compare image qualities and computes process metadata
            lower_quality, duplicate_count, similar_count = self._search_metadata_union(result)

        end_time = datetime.now()

        # generate process stats
        stats = _generate_stats().search(build_stats=self.__difpy_obj.stats, start_time=start_time, end_time=end_time, similarity = self.__similarity, rotate=self.__rotate, lazy=self.__lazy, processes=self.__processes, files_searched=len(self.__difpy_obj._tensor_dictionary), duplicate_count=duplicate_count, similar_count=similar_count, chunksize=self.__chunksize)

        return result, lower_quality, stats

    def _search_union(self):
        # Function that performs search in the union of all directories
        result_raw = list()
        self.__count = 0

        if len(self.__difpy_obj._tensor_dictionary.keys()) <= 5000:
            # search algorithm for smaller datasets, <= 5k images
            id_combinations = list(combinations(list(self.__difpy_obj._tensor_dictionary.keys()), 2))
            with Pool(processes=self.__processes) as pool:
                output = pool.map(self._find_matches, id_combinations)
            for i in output:
                if i:
                    # if matches found, add to result
                    result_raw = self._add_to_result(result_raw, i)
            self.__count += 1       
            if self.__show_progress:
                _help._progress_bar(self.__count, 1, task=f'searching files')

        else:
            # search algorithm for smaller datasets, > 5k images
            if self.__chunksize == None:
                self.__chunksize = round(1000000 / len(self.__difpy_obj._tensor_dictionary.keys()))
            with Pool(processes=self.__processes) as pool:
                for output in pool.imap_unordered(self._find_matches_batch, self._yield_comparison_group(), self.__chunksize):
                    if len(output) > 0:
                        # if matches found, add to result
                        result_raw = result_raw + output
                    self.__count += 1  
                    if self.__show_progress:
                        print(self.__count, end="\r")
                        _help._progress_bar(self.__count, len(self.__difpy_obj._tensor_dictionary.keys())-1, task=f'searching files')     

        # format the end result
        result = self._group_result_union(result_raw)
        return result

    def _search_infolder(self):
        # Function that performs search in isolated/separate directories
        result_raw = list()
        grouped_img_ids = [img_ids for group_id, img_ids in self.__difpy_obj._group_to_id_dictionary.items()]
        self.__count = 0

        with Pool(processes=self.__processes) as pool:
            for ids in grouped_img_ids:
                if len(ids) <= 5000:
                    # search algorithm for smaller datasets, <= 5k images
                    id_combinations = list(combinations(ids, 2))
                    output = pool.map(self._find_matches, id_combinations)
                    for i in output:
                        if i:
                            # if matches found, add to result
                            result_raw = self._add_to_result(result_raw, i)
                    self.__count += 1        
                else:
                    # search algorithm for bigger datasets, > 5k images
                    if self.__chunksize == None:
                        self.__chunksize = round(1000000 / len(ids))
                    for output in pool.imap_unordered(self._find_matches_batch, self._yield_comparison_group(), self.__chunksize):
                        if len(output) > 0:
                            # if matches found, add to result
                            result_raw = result_raw + output
                    self.__count += 1  
                if self.__show_progress:
                    _help._progress_bar(self.__count, len(grouped_img_ids), task=f'searching files')
        
        # format the end result
        result = self._group_result_infolder(result_raw)
        return result

    def _format_result_union(self, result):
        # Helper function that replaces the image IDs in the result dictionary by their filename
        updated_result = dict()
        for key, value in result.items():
            # replace the key with the corresponding value from dict2
            new_key = self.__difpy_obj._filename_dictionary.get(key, key)
            # replace the values in the inner lists with corresponding values from dict2
            new_value = [[self.__difpy_obj._filename_dictionary.get(inner[0], inner[0]), inner[1]] for inner in value]
            # update the new dictionary
            updated_result[new_key] = new_value
        return updated_result

    def _format_result_infolder(self, result):
        # Helper function that replaces the image IDs in the result dictionary by their filename
        updated_result = dict()
        for group_id in result.keys():
            for key, value in result[group_id].items():
                # replace the key with the corresponding value from dict2
                new_key = self.__difpy_obj._filename_dictionary.get(key, key)
                # replace the values in the inner lists with corresponding values from dict2
                new_value = [[self.__difpy_obj._filename_dictionary.get(inner[0], inner[0]), inner[1]] for inner in value]
                # update the new dictionary
                if group_id not in updated_result.keys():
                    updated_result.update({group_id : {}})
                updated_result[group_id][new_key] = new_value
        return updated_result

    def _find_matches(self, ids):
        # Function that searches for a match between two images
        id_A = ids[0]
        id_B = ids[1]
        tensor_A = self.__difpy_obj._tensor_dictionary[id_A]
        tensor_B = self.__difpy_obj._tensor_dictionary[id_B] 
        tensor_shape_A = self.__difpy_obj._id_to_shape_dictionary[id_A]
        tensor_shape_B = self.__difpy_obj._id_to_shape_dictionary[id_B]

        if self.__lazy:
            # check if two tensors have the same dimensions
            if _compare_imgs._compare_shape(tensor_shape_A, tensor_shape_B): 
                # check if two tensors are equal
                if _compare_imgs._check_equality(tensor_A, tensor_B):
                    return (id_A, id_B, 0.0) # MSE will always be 0
                else:
                    # compute the MSE
                    mse = _compare_imgs._compute_mse(tensor_A, tensor_B, rotate=self.__rotate)
                    if mse <= self.__similarity:
                        return (id_A, id_B, mse)
            else:
                return False
        else:
            # check if two tensors are equal
            if _compare_imgs._check_equality(tensor_A, tensor_B):
                return (id_A, id_B, 0.0) # MSE will always be 0
            else:
                # compute the MSE
                mse = _compare_imgs._compute_mse(tensor_A, tensor_B, rotate=self.__rotate)
                if mse <= self.__similarity:
                    return (id_A, id_B, mse)            

    def _find_matches_batch(self, ids):
        # Function that searches for matches among images in batches
        result = list()
        id_A = ids[0][0]
        tensor_A = self.__difpy_obj._tensor_dictionary[id_A]
        ids_B_list = np.asarray([x[1] for x in ids])
        tensor_B_list = np.asarray([self.__difpy_obj._tensor_dictionary[x[1]] for x in ids])

        if self.__lazy:
            # compare only those that have the same shape
            shape_A_list = [sorted(self.__difpy_obj._id_to_shape_dictionary[id_A])]*len(ids)
            shape_B_list = [sorted(self.__difpy_obj._id_to_shape_dictionary[id_B]) for id_B in ids_B_list]
            same_shape = np.equal(shape_A_list, shape_B_list).all(axis=1)
            shape_index = np.where(same_shape)
            if len(shape_index) > 0:
                ids_B_list = ids_B_list[shape_index]
                tensor_B_list = tensor_B_list[shape_index]
            
        # check for exact matches among img A and imgs B
        sum_B_list = [np.sum(tensor_B) for tensor_B in tensor_B_list]
        sum_A_list = [np.sum(tensor_A)]*len(sum_B_list)
        equals = np.equal(sum_A_list, sum_B_list)
        
        dupl_index = np.where(equals == True) 
        non_dupl_index = np.where(equals == False)

        # append duplicates to result
        if len(dupl_index) > 0:
            for id_B in ids_B_list[dupl_index]:
                result.append((id_A, id_B, 0))
            tensor_B_list = tensor_B_list[non_dupl_index]
            ids_B_list = ids_B_list[non_dupl_index]       

        if self.__similarity > 0:
            # for the remaining images, compute MSE for reach rotation
            mses = np.asarray([_compare_imgs._compute_mse(tensor_A, tensor_B, 
                                                            rotate=self.__rotate) for tensor_B in tensor_B_list])
            mse_index_sim = np.where(mses <= self.__similarity)
            if len(mse_index_sim) > 0:
                i = 0
                # append to result
                for id_B in ids_B_list[mse_index_sim]:
                    result.append((id_A, id_B, mses[i]))
                    i+=1                   

        return result

    def _add_to_result(self, result_raw, output):
        # Appends output to result
        result_raw.append(output)
        return result_raw

    def _yield_comparison_group(self):
        # Yields a list of images ready for comparison
        max_value = len(self.__difpy_obj._tensor_dictionary.keys())
        for i in range(max_value):
            group = [(i, j) for j in range(i+1, max_value)]
            if len(group) != 0:
                yield group

    def _group_result_union(self, tuple_list):
        # Function that formats the final result dict
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
        # Function that formats the final result dict
        result = defaultdict(list)
        already_added = set()
        for k, *v in tuple_list:
            k_group = self.__difpy_obj._id_to_group_dictionary[k]
            if k_group not in result:
                result.update({k_group:{}})
            if v[0] not in already_added:
                if k not in result[k_group]:
                    result[k_group].update({k:[]})
                result[k_group][k].append(v)
                already_added.add(v[0])

        result = dict(result)
        del already_added
        return result

    def _search_metadata_union(self, result):
        # Helper function that compares image qualities and computes process metadata
        duplicate_count, similar_count = 0, 0
        lower_quality = np.array([])
        if self.__similarity == 0:
            for img in result.keys():
                match_group = [img]
                # count number of duplicates
                duplicate_count += len(result[img])
                for img_matches in result[img]:
                    
                    match_group.append(img_matches[0])
                # compare image quality
                match_group = _compare_imgs._sort_imgs_by_size(match_group)
                # group lower quality images
                lower_quality = np.concatenate((lower_quality, match_group[1:]), axis = None)
        else:
            for img in result.keys():
                match_group = [img]
                for img_matches in result[img]:
                    # create list of all images in match group
                    match_group.append(img_matches[0])
                    # count number of duplicates/similar images
                    if img_matches[1] == 0:
                        duplicate_count += 1
                    else:
                        similar_count += 1    
                # compare image quality
                match_group = _compare_imgs._sort_imgs_by_size(match_group)
                # group lower quality images
                lower_quality = np.concatenate((lower_quality, match_group[1:]), axis = None)
        
        lower_quality = list(set(lower_quality))
        return lower_quality, duplicate_count, similar_count    

    def _search_metadata_infolder(self, result):
        # Helper function that compares image qualities and computes process metadata
        duplicate_count, similar_count = 0, 0
        lower_quality = np.array([])
        if self.__similarity == 0:
            for group_id in result.keys():
                for img in result[group_id].keys():
                    match_group = [img]
                    # count number of duplicates
                    duplicate_count += len(result[group_id][img])
                    for img_matches in result[group_id][img]:
                        match_group.append(img_matches[0])
                    # compare image quality
                    match_group = _compare_imgs._sort_imgs_by_size(match_group)
                    # group lower quality images
                    lower_quality = np.concatenate((lower_quality, match_group[1:]), axis = None)
        else:
            for group_id in result.keys():
                for img in result[group_id].keys():
                    match_group = [img]
                    for img_matches in result[group_id][img]:
                        # create list of all images in match group
                        match_group.append(img_matches[0])
                        # count number of duplicates/similar images
                        if img_matches[1] == 0:
                            duplicate_count += 1
                        else:
                            similar_count += 1    
                    # compare image quality
                    match_group = _compare_imgs._sort_imgs_by_size(match_group)
                    # group lower quality images
                    lower_quality = np.concatenate((lower_quality, match_group[1:]), axis = None)
            
        lower_quality = list(set(lower_quality))
        return lower_quality, duplicate_count, similar_count  

    def move_to(self, destination_path):
        # Function for moving the lower quality images that were found after the search
        '''
        Parameters
        ----------
        destination_path : str
            Path to move the lower_quality files to
        '''
        destination_path = _validate_param._move_to(destination_path)
        new_lower_quality = []
        for file in self.lower_quality:
            try:
                head, tail = os.path.split(file)
                os.replace(file, os.path.join(destination_path, tail))
                new_lower_quality = np.append(new_lower_quality, str(Path(os.path.join(destination_path, tail))))
            except:
                print(f'Could not move file: {file}')            
        print(f'Moved {len(self.lower_quality)} files(s) to "{str(Path(destination_path))}"')
        self.lower_quality = new_lower_quality
        return  

    def delete(self, silent_del=False):
        # Function for deleting the lower quality images that were found after the search
        '''
        Parameters
        ----------
        silent_del : bool, optional
            Skip user confirmation when delete=True (default is False)
        '''
        silent_del = _validate_param._silent_del(silent_del)
        deleted_files = 0
        if len(self.lower_quality) > 0:
            if not silent_del:
                usr = input('Are you sure you want to delete all lower quality matched images? \n! This cannot be undone. (y/n)')
                if str(usr).lower() == 'y':
                    for file in self.lower_quality:
                        try:
                            os.remove(file)
                            deleted_files += 1
                        except:
                            print(f'Could not delete file: {file}')       
                else:
                    print('Deletion canceled.')
                    return
            else:
                for file in self.lower_quality:
                    try:
                        os.remove(file)
                        deleted_files += 1
                    except:
                        print(f'Could not delete file: {file}')
        print(f'Deleted {deleted_files} file(s)')
        return

class _compare_imgs:
    '''
    A class for comparing images, used by the difpy algorithm
    '''    
    def _compute_mse(tensor_A, tensor_B, rotate=True):
        # Function that computes the mse between two tensors
        if rotate:
            mse_list = []
            for rot in range(0, 3):
                if rot == 0:
                    # first rotation
                    mse = np.square(np.subtract(tensor_A, tensor_B)).mean()
                    mse_list.append(mse)
                elif rot <= 3:
                    # all other rotations
                    tensor_B = np.rot90(tensor_B)
                    mse = np.square(np.subtract(tensor_A, tensor_B)).mean()
                    mse_list.append(mse)
            # return only the smallest MSE during the 4 rotations
            min_mse = min(mse_list)  
            return min_mse
        else:
            # compute MSE without rotating
            mse = np.square(np.subtract(tensor_A, tensor_B)).mean()
            return mse

    def _compare_shape(tensor_shape_A, tensor_shape_B):
        # Function that checks whether the dimensions of two tensors are equal
        if (sorted(tensor_shape_A)==sorted(tensor_shape_B)):
            return True
        else:
            return False

    def _check_equality(tensor_A, tensor_B):
        # Function that checks whether two tensors are equal
        if (tensor_A==tensor_B).all():
            return True
        else:
            return False
        
    def _sort_imgs_by_size(img_list):
        # Function for sorting a list of images based on their file sizes
        imgs_sizes = []
        for img in img_list:
            img_size = (os.stat(str(img)).st_size, img)
            imgs_sizes.append(img_size)
        sort_by_size = [file for size, file in sorted(imgs_sizes, reverse=True)]
        return sort_by_size
        
class _generate_stats:
    '''
    A class for generating statistics on the difPy processes
    '''   
    def __init__(self):
        # Initialize the stats dict
        self.stats = dict()

    def build(self, **kwargs):
        # Function that generates stats for the Build process
        seconds_elapsed = np.round((kwargs['end_time'] - kwargs['start_time']).total_seconds(), 4)
        total_files = kwargs['total_files']
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
                                                         'processes' : kwargs['processes']
                                                        }})
        self.stats['process']['build'].update({'total_files' : {'count': total_files+len(invalid_files)}})   
        self.stats['process']['build'].update({'invalid_files': {'count' : len(invalid_files),
                                               'logs' : invalid_files}})
        
        return self.stats

    def search (self, **kwargs):
        # Function that generates stats for the Search process
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
                                                           'chunksize' : kwargs['chunksize']                                                         
                                                          }})
        stats['process']['search'].update({'files_searched' : kwargs['files_searched']})
        
        stats['process']['search'].update({'matches_found' : {'duplicates': kwargs['duplicate_count'],
                                                              'similar' : kwargs['similar_count']
                                                             }})        
        return stats

class _validate_param:
    '''
    A class used to validate difPy input parameters
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

    def _chunksize(chunksize):
        # Function that validates the 'chunksize' input parameter
        if not isinstance(chunksize, int):
            if not chunksize == None:
                raise Exception('Invalid value for "chunksize" parameter: must be of type INT or None.')
        return chunksize        

    def _silent_del(silent_del):
        # Function that _validates the 'delete' and the 'silent_del' input parameter
        if not isinstance(silent_del, bool):
            raise Exception('Invalid value for "silent_del" parameter: must be of type BOOL.')
        return silent_del
      
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

    def _kwargs(kwargs):
        if "logs" in kwargs:
            warnings.warn('Parameter "logs" was deprecated with difPy v4.1. Using it might lead to an exception in future versions. Consider updating your script.', FutureWarning)

class _help:
    '''
    A helper class used for throughout the difPy processes
    '''
    def _progress_bar(count, total_count, task='processing images'):
        # Function that displays a progress bar during the search
        if count == total_count:
            print(f'difPy {task}: [{count/total_count:.0%}]')    
        else:
            print(f'difPy {task}: [{count/total_count:.0%}]', end='\r')

    def _convert_str_to_int(x):
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
    parser.add_argument('-s', '--similarity', type=_help._convert_str_to_int, help='Similarity grade (mse).', required=False, default='duplicates')
    parser.add_argument('-ro', '--rotate', type=lambda x: bool(strtobool(x)), help='Rotate images during comparison process.', required=False, choices=[True, False], default=True)    
    parser.add_argument('-la', '--lazy', type=lambda x: bool(strtobool(x)), help='Compares image dimensions before comparison process.', required=False, choices=[True, False], default=True)    
    parser.add_argument('-mv', '--move_to', type=str, help='Output directory path of lower quality images among matches.', required=False, default=None)
    parser.add_argument('-d', '--delete', type=lambda x: bool(strtobool(x)), help='Delete lower quality images among matches.', required=False, choices=[True, False], default=False)
    parser.add_argument('-sd', '--silent_del', type=lambda x: bool(strtobool(x)), help='Suppress the user confirmation when deleting images.', required=False, choices=[True, False], default=False)
    parser.add_argument('-p', '--show_progress', type=lambda x: bool(strtobool(x)), help='Show the real-time progress of difPy.', required=False, choices=[True, False], default=True)
    parser.add_argument('-proc', '--processes', type=_help._convert_str_to_int, help='Maximum number of simultaneous processes when multiprocessing.', required=False, default=None)
    parser.add_argument('-ch', '--chunksize', type=_help._convert_str_to_int, help='Only relevant when dataset > 5k images. Sets the batch size at which the job is simultaneously processed when multiprocessing.', required=False, default=None)
    parser.add_argument('-l', '--logs', type=lambda x: bool(strtobool(x)), help='(Deprecated) Collect statistics during the process.', required=False, choices=[True, False], default=None)

    args = parser.parse_args()

    if args.logs != None:
        _validate_param._kwargs(["logs"])

    # initialize difPy
    dif = build(args.directory, recursive=args.recursive, in_folder=args.in_folder, limit_extensions=args.limit_extensions, px_size=args.px_size, show_progress=args.show_progress, processes=args.processes, )
    
    # perform search
    se = search(dif, similarity=args.similarity, rotate=args.rotate, lazy=args.lazy, processes=args.processes, chunksize=args.chunksize)

    # create filenames for the output files
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    result_file = f'difPy_{timestamp}_results.json'
    lq_file = f'difPy_{timestamp}_lower_quality.txt'
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