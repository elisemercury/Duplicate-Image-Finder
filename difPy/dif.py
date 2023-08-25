'''
difPy - Python package for finding duplicate or similar images within folders 
https://github.com/elisemercury/Duplicate-Image-Finder
'''
from glob import glob
from matplotlib.pyplot import figure, suptitle, imshow, axis, show as plt
import uuid
import numpy as np
from PIL import Image
from distutils.util import strtobool
import os
#from time import time, strftime, localtime
from datetime import datetime
from pathlib import Path
import argparse
import json
import csv
import warnings
warnings.filterwarnings('ignore')

class dif:
    '''
    A class used to initialize and run difPy
    '''
    def __init__(self, *directory, fast_search=True, recursive=True, limit_extensions=False, similarity='duplicates', px_size=50, show_progress=True, show_output=False, move_to=None, delete=False, silent_del=False, logs=False):
        '''
        Parameters
        ----------
        directory : str, list
            The name(s) of the directories to be compared
        fast_search : bool, optional
            Use Fast Search Algorithm (default is True)
        recursive : bool, optional
            Search recursively within the directories (default is True)
        limit_extensions : bool, optional
            Limit search to known image file extensions (default is False)
        similarity : 'duplicates', 'similar', float, optional
            Image similarity threshold (mse) (default is 'duplicates', 0)
        px_size : int, optional
            Image compression size in pixels (default is 50)
        show_progress : bool, optional
            Show the difPy progress bar in console (default is True)
        show_output : bool, optional
            Show the image matches in console (default is False)
        move_to : bool, optional
            Move the lower quality images to a target folder
        delete : bool, optional
            Delete lower quality matches images (default is False)
        silent_del : bool, optional
            Skip user confirmation when delete=True (default is False)
        logs : bool, optional
            Enable log collection for invalid files in stats output    
        '''
        # Validate input parameters
        self.directory = _validate._directory(directory)
        self.recursive = _validate._recursive(recursive)
        self.limit_extensions = _validate._limit_extensions(limit_extensions)
        self.similarity = _validate._similarity(similarity)
        self.fast_search = _validate._fast_search(fast_search, self.similarity)
        self.px_size = _validate._px_size(px_size)
        self.show_progress = _validate._show_progress(show_progress)
        self.show_output = _validate._show_output(show_output)
        self.move_to = _validate._move_to(move_to)
        self.delete, self.silent_del = _validate._delete(delete, silent_del)
        self.logs = _validate._logs(logs)

        # Start timer
        start_time = datetime.now()

        # Run difpy algortihm
        self.result, self.lower_quality, total_count, duplicate_count, similar_count, invalid_files, skipped_files, deleted_files = self._run()
        
        # End timer
        end_time = datetime.now()
        time_elapsed = np.round((end_time - start_time).total_seconds(), 4)

        # Print depending on similarity parameter
        if self.similarity == 0:
            print(f'Found {duplicate_count} pair(s) of duplicate image(s) in {time_elapsed} seconds.')
        else:
            print(f'Found {duplicate_count} pair(s) of duplicate and {similar_count} pair(s) of similar image(s) in {time_elapsed} seconds.')

        # Generate process stats
        self.stats = self._generate_stats(start_time=start_time, end_time=end_time, time_elapsed=time_elapsed, 
                                          total_count=total_count, duplicate_count=duplicate_count, similar_count=similar_count, 
                                          invalid_files=invalid_files, deleted_files=deleted_files, skipped_files=skipped_files)
    
    def _run(self):
        '''Runs the difPy algorithm.
        '''
        for count, dir in enumerate(self.directory):
            if count == 0:
                directory_files, skipped_files = _help._list_all_files(dir, self.recursive, self.limit_extensions)
                id_by_location = _compute._id_by_location(directory_files, id_by_location=None)
            else:
                if len(self.directory) >= 2:
                    if not os.path.normpath(dir) in directory_files:
                        directory_files, skipped_files = _help._list_all_files(dir, self.recursive, self.limit_extensions)
                        id_by_location = _compute._id_by_location(directory_files, id_by_location=id_by_location)
                    else:
                        print(f"Skipped directory {dir} as it is part of another directory provided.")
                else:
                    break
        imgs_matrices, invalid_files = _compute._imgs_matrices(id_by_location, self.px_size, self.show_progress)
        result, exclude_from_search, total_count, duplicate_count, similar_count = _search._matches(imgs_matrices, id_by_location, self.similarity, self.show_output, self.show_progress, self.fast_search)
        lower_quality = _search._lower_quality(result)

        # Move or delete the lower quality duplicate images
        deleted_files = np.array([])
        if duplicate_count + similar_count != 0:
            if self.move_to != None:
                self.lower_quality = _help._move_imgs(self.lower_quality, self.move_to)
            elif self.delete:
                if self.lower_quality.size != 0:
                    deleted_files = _help._delete_imgs(set(self.lower_quality), silent_del=self.silent_del)

        return result, lower_quality, total_count, duplicate_count, similar_count, invalid_files, skipped_files,deleted_files

    def _generate_stats(self, **kwargs):
        '''Generates stats of the difPy process.
        '''
        if self.logs:
            invalid_stats = {'count': len(kwargs['invalid_files']),
                             'logs': kwargs['invalid_files']}
            deleted_stats = {'count': len(kwargs['deleted_files']), 
                             'logs': kwargs['deleted_files']}
            skipped_stats = {'count': len(kwargs['skipped_files']), 
                             'logs': kwargs['skipped_files']}
        else:
            invalid_stats = {'count': len(kwargs['invalid_files'])}
            deleted_stats = {'count': len(kwargs['deleted_files'])}
            skipped_stats = {'count': len(kwargs['skipped_files'])}
             
        stats = {'directory': self.directory,
                 'duration': {'start_date': kwargs['start_time'].strftime('%Y-%m-%d'),
                              'start_time': kwargs['start_time'].strftime('%Y-%m-%d'),
                              'end_date': kwargs['end_time'].strftime('%Y-%m-%d'),
                              'end_time': kwargs['end_time'].strftime('%Y-%m-%d'),
                              'seconds_elapsed': kwargs['time_elapsed']},
                 'fast_search': self.fast_search,
                 'recursive': self.recursive,
                 'match_mse': self.similarity,
                 'px_size': self.px_size,
                 'files_searched': kwargs['total_count'],
                 'matches_found': {'duplicates': kwargs['duplicate_count'],
                                   'similar': kwargs['similar_count']},
                 'invalid_files': invalid_stats,
                 'deleted_files': deleted_stats,
                 'skipped_files': skipped_stats
                 }
        return stats

