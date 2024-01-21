'''
difPy - Python package for finding duplicate and similar images
2023 Elise Landman
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

class build:
    '''
    A class used to initialize difPy and build its image repository
    '''
    def __init__(self, *directory, recursive=True, in_folder=False, limit_extensions=True, px_size=50, show_progress=True, logs=True):
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
        logs : bool (optional)
            Collect stats on the difPy process (default is True) 
        '''
        # Validate input parameters
        self.__directory = _validate._directory(directory)
        self.__recursive = _validate._recursive(recursive)
        self.__in_folder = _validate._in_folder(in_folder, recursive)
        self.__limit_extensions = _validate._limit_extensions(limit_extensions)
        self.__px_size = _validate._px_size(px_size)
        self.__show_progress = _validate._show_progress(show_progress)
        self.__stats = _validate._stats(logs)

        self._tensor_dictionary, self._filename_dictionary, self._id_to_group_dictionary, self._group_to_id_dictionary, self._invalid_files, self._stats = self._main()

    def _main(self):
        # Function that runs the build workflow
        if self.__show_progress:
            count = 0
            total_count = 3
            _help._show_progress(count, total_count, task='preparing files')

        self.__start_time = datetime.now()
        valid_files, skipped_files = self._get_files()
        if self.__show_progress:
            count += 1
            _help._show_progress(count, total_count, task='preparing files')
        
        tensor_dictionary, filename_dictionary, id_to_group_dictionary, group_to_id_dictionary, invalid_files = self._build_image_dictionaries(valid_files)
        self.__end_time = datetime.now()
        if self.__show_progress:
            count += 1
            _help._show_progress(count, total_count, task='preparing files')
        
        stats = self._stats(invalid_files=invalid_files, skipped_files=skipped_files)
        if self.__show_progress:
            count += 1
            _help._show_progress(count, total_count, task='preparing files')
        return tensor_dictionary, filename_dictionary, id_to_group_dictionary, group_to_id_dictionary, invalid_files, stats
        # 8m55

    def _stats(self, **kwargs):
        # Function that generates build stats
        stats = dict()
        seconds_elapsed = np.round((self.__end_time - self.__start_time).total_seconds(), 4)
        invalid_files = kwargs['invalid_files']
        for file in kwargs['skipped_files']:
            invalid_files.update({str(Path(file)) : 'ImageFilterWarning: invalid image extension.'})
        stats.update({'directory' : self.__directory})
        stats.update({'process' : {'build': {}}})   
        stats['process']['build'].update({'duration' : {'start': self.__start_time.isoformat(),
                                                        'end' : self.__end_time.isoformat(),
                                                        'seconds_elapsed' : seconds_elapsed
                                                       }})
        stats['process']['build'].update({'parameters': {'recursive' : self.__recursive,
                                                         'in_folder' : self.__in_folder,
                                                         'limit_extensions' : self.__limit_extensions,
                                                         'px_size' : self.__px_size,
                                                        }})
        
        stats.update({'invalid_files': {'count' : len(invalid_files),
                                        'logs' : invalid_files}})
        
        return stats

    def _get_files(self):
        # Function that searched for files in the input directories
        valid_files_all = []
        skipped_files_all = np.array([])
        if self.__in_folder:
            # Search directories separately
            directories = []
            files = []
            for dir in self.__directory:
                if os.path.isdir(dir):
                    directories += glob(str(dir) + '/**/', recursive=self.__recursive)
                elif os.path.isfile(dir):
                    files.append(dir)
            for dir in directories:
                files += glob(str(dir) + '/*', recursive=self.__recursive)
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
        filename_dictionary = dict()
        invalid_files = dict()
        id_to_group_dictionary = dict()
        group_to_id_dictionary = dict()
        count = 0
        if self.__in_folder:
            # Search directories separately
            for j in range(0, len(valid_files)):
                group_id = f"group_{j}"
                group_img_ids = []
                with Pool() as pool:
                    file_nums = [(i, valid_files[j][i]) for i in range(len(valid_files[j]))]
                    for tensor in pool.starmap(self._generate_tensor, file_nums):
                        if isinstance(tensor, dict):
                            invalid_files.update(tensor)
                            count += 1
                        else:
                            img_id = uuid4().int
                            while img_id in filename_dictionary:
                                img_id = uuid4().int
                            group_img_ids.append(img_id)
                            id_to_group_dictionary.update({img_id : group_id})
                            filename_dictionary.update({img_id : valid_files[j][tensor[0]]})
                            tensor_dictionary.update({img_id : tensor[1]})
                            count += 1
                group_to_id_dictionary.update({group_id : group_img_ids})
        
        else:
            # Search union of all directories
            with Pool() as pool:
                file_nums = [(i, valid_files[i]) for i in range(len(valid_files))]
                for tensor in pool.starmap(self._generate_tensor, file_nums):
                    if isinstance(tensor, dict):
                        invalid_files.update(tensor)
                        count += 1
                    else:
                        img_id = uuid4().int
                        while img_id in filename_dictionary:
                            img_id = uuid4().int
                        filename_dictionary.update({img_id : valid_files[tensor[0]]})
                        tensor_dictionary.update({img_id : tensor[1]})
                        count += 1
        return tensor_dictionary, filename_dictionary, id_to_group_dictionary, group_to_id_dictionary, invalid_files

    def _generate_tensor(self, num, file):
        # Function that generates a tesnor of an image
        try:
            img = Image.open(file)
            if img.getbands() != ('R', 'G', 'B'):
                img = img.convert('RGB')
            img = img.resize((self.__px_size, self.__px_size), resample=Image.BICUBIC)
            img = np.asarray(img)
            return (num, img)
        except Exception as e:
            if e.__class__.__name__== 'UnidentifiedImageError':
                return {str(Path(file)) : 'UnidentifiedImageError: file could not be identified as image.'}
            else:
                return {str(Path(file)) : str(e)}

