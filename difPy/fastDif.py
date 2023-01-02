from database import Database
from typing import Union
import os
import warnings
from utils import *
import numpy as np
import cv2
import skimage.color
import multiprocessing as mp
from dataclasses import dataclass
import queue
import json


"""
Fast implementation of the DifPy Library.
Features:
- Use GPU to accelerate the comparison
- Use Parallelization to use multicore CPUs
- Use of aspect rotation to ignore images with non-matching aspect ratio
- Use hash based deduplication to find duplicates with color grading
- Use of binary differentiation to detect hard file duplicates  # TODO for later
- Use of file names / zero difference to detect images which differ only in the metadata.  # TODO for later
"""

# TODO Implement process stop recovery.


@dataclass
class PreprocessArguments:
    # TODO different amounts for different colors.
    key: int
    in_path: str
    out_path: str

    size_x: int
    size_y: int

    compute_hash: bool
    store_thumb: bool

    amount: int

    @staticmethod
    def from_json(json_string: str):
        """
        Create a PreprocessArguments object from a json dict. (jsonified by the to_json method of the class)
        :param json_string: string to convert to object.
        :return:
        """
        obj_dict = json.loads(json_string)
        keys = obj_dict.keys()

        target_keys = ["in_path", "out_path", "size_x", "size_y", "compute_hash", "amount", "store_thumb", "key"]
        if not all(x in keys for x in target_keys):
            raise ValueError("Provided Json String doesn't contain the necessary keys.")

        return PreprocessArguments(in_path=obj_dict["in_path"],
                                   out_path=obj_dict["out_path"],
                                   size_x=obj_dict["size_x"],
                                   size_y=obj_dict["size_y"],
                                   compute_hash=obj_dict["compute_hash"],
                                   amount=obj_dict["amount"],
                                   store_thumb=obj_dict["store_thumb"],
                                   key=int(obj_dict["key"]))

    def to_dict(self):
        """
        Convert object to dict
        :return:
        """
        return {
            "in_path": self.in_path,
            "out_path": self.out_path,
            "size_x": self.size_x,
            "size_y": self.size_y,
            "compute_hash": self.compute_hash,
            "amount": self.amount,
            "store_thumb": self.store_thumb,
            "key": self.key
        }

    def to_json(self):
        """
        Convert an Object into json string.
        :return:
        """
        return json.dumps(self.to_dict())


@dataclass
class PreprocessResults:
    key: int
    in_path: str
    out_path: str

    success: bool

    original_x: int
    original_y: int

    hash_0: str
    hash_90: str
    hash_180: str
    hash_270: str

    error: str

    @staticmethod
    def from_json(json_string: str):
        """
        Create the PreprocessResults Object from a json dict (jsonified by the to_json method of the object)
        :param json_string: string to convert to object.
        :return:
        """
        obj_dict = json.loads(json_string)
        keys = obj_dict.keys()

        target_keys = ["in_path", "out_path", "original_x", "original_y", "hash_0", "hash_90", "hash_180", "hash_270",
                       "success", "error", "key"]
        if not all(x in keys for x in target_keys):
            raise ValueError("Provided Json String doesn't contain the necessary keys.")

        return PreprocessResults(in_path=obj_dict["in_path"],
                                 out_path=obj_dict["out_path"],
                                 original_x=obj_dict["original_x"],
                                 original_y=obj_dict["original_y"],
                                 success=obj_dict["success"],
                                 hash_0=obj_dict["hash_0"],
                                 hash_90=obj_dict["hash_90"],
                                 hash_180=obj_dict["hash_180"],
                                 hash_270=obj_dict["hash_270"],
                                 error=obj_dict["error"],
                                 key=int(obj_dict["key"]))

    @staticmethod
    def error_obj(in_path: str, out_path: str, error: str, key: int):
        return PreprocessResults(
            in_path=in_path,
            out_path=out_path,
            success=False,
            error=error,
            original_x=-1,
            original_y=-1,
            hash_0="<ERROR>",
            hash_90="<ERROR>",
            hash_180="<ERROR>",
            hash_270="<ERROR>",
            key=key,
        )

    @staticmethod
    def no_hash_init(in_path: str, out_path: str, original_x: int, original_y: int, key: int):
        return PreprocessResults(
            in_path=in_path,
            out_path=out_path,
            success=True,
            error="<EMPTY>",
            original_x=original_x,
            original_y=original_y,
            hash_0="<EMPTY>",
            hash_90="<EMPTY>",
            hash_180="<EMPTY>",
            hash_270="<EMPTY>",
            key=key,
        )

    def to_dict(self):
        """
        Convert object to dict representation
        :return:
        """
        return {
            "in_path": self.in_path,
            "out_path": self.out_path,
            "original_x": self.original_x,
            "original_y": self.original_y,
            "hash_0": self.hash_0,
            "hash_90": self.hash_90,
            "hash_180": self.hash_180,
            "hash_270": self.hash_270,
            "success": self.success,
            "error": self.error,
            "key": self.key,
        }

    def to_json(self):
        """
        Converts an object into json string.
        :return:
        """
        return json.dumps(self.to_dict())