class _validate:
    '''
    A class used to validate difPy input parameters.
    '''
    def _directory(directory):
        # Function that _validates the input directories

        # Check the type of directory parameter provided
        if len(directory) == 0:
            raise ValueError('Invalid directory parameter: no directory provided.')
        if all(isinstance(dir, list) for dir in directory):
            directory = np.array([item for sublist in directory for item in sublist])
        elif all(isinstance(dir, str) for dir in directory):
            directory = np.array(directory) 
        else:
            raise ValueError('Invalid directory parameter: directories must be of type list or string.')
        
        # Check if the directory exists
        for dir in directory:
            dir = Path(dir)
            if not os.path.isdir(dir):
                raise FileNotFoundError(f'Directory "{str(dir)}" does not exist')
            
        # Check if the directories provided are unique
        if len(set(directory)) != directory.size:
            raise ValueError('Invalid directory parameters: an attempt to compare a directory with itself.')
        
        return sorted(directory)

    def _fast_search(fast_search, similarity):
        # Function that _validates the 'show_output' input parameter
        if not isinstance(fast_search, bool):
            raise Exception('Invalid value for "fast_search" parameter: must be of type bool.')
        if similarity > 0:
            fast_search = False
        return fast_search

    def _recursive(recursive):
        # Function that _validates the 'recursive' input parameter
        if not isinstance(recursive, bool):
            raise Exception('Invalid value for "recursive" parameter: must be of type bool.')
        return recursive
    
    def _limit_extensions(limit_extensions):
        # Function that _validates the 'limit_extensions' input parameter
        if not isinstance(limit_extensions, bool):
            raise Exception('Invalid value for "limit_extensions" parameter: must be of type bool.')
        return limit_extensions

    def _similarity(similarity):
        # Function that _validates the 'similarity' input parameter
        if similarity in ['low', 'normal', 'high']:
            raise Exception('Since difPy v3.0.8, "similarity" parameter only accepts "duplicates" and "similar" as input options.')  
        elif similarity not in ['duplicates', 'similar']: 
            try:
                similarity = float(similarity)
                if similarity < 0:
                  raise Exception('Invalid value for "similarity" parameter: must be > 0.')  
                else:
                    return similarity
            except:
                raise Exception('Invalid value for "similarity" parameter: must be of type float.')
        else: 
            if similarity == 'duplicates':
                # search for duplicate images
                similarity = 0
            elif similarity == 'similar':
                # search for similar images
                similarity = 1000
            return similarity

    def _px_size(px_size):
        # Function that _validates the 'px_size' input parameter   
        if not isinstance(px_size, int):
            raise Exception('Invalid value for "px_size" parameter: must be of type int.')
        if px_size < 10 or px_size > 5000:
            raise Exception('Invalid value for "px_size" parameter: must be between 10 and 5000.')
        return px_size

    def _show_output(show_output):
        # Function that _validates the 'show_output' input parameter
        if not isinstance(show_output, bool):
            raise Exception('Invalid value for "show_output" parameter: must be of type bool.')
        return show_output

    def _show_progress(show_progress):
        # Function that _validates the 'show_progress' input parameter
        if not isinstance(show_progress, bool):
            raise Exception('Invalid value for "show_progress" parameter: must be of type bool.')
        return show_progress 

    def _move_to(move_to):
        # Function that _validates the 'move_to' input parameter
        if not isinstance(move_to, str):
            if not move_to == None:
                raise Exception('Invalid value for "move_to" parameter: must be of type str or "None"')
        else:
            _validate._directory_exist([move_to])
        return move_to

    def _delete(delete, silent_del):
        # Function that _validates the 'delete' and the 'silent_del' input parameter
        if not isinstance(delete, bool):
            raise Exception('Invalid value for "delete" parameter: must be of type bool.')
        if not isinstance(silent_del, bool):
            raise Exception('Invalid value for "silent_del" parameter: must be of type bool.')
        return delete, silent_del

    def _logs(logs):
        # Function that _validates the 'recursive' input parameter
        if not isinstance(logs, bool):
            raise Exception('Invalid value for "logs" parameter: must be of type bool.')
        return logs