class search:
    '''
    A class used to search for matches in a difPy image repository
    '''
    def __init__(self, difpy_obj, similarity='duplicates', show_progress=True, logs=True):
        '''
        Parameters
        ----------
        difPy_obj : difPy.dif.build
            difPy object containing the image repository
        similarity : 'duplicates', 'similar', float (optional)
            Image comparison similarity threshold (mse) (default is 'duplicates', 0)
        show_progress : bool (optional)
            Show the difPy progress bar in console (default is True)
        logs : bool (optional)
            Collect stats on the difPy process (default is True) 
        '''
        # Validate input parameters
        self.__difpy_obj = difpy_obj
        self.__similarity = _validate._similarity(similarity)
        self.__show_progress = _validate._show_progress(show_progress)
        self.__in_folder = self.__difpy_obj._stats['process']['build']['parameters']['in_folder']
        if self.__show_progress:
            count = 1
            total_count = 3
            _help._show_progress(count, total_count, task='searching files')
        self.result = self._main()
        if self.__show_progress:
            count += 1
            _help._show_progress(count, total_count, task='searching files')
        self.lower_quality, self.__duplicate_count, self.__similar_count = self._search_helper()
        if self.__show_progress:
            count += 1
            _help._show_progress(count, total_count, task='searching files')
        if logs:
            self.stats = self._stats()

    def _main(self):
        # Function that runs the search workflow
        self.start_time = datetime.now()
        self.result = dict()
        self.duplicate_count = 0
        self.similar_count = 0
        if self.__in_folder:
            # Search directories separately
            with Pool() as pool:
                grouped_img_ids = [img_ids for group_id, img_ids in self.__difpy_obj._group_to_id_dictionary.items()]
                items = []
                for ids in grouped_img_ids:
                    items = []
                    for i, id_a in enumerate(ids):
                        for j, id_b in enumerate(ids):
                            if j > i:
                                items.append((id_a, id_b, self.__difpy_obj._tensor_dictionary[id_a], self.__difpy_obj._tensor_dictionary[id_b]))

                    for output in pool.starmap(self._compute_mse, items):
                        if output[2] <= self.__similarity:
                            self._add_to_result(output)
            self.end_time = datetime.now()
            return self.result
        else:
            # Search union of all directories
            with Pool() as pool:       
                ids = list(self.__difpy_obj._tensor_dictionary.keys())
                items = []
                for i, id_a in enumerate(ids):
                    for j, id_b in enumerate(ids):
                        if j > i:
                            items.append((id_a, id_b, self.__difpy_obj._tensor_dictionary[id_a], self.__difpy_obj._tensor_dictionary[id_b]))
                for output in pool.starmap(self._compute_mse, items):
                    if output[2] <= self.__similarity:
                        self._add_to_result(output)
            self.end_time = datetime.now()
            return self.result

    def _stats(self):
        # Function that generates build stats
        stats = self.__difpy_obj._stats
        seconds_elapsed = np.round((self.end_time - self.start_time).total_seconds(), 4)
        stats['process'].update({'search' : {}})
        stats['process']['search'].update({'duration' : {'start': self.start_time.isoformat(),
                                                         'end' : self.end_time.isoformat(),
                                                        'seconds_elapsed' : seconds_elapsed 
                                                        }})
        stats['process']['search'].update({'parameters' : {'similarity_mse': self.__similarity
                                                          }})
        stats['process']['search'].update({'files_searched' : len(self.__difpy_obj._tensor_dictionary)})
        
        stats['process']['search'].update({'matches_found' : {'duplicates': self.__duplicate_count,
                                                              'similar' : self.__similar_count
                                                             }})        
        return stats
 
    def _search_helper(self):
        # Helper function that compares image qualities and computes process metadata
        duplicate_count, similar_count = 0, 0
        lower_quality = []
        if self.__in_folder:
            # Search directories separately
            if self.__similarity > 0:
                for group_id in self.result.keys():
                    for id in self.result[group_id]['contents']:
                        match_group = [self.result[group_id]['contents'][id]['location']]
                        for match_id in self.result[group_id]['contents'][id]['matches']:
                            # compare image quality
                            match_group.append(self.result[group_id]['contents'][id]['matches'][match_id]['location'])
                            match_group = self._compare_img_quality(match_group)
                            lower_quality += match_group[1:]
                            # count duplicate/similar
                            if self.result[group_id]['contents'][id]['matches'][match_id]['mse'] > 0:
                                similar_count += 1
                            else:
                                duplicate_count +=1        
            else:
                for group_id in self.result.keys():
                    duplicate_count += len(self.result[group_id]['contents'])   
                    for id in self.result[group_id]['contents']:       
                        match_group = [self.result[group_id]['contents'][id]['location']]
                        for match_id in self.result[group_id]['contents'][id]['matches']:
                            # compare image quality
                            match_group.append(self.result[group_id]['contents'][id]['matches'][match_id]['location'])
                            match_group = self._compare_img_quality(match_group)
                            lower_quality += match_group[1:]                      
        else:
            # Search union of all directories
            if self.__similarity > 0:
                for id in self.result.keys():
                    match_group = [self.result[id]['location']]
                    for matchid in self.result[id]['matches']:
                        # compare image quality
                        match_group.append(self.result[id]['matches'][matchid]['location'])
                        match_group = self._compare_img_quality(match_group)
                        lower_quality += match_group[1:]
                        # count duplicate/similar
                        if self.result[id]['matches'][matchid]['mse'] > 0:
                            similar_count += 1
                        else:
                            duplicate_count +=1     
            else:
                for id in self.result.keys():
                    match_group = [self.result[id]['location']]
                    duplicate_count += len(self.result[id]['matches'])
                    for matchid in self.result[id]['matches']:
                        # compare image quality
                        match_group.append(self.result[id]['matches'][matchid]['location'])
                        match_group = self._compare_img_quality(match_group)
                        lower_quality += match_group[1:]

        lower_quality = {'lower_quality': list(set(lower_quality))}
        return lower_quality, duplicate_count, similar_count    

    def _compare_img_quality(self, img_list):
        # Function for sorting a list of images based on their file sizes
        imgs_sizes = []
        for img in img_list:
            img_size = (os.stat(str(img)).st_size, img)
            imgs_sizes.append(img_size)
        sort_by_size = [file for size, file in sorted(imgs_sizes, reverse=True)]
        return sort_by_size

    def _add_to_result(self, output):
        # Function that adds a found image match to the result output
        id_A = output[0]
        filename_A = str(Path(self.__difpy_obj._filename_dictionary[id_A]))
        id_B = output[1]
        filename_B = str(Path(self.__difpy_obj._filename_dictionary[id_B]))
        mse = output[2]
        if self.__in_folder:
            # Search directories separately  
            group_id = self.__difpy_obj._id_to_group_dictionary[id_A]
            group_path = os.path.dirname(filename_A) 
            if group_id in self.result:
                for key in self.result[group_id]['contents'].keys():
                    if id_A in self.result[group_id]['contents'][key]['matches']:
                        self.result[group_id]['contents'][key]['matches'].update({id_B : {'location': filename_B,
                                                                                          'mse': mse}}) 
                        return self.result                  
                if id_A in self.result[group_id]['contents']:
                    self.result[group_id]['contents'][id_A]['matches'].update({id_B : {'location': filename_B,
                                                                                       'mse': mse}})
                    return self.result
                else:
                    self.result[group_id]['contents'].update({id_A : {'location': filename_A,
                                                                      'matches' : {id_B : {'location': filename_B,
                                                                                           'mse': mse}}}}) 
                    return self.result
            else:
                self.result.update({group_id : {'location' : group_path,
                                                'contents' : {id_A : {'location': filename_A,
                                                                      'matches': {id_B: {'location' : filename_B,
                                                                                         'mse': mse }}}}}})
                return self.result
        else:
            # Search union of all directories
            for key in list(self.result.keys()):
                if id_A in self.result[key]['matches']:
                    self.result[key]['matches'].update({id_B : {'location': filename_B,
                                                                'mse': mse}}) 
                    return self.result                  
            if id_A in self.result:
                self.result[id_A]['matches'].update({id_B : {'location': filename_B,
                                                             'mse': mse}})
            else:
                self.result.update({id_A : {'location': filename_A,
                                            'matches' : {id_B : {'location': filename_B,
                                                                 'mse': mse}}}}) 
            return self.result 

    def _compute_mse(self, id_A, id_B, img_A, img_B):
        # Function that calculates the mean squared error (mse) between two image matrices
        mse = np.square(np.subtract(img_A, img_B)).mean()
        return (id_A, id_B, mse)      

    def move_to(self, destination_path):
        # Function for moving the lower quality images that were found after the search
        '''
        Parameters
        ----------
        destination_path : str
            Path to move the lower_quality files to
        '''
        destination_path = _validate._move_to(destination_path)
        new_lower_quality = []
        for file in self.lower_quality['lower_quality']:
            try:
                head, tail = os.path.split(file)
                os.replace(file, os.path.join(destination_path, tail))
                new_lower_quality = np.append(new_lower_quality, str(Path(os.path.join(destination_path, tail))))
            except:
                print(f'Could not move file: {file}')            
        print(f'Moved {len(self.lower_quality["lower_quality"])} files(s) to "{str(Path(destination_path))}"')
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
        silent_del = _validate._silent_del(silent_del)
        deleted_files = 0
        if len(self.lower_quality) > 0:
            if not silent_del:
                usr = input('Are you sure you want to delete all lower quality matched images? \n! This cannot be undone. (y/n)')
                if str(usr).lower() == 'y':
                    for file in self.lower_quality['lower_quality']:
                        try:
                            os.remove(file)
                            deleted_files += 1
                        except:
                            print(f'Could not delete file: {file}')       
                else:
                    print('Deletion canceled.')
                    return
            else:
                for file in self.lower_quality['lower_quality']:
                    try:
                        os.remove(file)
                        deleted_files += 1
                    except:
                        print(f'Could not delete file: {file}')
        print(f'Deleted {deleted_files} file(s)')
        return