def process_image_cuda(args: PreprocessArguments) -> PreprocessResults:
    # import cupy and use cupy instead of the
    # TODO Test if the process works correctly with cupy
    import cupy as cp

    return process_image(cp)


def process_image(args: PreprocessArguments, xp=np) -> PreprocessResults:
    """
    Perform the preprocessing on the image.
    :param args: arguments to parse
    :param xp: implementation of numpy. default is numpy but might also be cupy
    :return:
    """
    try:
        img = cv2.imdecode(xp.fromfile(args.in_path, dtype=xp.uint8), cv2.IMREAD_COLOR)

        if type(img) != xp.ndarray:
            return PreprocessResults.error_obj(in_path=args.in_path, out_path=args.out_path,
                                               error="Type Error, result of image decode was not np.ndarray",
                                               key=args.key)

        org_size_x, org_size_y, _ = xp.shape(img)

        # only get the image size for the scheduler to accelerate non-matching images.
        if not args.compute_hash and not args.store_thumb:
            return PreprocessResults.no_hash_init(in_path=args.in_path,
                                                  out_path=args.out_path,
                                                  original_x=org_size_x,
                                                  original_y=org_size_y,
                                                  key=args.key)

        img = img[..., 0:3]
        img = cv2.resize(img, dsize=(args.size_x, args.size_y), interpolation=cv2.INTER_CUBIC)

        if len(img.shape) == 2:
            img = skimage.color.gray2rgb(img)

        # write thumbnail
        if args.store_thumb:
            cv2.imwrite(args.out_path, img)

        # return here if the hashes are not computed
        if not args.compute_hash:
            return PreprocessResults.no_hash_init(in_path=args.in_path,
                                                  out_path=args.out_path,
                                                  original_x=org_size_x,
                                                  original_y=org_size_y,
                                                  key=args.key)

        # TODO move this part into a new function
        assert 8 > args.amount > -8, "amount exceeding range"

        p, e = os.path.splitext(args.out_path)
        path_0 = f"{p}_0{e}"
        path_90 = f"{p}_90{e}"
        path_180 = f"{p}_180{e}"
        path_270 = f"{p}_270{e}"

        # shift only if the amount is non-zero
        if args.amount > 0:
            xp.right_shift(img, args.amount)
        elif args.amount < 0:
            xp.left_shift(img, abs(args.amount))

        cv2.imwrite(path_0, img)

        # rot 90
        xp.rot90(img, k=1, axes=(0, 1))
        cv2.imwrite(path_90, img)

        # rot 180
        xp.rot90(img, k=1, axes=(0, 1))
        cv2.imwrite(path_180, img)

        # rot 270
        xp.rot90(img, k=1, axes=(0, 1))
        cv2.imwrite(path_270, img)

        # need to compute file hash since writing the
        hash_0 = hash_file(args.out_path)
        hash_90 = hash_file(path_90)
        hash_180 = hash_file(path_180)
        hash_270 = hash_file(path_270)

        # shouldn't be allowed to fail
        os.remove(path_0)
        os.remove(path_90)
        os.remove(path_180)
        os.remove(path_270)

        return PreprocessResults(
            in_path=args.in_path,
            out_path=args.out_path,
            success=True,
            error="<EMPTY>",
            original_x=org_size_x,
            original_y=org_size_y,
            hash_0=hash_0,
            hash_90=hash_90,
            hash_180=hash_180,
            hash_270=hash_270,
            key=args.key
        )

    except Exception as e:
        return PreprocessResults.error_obj(in_path=args.in_path, out_path=args.out_path,
                                           error=f"Error: {e}", key=args.key)