class _compute:
    '''
    A class used for difPy compute operations.
    '''
    def _id_by_location(directory_files, id_by_location):
        # Function that creates a collection of 'ids : image_location'
        img_ids = np.array([])
        for i in range(0, len(directory_files)):
            img_id = uuid.uuid4().int
            while img_id in img_ids:
                img_id = uuid.uuid4().int
            np.append(img_ids, img_id)

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
        invalid_files = {}
        try:
            for id, file in id_by_location.items():
                if show_progress:
                    _help._show_progress(count, total_count, task='preparing files')
                try:
                    img = Image.open(file)
                    if img.getbands() != ('R', 'G', 'B'):
                        img = img.convert('RGB')
                    img = img.resize((px_size, px_size), resample=Image.BICUBIC)
                    img = np.asarray(img)
                    imgs_matrices[id] = img
                except Exception as e:
                    if e.__class__.__name__== 'UnidentifiedImageError':
                        invalid_files[str(Path(file))] = f'UnidentifiedImageError: file could not be identified as image.'
                    else:
                        invalid_files[str(Path(file))] = str(e)
                finally:
                    count += 1
            for id in invalid_files:
                id_by_location.pop(id, None)
            return imgs_matrices, invalid_files
        except KeyboardInterrupt:
            raise KeyboardInterrupt

    def _mse(img_A, img_B):
        # Function that calculates the mean squared error (mse) between two image matrices
        mse = np.square(np.subtract(img_A, img_B)).mean()
        return mse

