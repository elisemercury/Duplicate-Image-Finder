'''
difPy - Python package for finding duplicate and similar images
2023 Elise Landman
https://github.com/elisemercury/Duplicate-Image-Finder
'''
import os
from pathlib import Path
import numpy as np

class delete:
    '''
    A class used to delete difPy objects.
    '''  
    def __init__(self, difpy_obj, silent_del=False):
        self.silent_del = _validate._silent_del(silent_del)
        print(difpy_obj.lower_quality)
        self.lower_quality = _validate._file_list(difpy_obj.lower_quality)
        self._main()
        
    def _main(self):
        # Function for deleting the lower quality images that were found after the search
        deleted_files = []
        if not self.silent_del:
            usr = input('Are you sure you want to delete all lower quality matched images? \n! This cannot be undone. (y/n)')
            if str(usr).lower() == 'y':
                for file in self.lower_quality:
                    print('\nDeletion in progress...', end='\r')
                    try:
                        os.remove(file)
                        deleted_files.append(file)
                    except:
                        print(f'Could not delete file: {file}', end='\r')       
            else:
                print('Deletion canceled.')
                return
        else:
            for file in self.lower_quality:
                print('\nDeletion in progress...', end='\r')
                try:
                    os.remove(file)
                    deleted_files.append(file)
                except:
                    print(f'Could not delete file: {file}', end='\r')
        print(f'Deleted {len(deleted_files)} file(s).')
        return deleted_files     

class move_to:
    '''
    A class used to move difPy objects.
    '''  
    def __init__(self, difpy_obj, destination_path):
        self.destination_path = _validate._move_to(destination_path)
        self.lower_quality = difpy_obj.lower_quality
        self.lower_quality = self._main()
        
    def _main(self):
        new_lower_quality = []
        for file in self.lower_quality:
            try:
                head, tail = os.path.split(file)
                os.replace(file, os.path.join(move_to, tail))
                new_lower_quality = np.append(new_lower_quality, str(Path(os.path.join(move_to, tail))))
            except:
                print(f'Could not move file: {file}', end='\r')            
        print(f'Moved {len(self.lower_quality)} files(s) to {str(Path(move_to))}')
        return new_lower_quality   

class _validate:
    '''
    A class used to validate action input parameters.
    '''    
    def _silent_del(silent_del):
        # Function that _validates the 'delete' and the 'silent_del' input parameter
        if not isinstance(silent_del, bool):
            raise Exception('Invalid value for "silent_del" parameter: must be of type BOOL.')
        return silent_del
    
    def _file_list(file_list):
        # Function that _validates the 'delete' and the 'silent_del' input parameter
        if not isinstance(file_list, list):
            raise Exception('Invalid value for "file_list" parameter: must be of type LIST.')
        return file_list
    
    def _move_to(move_to):
        # Function that _validates the 'move_to' input parameter
        if not isinstance(move_to, str):
            if not move_to == None:
                raise Exception('Invalid value for "move_to" parameter: must be of type str or "None"')
        else:
            if not os.path.exists(dir):
                try:
                    os.makedirs(dir)
                except:
                    raise Exception(f'Invalid value for "move_to" parameter: "{str(dir)}" does not exist.')
            elif not os.path.isdir(dir):
                raise ValueError(f'Invalid value for "move_to" parameter: "{str(dir)}" is not a directory.')
        return move_to