class _validate:
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
            warnings.warn('"in_folder" cannot be "True" if "recurive" is set to "False". "in_folder" will be ignored.')
            in_folder = False
        return in_folder
    
    def _limit_extensions(limit_extensions):
        # Function that _validates the 'limit_extensions' input parameter
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
                raise Exception('Invalid value for "similarity" parameter: must be of type INT or FLOAT.')
        else: 
            if similarity == 'duplicates':
                # search for duplicate images
                similarity = 0
            elif similarity == 'similar':
                # search for similar images
                similarity = 50
            return similarity

    def _px_size(px_size):
        # Function that validates the 'px_size' input parameter   
        if not isinstance(px_size, int):
            raise Exception('Invalid value for "px_size" parameter: must be of type INT.')
        if px_size < 10 or px_size > 5000:
            raise Exception('Invalid value for "px_size" parameter: must be between 10 and 5000.')
        return px_size

    def _show_progress(show_progress):
        # Function that validates the 'show_progress' input parameter
        if not isinstance(show_progress, bool):
            raise Exception('Invalid value for "show_progress" parameter: must be of type BOOL.')
        return show_progress 

    def _stats(stats):
        # Function that validates the 'stats' input parameter
        if not isinstance(stats, bool):
            raise Exception('Invalid value for "stats" parameter: must be of type BOOL.')
        return stats

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