class _search:
    '''
    A class used for difPy search operations.
    '''
    def _matches(imgs_matrices, id_by_location, similarity, show_output, show_progress, fast_search):
        # Function that searches the images on duplicates/similarity matches
        progress_count = 0
        duplicate_count, similar_count = 0, 0
        total_count = len(imgs_matrices)
        exclude_from_search = np.array([])
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
                            if mse <= similarity:
                                check = False
                                for key in result.keys():
                                    if id_A in result[key]['matches']:
                                        result[key]['matches'][id_B] = {'location': str(Path(id_by_location[id_B])),
                                                                        'mse': mse }  
                                        check = True
                                if not check:                                      
                                    if id_A not in result.keys():
                                        result[id_A] = {'location': str(Path(id_by_location[id_A])),
                                                        'matches': {id_B: {'location': str(Path(id_by_location[id_B])),
                                                                            'mse': mse }}}
                                    else:
                                        result[id_A]['matches'][id_B] = {'location': str(Path(id_by_location[id_B])),
                                                                        'mse': mse }
                                if show_output:
                                    _help._show_img_figs(matrix_A, matrix_B, mse)
                                    _help._show_file_info(str(Path(id_by_location[id_A])), str(Path(id_by_location[id_B])))
                                if fast_search == True:
                                    np.append(exclude_from_search, id_B)
                                rotations = 4
                            else:
                                rotations += 1
                progress_count += 1
        
        if similarity > 0:
            for id in result:
                if similarity > 0:
                    for matchid in result[id]['matches']:
                        if result[id]['matches'][matchid]['mse'] > 0:
                            similar_count += 1
                        else:
                            duplicate_count +=1        
        else:
            for id in result:
                duplicate_count += len(result[id]['matches'])
        return result, exclude_from_search, total_count, duplicate_count, similar_count

    def _lower_quality(result):
        # Function that creates a list of all image matches that have the lowest quality within the match group
        lower_quality = np.array([])
        for id, results in result.items():
            match_group = np.array([])
            np.append(match_group, result[id]['location'])
            for match_id in result[id]['matches']:
                np.append(match_group, result[id]['matches'][match_id]['location'])
            sort_by_size = _help._check_img_quality(match_group)
            lower_quality = lower_quality + sort_by_size[1:]
        return lower_quality