def parallel_resize(iq: mp.Queue, output: mp.Queue, identifier: int, try_cupy: bool) -> bool:
    """
    Parallel implementation of first loop iteration.
    :param iq: input queue containing arguments dict or
    :param output: output queue containing only json strings of obj
    :param identifier: id of running thread
    :param try_cupy: check if cupy is available and use cupy instead.
    :return: True, running was successful and no error encountered, otherwise exit without return or return False
    """
    timeout = 0

    # try to use cupy if it is indicated by arguments
    if try_cupy:
        try:
            import cupy
            cupy_avail = True
        except ImportError:
            cupy_avail = False

    # stay awake for 60s, otherwise kill
    while timeout < 60:
        try:
            args_str = iq.get(timeout=1)
        except queue.Empty:
            timeout += 1
            continue

        if args_str is None:
            print(f"{identifier:03} Terminating")
            break

        args = PreprocessArguments.from_json(args_str)
        timeout = 0

        if cupy_avail:
            result = process_image_cuda(args)
        else:
            result = process_image(args)
        print(f"{identifier:03}: Done with {os.path.basename(args.in_path)}")

        # Sending the result to the handler
        output.put(result.to_json())

    return True

class FastDifPy:
    p_db: str
    __p_root_dir_a: str
    __p_root_dir_b: Union[str, None]

    __thumb_dir_a: str
    __thumb_dir_b: Union[str, None]

    __thumbnail_size_x = 64
    __thumbnail_size_y = 64

    supported_file_types = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".gif", ".webp"}

    db: Database

    def __init__(self, directory_a: str, directory_b: str = None, test_db: bool = True):
        """
        Provide the directories to be searched. If a different implementation of the database is used,
        set the test_db to false.

        :param directory_a: first directory to search for differentiation.
        :param directory_b: second directory to compare against. Otherwise, comparison will be done against directory
        itself.
        :param test_db: Weather or not the code should test for the presence of the default sqlite database.
        """

        self.p_root_dir_b = directory_a
        self.p_root_dir_b = directory_b

        # proceed with the database if the default is used.
        if test_db:
            if not self.test_for_db():
                print("No matching database found. Creating new one.")
                self.db = Database(os.path.join(self.p_root_dir_a, "diff.db"))
                self.write_config()

    def test_for_db(self):
        """
        Test if the database is present in the current directory/ies. Directory A has priority.
        If a Database is found, the config is checked to make sure the paths match the current ones.

        :return: True -> Database connected and ready to use. False -> Database not found.
        """
        db_a = os.path.join(self.p_root_dir_a, "diff.db")
        dir_b = self.p_root_dir_b  # can be none
        db_b = os.path.join(dir_b, "diff.db")
        matching_config = False

        if os.path.exists(db_a):
            temp_db = Database(db_a)
            cfg = temp_db.get_config('main_config')

            # verify the config matches the call arguments (in case the computation was stopped during the
            # execution before)
            if cfg is not None:
                matching_config = cfg["directory_a"] == self.p_root_dir_a and cfg["directory_b"] == self.p_root_dir_b

                # return straight away in case the other directory is not set
                if matching_config and dir_b is None:
                    self.db = temp_db
                    return True

        if dir_b is not None and os.path.exists(db_b):
            temp_db = Database(db_b)
            cfg = temp_db.get_config('main_config')

            # verify the config matches the call arguments (in case the computation was stopped during the
            # execution before)
            if cfg is not None:
                temp_match = cfg["directory_a"] == self.p_root_dir_a and cfg["directory_b"] == self.p_root_dir_b

                if matching_config and temp_match:
                    raise Exception("Two matching configs found. Please remove one of the databases in one of the "
                                    "selected directories so the program can continue.")

                if temp_match:
                    self.db = temp_db
                    return True

        return False

    def get_progress_from_db(self):
        """
        Loads the progress state from the database.
        WARNING: The programm WILL NOT reindex the files. If you added files in the meantime, the files are NOT going
        compared against!
        :return:
        """

        # TODO get the progress from the database
        print("Not implemented yet")

    def write_config(self):
        """
        Write the initial config to the database.
        :return:
        """
        temp_config = {
            "directory_a": self.p_root_dir_a,
            "directory_b": self.p_root_dir_b
        }
        self.db.create_config(type_name="main_config", config=temp_config)

    # Perform two loops.
    # First loop:
    # - load the metadata / paths of the images i.e. (image size)
    # - If desired, compute the thumbnail of the image
    # - if desired compute the hash of the image

    # Second loop
    # - compress the images (if not thumbnails were calculated)
    #

    def index_the_dirs(self):
        # create the tables in the database
        self.db.create_directory_tables(secondary_folder=self.p_root_dir_b is not None)

        self.recursive_index(True)
        if self.p_root_dir_b is not None:
            self.recursive_index(False)

    def recursive_index(self, dir_a: bool = True, path: str = None, ignore_thumbnail: bool = True):
        """
        Recursively index the directories. This function is called by the index_the_dirs function.
        :param ignore_thumbnail: If any directory at any level, starting with .thumb should be ignored.
        :param dir_a: True -> Index dir A. False -> Index dir B
        :param path: The path to the current directory. This is used for recursion.
        :return:
        """

        # load the path to index from
        if path is None:
            if dir_a:
                path = self.p_root_dir_a
            else:
                path = self.p_root_dir_b

        for file_name in os.listdir(path):
            full_path = os.path.join(path, file_name)

            # Thumbnail directory is called .thumbnails
            if file_name.startswith(".thumb") and ignore_thumbnail:
                continue

            # for directories, continue the recursion
            if os.path.isdir(full_path):
                self.recursive_index(dir_a, full_path)

            if os.path.isfile(full_path):
                # check if the file is supported, then add it to the database
                if os.path.splitext(full_path)[1] in self.supported_file_types:
                    self.db.add_file(full_path, file_name, dir_a)

    def estimate_disk_usage(self):
        """
        Estimate the diskusage of the thumbnail directory given the compressed image size.
        :return:
        """
        dir_a_count = self.db.get_dir_count(True)
        dir_b_count = self.db.get_dir_count(False)

        byte_count_a = dir_a_count * self.__thumbnail_size_x * self.__thumbnail_size_y * 3
        byte_count_b = dir_b_count * self.__thumbnail_size_x * self.__thumbnail_size_y * 3

        target = max(len(self.p_root_dir_a), len(self.p_root_dir_b), len(self.p_root_dir_b) + len(self.p_root_dir_a))

        print(f"Estimated disk usage by {fill(str(len(self.p_root_dir_a)), target)}: " + h(byte_count_a, "B") + " bytes")
        print(f"Estimated disk usage by {fill(str(len(self.p_root_dir_b)), target)}: " + h(byte_count_b, "B") + " bytes")
        print(f"Estimated disk usage by {fill('the two dirs ', target)}: " + h(byte_count_b + byte_count_a,
                                                                               "B") + "bytes")

    def check_create_thumbnail_dir(self):
        """
        Create the thumbnail directories if they don't exist already.
        :return:
        """
        if not os.path.exists(self.thumb_dir_a):
            os.makedirs(self.thumb_dir_a)

        if self.thumb_dir_b is not None and not os.path.exists(self.__thumb_dir_b):
            os.makedirs(self.thumb_dir_b)

    def generate_thumbnail_path(self, key: int, filename: str, dir_a: bool):
        """
        Generate the thumbnail_path first tries to fetch the thumbnail name from the db if it exists already,
        otherwise generate a new name.

        :param key: key in the directory_x table
        :param filename: the name of the file with extension
        :param dir_a: if the file is located in directory a or b
        :return: the thumbnail path.
        """
        name = self.db.get_thumb_name(key, dir_a=dir_a)
        directory = self.thumb_dir_a if dir_a else self.__thumb_dir_b

        # return the name if it existed already
        if name is not None:
            return os.path.join(directory, name)

        name = self.db.generate_new_thumb_name(key, filename, dir_a=dir_a)
        return os.path.join(directory, name


    def first_loop_iteration(self, compute_thumbnails: bool = True, compute_hash: bool = False, amount: int = 4,
                             gpu_proc: int = 0, cpu_proc: int = 16):
        # store thumbnails if possible.
        if compute_hash:
            if amount == 0:
                print("WARNING: amount 0, only EXACT duplicates are detected like this.")

            if amount > 7 or amount < -7:
                raise ValueError("amount my only be in range [-7, 7]")

        # thumbnail are required to exist for both.
        if compute_thumbnails or compute_hash:
            self.check_create_thumbnail_dir()

        cpu_handles = []
        gpu_handles = []

        task_queue = mp.Queue(maxsize=(cpu_proc + gpu_proc) * 2)
        res_queue = mp.Queue()

        # prefill loop
        for i in range(cpu_proc + gpu_proc):
            task = self.db.get_next_to_process()

            # stop if there's nothing left to do.
            if task is None:
                break

            # generate a new argument
            arg = PreprocessArguments(
                amount=amount,
                key=task["key"],
                in_path=task["path"],
                out_path=self.generate_thumbnail_path(dir_a=task["dir_a"], filename=task["filename"], key=task["key"]),
                compute_hash=compute_hash,
                store_thumb=compute_thumbnails,
                size_x=self.thumbnail_size_x,
                size_y=self.__thumbnail_size_y,
            )

            task_queue.put(arg.to_json())


        # start processes for cpu
        for i in range(cpu_proc):
            p = mp.Process(target=parallel_resize, args=(task_queue, res_queue, i, False))
            p.start()
            cpu_handles.append(p)

        # start processes for gpu
        for i in range(cpu_proc, gpu_proc + cpu_proc):
            p = mp.Process(target=parallel_resize, args=(task_queue, res_queue, i, True))
            p.start()
            gpu_handles.append(i)

        # turn main loop ito handler and perform monitoring of the threads.


    def clean_up(self):
        # TODO remove the thumbnails
        # TODO remove database (if desired)
        print("Not implemented yet")

    @property
    def thumbnail_size_x(self):
        return self.__thumbnail_size_x

    @thumbnail_size_x.setter
    def thumbnail_size_x(self, value):
        if value < 0:
            raise ValueError("Thumbnail size must be positive")

        if value > 1000:
            warnings.warn("Thumbnail size is very large. Higher Accuracy will slow down the process and "
                          "increase storage usage.")
        self.__thumbnail_size_x = value

    @property
    def thumbnail_size_y(self):
        return self.__thumbnail_size_y

    @thumbnail_size_y.setter
    def thumbnail_size_y(self, value):
        if value < 0:
            raise ValueError("Thumbnail size must be positive")

        if value > 1000:
            warnings.warn("Thumbnail size is very large. Higher Accuracy will slow down the process and "
                          "increase storage usage.")
        self.__thumbnail_size_y = value

    @property
    def p_root_dir_a(self):
        return self.__p_root_dir_a

    @p_root_dir_a.setter
    def p_root_dir_a(self, value):
        if os.path.exists(value):
            self.__p_root_dir_a = value
            self.__thumb_dir_a = os.path.join(self.__p_root_dir_a, ".temp_thumbnails")

    @property
    def p_root_dir_b(self):
        return self.__p_root_dir_b

    @p_root_dir_b.setter
    def p_root_dir_b(self, value):
        if os.path.exists(value):
            self.__p_root_dir_b = value
            self.__thumb_dir_b = os.path.join(self.__p_root_dir_b, ".temp_thumbnails")

    @property
    def thumb_dir_a(self):
        return self.__thumb_dir_a

    @property
    def thumb_dir_b(self):
        return self.__thumb_dir_b