class _help:
    '''
    A class used for difPy helper functions.
    '''
    def _show_progress(count, total_count, task='processing images'):
        # Function that displays a progress bar during the search
        if count == total_count:
            print(f'difPy {task}: [{count/total_count:.0%}]')
            #print(f'difPy {task}: [{count+1}/{total_count}] [{(count+1)/total_count:.0%}]')          
        else:
            print(f'difPy {task}: [{count/total_count:.0%}]', end='\r')

    def _type_str_int(x):
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
    parser.add_argument('-s', '--similarity', type=_help._type_str_int, help='Similarity grade (mse).', required=False, default='duplicates')
    parser.add_argument('-mv', '--move_to', type=str, help='Output directory path of lower quality images among matches.', required=False, default=None)
    parser.add_argument('-d', '--delete', type=lambda x: bool(strtobool(x)), help='Delete lower quality images among matches.', required=False, choices=[True, False], default=False)
    parser.add_argument('-sd', '--silent_del', type=lambda x: bool(strtobool(x)), help='Suppress the user confirmation when deleting images.', required=False, choices=[True, False], default=False)
    parser.add_argument('-l', '--logs', type=lambda x: bool(strtobool(x)), help='Collect statistics during the process.', required=False, choices=[True, False], default=True)
    args = parser.parse_args()

    # initialize difPy
    dif = build(args.directory, recursive=args.recursive, in_folder=args.in_folder, limit_extensions=args.limit_extensions,px_size=args.px_size, show_progress=args.show_progress, logs=args.logs)
    
    # perform search
    se = search(dif, similarity=args.similarity)

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
    if args.logs:
        with open(os.path.join(dir, stats_file), 'w') as file:
            json.dump(se.stats, file)

    # check 'move_to' parameter
    if args.move_to != None:
        # move lower quality files
        se.lower_quality = se.move_to(se, args.move_to).lower_quality

    # output 'search.lower_quality' to file
    with open(os.path.join(dir, lq_file), 'w') as file:
        json.dump(se.lower_quality, file)

    # check 'delete' parameter
    if args.delete:
        # delete search.lower_quality files
        se.delete(silent_del=args.silent_del)

    print(f'''\n{result_file}\n{lq_file}\n{stats_file}\n\nsaved in '{dir}'.''')