class _help:
    '''
    A class used for difPy helper functions.
    '''
    def _list_all_files(directory, recursive, limit_extensions):
        # Function that creates an array of all files in the directory
        skipped = np.array([])
        directory_files = np.array(glob(str(directory) + '/**', recursive=recursive))
        directory_files = np.array([os.path.normpath(file) for file in directory_files if not os.path.isdir(file)])
        if limit_extensions:
            directory_files, skipped = _help._filter_extensions(directory_files)
        return directory_files, skipped
    
    def _filter_extensions(directory_files):
        # Function that filters files into those with & without valid image extensions
        valid_extensions = ('.apng', '.bw', '.cdf', '.cur', '.dcx', '.dds', '.dib', '.emf', '.eps', '.fli', '.flc', '.fpx', '.ftex', '.fits', '.gd', '.gd2', '.gif', '.gbr', '.icb', '.icns', '.iim', '.ico', '.im', '.imt', '.j2k', '.jfif', '.jfi', '.jif', '.jp2', '.jpe', '.jpeg', '.jpg', '.jpm', '.jpf', '.jpx', '.jpeg', '.mic', '.mpo', '.msp', '.nc', '.pbm', '.pcd', '.pcx', '.pgm', '.png', '.ppm', '.psd', '.pixar', '.ras', '.rgb', '.rgba', '.sgi', '.spi', '.spider', '.sun', '.tga', '.tif', '.tiff', '.vda', '.vst', '.wal', '.webp', '.xbm', '.xpm')
        filtered_list = np.array([])
        skipped_list = np.array([])
        for file in directory_files:
            file_extension = os.path.splitext(file)[1]
            if file_extension.lower() in valid_extensions:
                np.append(filtered_list, file)
            else:
                np.append(skipped_list, file)
        return filtered_list, skipped_list

    def _show_img_figs(img_A, img_B, err):
        # Function that plots two compared image files and their mse
        fig = plt.figure()
        plt.suptitle('MSE: %.2f' % (err))
        # Plot first image
        ax = fig.add_subplot(1, 2, 1)
        plt.imshow(img_A, cmap=plt.cm.gray)
        plt.axis('off')
        # Plot second image
        ax = fig.add_subplot(1, 2, 2)
        plt.imshow(img_B, cmap=plt.cm.gray)
        plt.axis('off')
        # Show the images
        plt.show()

    def _show_file_info(img_A, img_B):
        # Function for printing filename info of plotted image files
        img_A = f'...{img_A[-45:]}'
        img_B = f'...{img_B[-45:]}'
        print(f'''Files:\n{img_A} and \n{img_B}\n''')

    def _rotate_img(img):
        # Function for rotating an image matrix by a 90 degree angle
        img = np.rot90(img, k=1, axes=(0, 1))
        return img

    def _check_img_quality(img_list):
        # Function for sorting a list of images based on their file sizes
        imgs_sizes = np.array([])
        for img in img_list:
            img_size = (os.stat(str(img)).st_size, img)
            np.append(imgs_sizes, img_size)
        sort_by_size = np.array([file for size, file in -np.sort(-imgs_sizes)])
        return sort_by_size

    def _show_progress(count, total_count, task='processing images'):
        # Function that displays a progress bar during the search
        if count+1 == total_count:
            print(f'difPy {task}: [{count}/{total_count}] [{count/total_count:.0%}]', end='\r')
            print(f'difPy {task}: [{count+1}/{total_count}] [{(count+1)/total_count:.0%}]')          
        else:
            print(f'difPy {task}: [{count}/{total_count}] [{count/total_count:.0%}]', end='\r')

    def _move_imgs(lower_quality, move_to):
        new_lower_quality = np.array([])
        for file in lower_quality:
            head, tail = os.path.split(file)
            os.replace(file, os.path.join(move_to, tail))
            np.append(new_lower_quality, str(Path(os.path.join(move_to, tail))))
        print(f'Moved {len(lower_quality)} image(s) to {str(Path(move_to))}')
        return new_lower_quality

    def _delete_imgs(lower_quality_set, silent_del=False):
        # Function for deleting the lower quality images that were found after the search
        deleted_files = np.array([])
        if not silent_del:
            usr = input('Are you sure you want to delete all lower quality matched images? \n! This cannot be undone. (y/n)')
            if str(usr) == 'y':
                for file in lower_quality_set:
                    print('\nDeletion in progress...', end='\r')
                    try:
                        os.remove(file)
                        np.append(deleted_files, file)
                        print(f'Deleted file: {file}', end='\r')
                    except:
                        print(f'Could not delete file: {file}', end='\r')       
            else:
                print('Image deletion canceled.')
                return
        else:
            for file in lower_quality_set:
                print('\nDeletion in progress...', end='\r')
                try:
                    os.remove(file)
                    np.append(deleted_files, file)
                    print(f'Deleted file: {file}', end='\r')
                except:
                    print(f'Could not delete file: {file}', end='\r')
        print(f'\n***\nDeleted {len(deleted_files)} image file(s).')
        return deleted_files

    def _type_str_int(x):
        # Helper function to make the CLI accept int and str type inputs for the similarity parameter
        try:
            return int(x)
        except:
            return x


if __name__ == '__main__':
    # Parameters for when launching difPy via CLI
    parser = argparse.ArgumentParser(description='Find duplicate or similar images with difPy - https://github.com/elisemercury/Duplicate-Image-Finder')
    parser.add_argument('-D', '--directory', type=str, nargs='+', help='Directory to search for images.', required=True)
    parser.add_argument('-Z', '--output_directory', type=str, help='Output directory for the difPy result files. Default is working dir.', required=False, default=None)
    parser.add_argument('-f', '--fast_search', type=lambda x: bool(strtobool(x)), help='Use difPys Fast Search Algorithm.', required=False, choices=[True, False], default=True)
    parser.add_argument('-r', '--recursive', type=lambda x: bool(strtobool(x)), help='Scan subfolders for duplicate images.', required=False, choices=[True, False], default=True)
    parser.add_argument('-le', '--limit_extensions', type=lambda x: bool(strtobool(x)), help='Limit search to known image file extensions.', required=False, choices=[True, False], default=False)
    parser.add_argument('-s', '--similarity', type=_help._type_str_int, help='Similarity grade.', required=False, default='duplicates')
    parser.add_argument('-px', '--px_size', type=int, help='Compression size of images in pixels.', required=False, default=50)
    parser.add_argument('-p', '--show_progress', type=lambda x: bool(strtobool(x)), help='Show the real-time progress of difPy.', required=False, choices=[True, False], default=True)
    parser.add_argument('-o', '--show_output', type=lambda x: bool(strtobool(x)), help='Show the compared images in real-time.', required=False, choices=[True, False], default=False)
    parser.add_argument('-mv', '--move_to', type=str, help='Move the lower quality images to a target folder.', required=False, default=None)
    parser.add_argument('-d', '--delete', type=lambda x: bool(strtobool(x)), help='Delete all duplicate images with lower quality.', required=False, choices=[True, False], default=False)
    parser.add_argument('-sd', '--silent_del', type=lambda x: bool(strtobool(x)), help='Suppress the user confirmation when deleting images.', required=False, choices=[True, False], default=False)
    parser.add_argument('-l', '--logs', type=lambda x: bool(strtobool(x)), help='Enable log collection for invalid files.', required=False, choices=[True, False], default=False)
    args = parser.parse_args()

    # initialize difPy
    search = dif(args.directory, fast_search=args.fast_search, recursive=args.recursive, limit_extensions=args.limit_extensions, similarity=args.similarity,px_size=args.px_size, show_output=args.show_output, show_progress=args.show_progress, move_to=args.move_to, delete=args.delete, silent_del=args.silent_del, logs=args.logs)

    # create filenames for the output files
    timestamp =str(time.time()).replace('.', '_')
    result_file = f'difPy_results_{timestamp}.json'
    lq_file = f'difPy_lower_quality_{timestamp}.csv'
    stats_file = f'difPy_stats_{timestamp}.json'

    if args.output_directory != None:
        dir = args.output_directory
    else:
        dir = os.getcwd()

    if not os.path.exists(dir):
        os.makedirs(dir)

    with open(os.path.join(dir, result_file), 'w') as file:
        json.dump(search.result, file)

    with open(lq_file, 'w') as file:
        wr = csv.writer(file, quoting=csv.QUOTE_ALL)
        wr.writerow(search.lower_quality)

    with open(os.path.join(dir, stats_file), 'w') as file:
        json.dump(search.stats, file)

    print(f'''\nSaved difPy results into folder '{dir}' and filenames:\n{result_file} \n{lq_file} \n{stats_file}''')