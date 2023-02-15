import datetime
import shutil
import time
from difPy.database import Database
import os
from typing import List, Tuple, Dict
from types import FunctionType
import warnings
from difPy.utils import *
import multiprocessing as mp
import threading as th
import queue
from difPy.datatransfer import *
from difPy.image_processor import ImageProcessing
from concurrent.futures import ProcessPoolExecutor

"""
Fast implementation of the DifPy Library.
Features:
- Use GPU to accelerate the comparison
- Use Parallelization to use multicore CPUs
- Use of aspect rotation to ignore images with non-matching aspect ratio
- Use hash based deduplication to find duplicates with color grading
"""


# TODO test cuda functionality
# TODO single processing handler
# TODO Reset Processing Class if the arguments are switched.


# ----------------------------------------------------------------------------------------------------------------------
# FEATURES
# ----------------------------------------------------------------------------------------------------------------------
# TODO Implement process stop recovery.
# TODO Range in which the aspects must lay for matching_aspect to trigger
# TODO Harakiri method. More reckless method.
# TODO Use of binary differentiation to detect hard file duplicates
# TODO  Use of file names / zero difference to detect images which differ only in the metadata.
# TODO keyboard shortcuts pyinput
# TODO different shift amounts for different colors.


def cpu_process_image(proc: ImageProcessing, args: PreprocessArguments) -> PreprocessResults:
    """
    Function to execute preprocessing with the ImageProcessing Class
    # TODO WARNING in docs that an error in the course of processing if it was not fatal, will be treated as fatal.

    :param proc: the ImageProcessing class to retain information (not really necessary currently)
    :param args: arguments loaded from the queue
    :return: PreprocessingResult
    """
    # update arguments and load image
    proc.update_preprocess_args(args=args)

    # check for error
    if proc.error != "":
        return proc.create_error_preprocess_result()

    # return here if only the aspect ratio is desired.
    if not args.compute_hash and not args.store_thumb:
        return proc.create_no_hash_preprocess_result()

    # resize image
    proc.resize_image(image_a=True)

    # storing image if desired.
    if args.store_thumb:
        proc.store_image(img_a=True)

    # for safety, returning with error here. It could be possible to continue even if an error
    # occurred while storing the file.
    if proc.error != "":
        return proc.create_error_preprocess_result()

    # return if no hash is desired.
    if not args.compute_hash:
        return proc.create_no_hash_preprocess_result()

    # compute hash
    proc.compute_img_hashes(img_a=True)

    # check for errors again
    if proc.error != "":
        return proc.create_error_preprocess_result()

    # full result return
    return proc.create_full_preprocess_result()


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
    cupy_avail = False
    if try_cupy:
        print("Cupy version currently not implemented")

    img_proc = ImageProcessing(identifier=identifier)

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

        result = cpu_process_image(img_proc, args)
        print(f"{identifier:03}: Done with {os.path.basename(args.in_path)}")

        # Sending the result to the handler
        output.put(result.to_json())

    return True


def parallel_compare(in_q: mp.Queue, out_q: mp.Queue, identifier: int, try_cupy: bool,
                     sc_size: bool = False, sc_hash: bool = False, debug: bool = False) -> bool:
    """
    Parallel implementation of first loop iteration.

    :param debug: adds more print statements to get an overview about the executing workers.
    :param in_q: input queue containing arguments dict or
    :param out_q: output queue containing only json strings of obj
    :param identifier: id of running thread
    :param try_cupy: check if cupy is available and use cupy instead.
    :param sc_size: Perform short_circuiting logic with image size
    :param sc_hash: Perform shirt_circuiting logic with image hashes.
    :return: True, running was successful and no error encountered, otherwise exit without return or return False
    """
    timeout = 0

    # try to use cupy if it is indicated by arguments
    cupy_avail = False
    if try_cupy:
        print("Cupy version currently not implemented")

    processor = ImageProcessing(identifier=identifier)
    # stay awake for 60s, otherwise kill
    while timeout < 60:
        try:
            args_str = in_q.get(timeout=1)
        except queue.Empty:
            timeout += 1
            continue

        if args_str is None:
            print(f"{identifier:03} Terminating")
            break

        args = CompareImageArguments.from_json(args_str)
        timeout = 0

        # short_circuiting
        result = ImageProcessing.short_circuit(args=args, sc_size=sc_size, sc_hash=sc_hash)
        if result is not None:
            assert type(result) is CompareImageResults, f"Unexpected Return Type of Short Circuiting function. \n" \
                                                        f"CompareImageResults expected, got {type(result).__name__}"

            if debug:
                print(f"{identifier:03}: Done with {os.path.basename(args.img_a)} and "
                      f"{os.path.basename(args.img_b)} - short circuiting")

            # Sending the result to the handler
            out_q.put(result.to_json())
            continue

        processor.update_compare_args(args)
        processor.compare_images()
        processor.store_plt_on_threshold()
        result = processor.create_compare_result()

        if debug:
            print(f"{identifier:03}: Done with {os.path.basename(args.img_a)} and {os.path.basename(args.img_b)}")

        # Sending the result to the handler
        out_q.put(result.to_json())

    return True


def find_best_image(args: Tuple[list, FunctionType]) -> Tuple[dict, list]:
    """
    Function which selects the best image out of a list. It is assumed that the images are all deemed to be duplicates.
    The comparator is a function taking two string arguments, representing two *absolute* filepaths.
    Because the comparison is only happening once, function must impose a *total order* on the files.

    --------------------------------------------------------------------------------------------------------------------

    If no function is provided, the default is file size:

    def simple_comp(fpa: str, fpb: str):
        return os.stat(fpa).st_size < os.stat(fpb).st_size

    :param args: The arguments as tuple. list: list of absolute filepaths, comparator: function to compare files with.
    :return: {"filename": <best image>, "location": <path to best image>}, list of the duplicates
    """
    filepaths = args[0]
    comparator = args[1]
    current_best = filepaths[0]

    # comparator if nothing is provided.
    def simple_comp(fpa: str, fpb: str):
        return os.stat(fpa).st_size < os.stat(fpb).st_size

    if comparator is None:
        comparator = simple_comp

    # get best image based on comparator
    for i in range(1,  len(filepaths)):
        if comparator(current_best, filepaths[i]):
            current_best = filepaths[i]

    result = {"filename": os.path.basename(current_best), "location": current_best, "duplicates": []}
    duplicates = []

    for fp in filepaths:
        if fp == current_best:
            continue
        duplicates.append(fp)

    return result, duplicates


class FastDifPy:
    p_db: str
    __p_root_dir_a: str
    __p_root_dir_b: Union[str, None]

    __thumb_dir_a: str
    __thumb_dir_b: Union[str, None]

    __thumbnail_size_x = 64
    __thumbnail_size_y = 64

    __similarity_threshold = 200

    __has_dir_b: bool = False

    supported_file_types = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".gif", ".webp"}

    db: Union[Database, None]

    # relative to child processes
    first_loop_in: mp.Queue = None  # the tasks sent to the child processes
    first_loop_out: mp.Queue = None  # the results coming from the child processes

    second_loop_in: Union[List[mp.Queue], mp.Queue] = None
    second_loop_out: mp.Queue = None

    second_loop_queue_status: Union[List[dict], dict] = None
    second_loop_base_a: bool = True

    # argument storage
    matching_hash: bool = False
    has_thumb_a: bool = False
    has_thumb_b: bool = False
    matching_aspect: bool = False
    make_diff_plots: bool = False
    plot_output_dir: str = None

    # multiprocessing handles
    cpu_handles = None
    gpu_handles = None

    less_optimized: bool = False

    def __init__(self, directory_a: str, directory_b: str = None, test_db: bool = True):
        """
        Provide the directories to be searched. If a different implementation of the database is used,
        set the test_db to false.

        :param directory_a: first directory to search for differentiation.
        :param directory_b: second directory to compare against. Otherwise, comparison will be done against directory
        itself.
        :param test_db: Test and create a sqlite db for the processing. Should be set to off, if a different
        implementation is used
        """

        if not os.path.isdir(directory_a):
            raise NotADirectoryError(f"{directory_a} is not a directory")

        if directory_b is not None and not os.path.isdir(directory_b):
            raise NotADirectoryError(f"{directory_b} is not a directory")

        directory_a = os.path.abspath(directory_a)
        directory_b = os.path.abspath(directory_b) if directory_b is not None else None

        # make sure the paths aren't subdirs of each other.
        if directory_b is not None:
            temp_a = directory_a + os.sep
            temp_b = directory_b + os.sep
            if temp_a.startswith(temp_b):
                raise ValueError(f"{directory_a} is a subdirectory of {directory_b}")
            elif temp_b.startswith(temp_a):
                raise ValueError(f"{directory_b} is a subdirectory of {directory_a}")

        self.p_root_dir_b = directory_b
        self.p_root_dir_a = directory_a

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
        db_b = os.path.join(dir_b, "diff.db") if self.has_dir_b else None
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
        WARNING: The program WILL NOT reindex the files. If you added files in the meantime, the files are NOT going
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

    def index_the_dirs(self):
        """
        List all the files in directory_a and possibly directory_b and store the paths and filenames in the temporary
        database.

        :return:
        """
        # create the tables in the database
        self.db.create_directory_tables()

        self.__recursive_index(True)
        if self.has_dir_b:
            self.__recursive_index(False)

    def __recursive_index(self, dir_a: bool = True, path: str = None, ignore_thumbnail: bool = True):
        """
        Recursively index the directories. This function is called by the index_the_dirs function.

        :param ignore_thumbnail: If any directory at any level, starting with .temp_thumb should be ignored.
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

            # Thumbnail directory is called .temp_thumbnails
            if file_name.startswith(".temp_thumb") and ignore_thumbnail:
                continue

            # for directories, continue the recursion
            if os.path.isdir(full_path):
                self.__recursive_index(dir_a, full_path)

            if os.path.isfile(full_path):
                # check if the file is supported, then add it to the database
                if os.path.splitext(full_path)[1] in self.supported_file_types:
                    self.db.add_file(full_path, file_name, dir_a)

    def estimate_disk_usage(self, print_results: bool = True) -> Tuple[int, int]:
        """
        Estimate the diskusage of the thumbnail directory given the compressed image size.

        :param print_results: print the results to console
        :return: byte_count_a, byte_count_b
        """
        dir_a_count = self.db.get_dir_count(True)
        dir_b_count = self.db.get_dir_count(False) if self.has_dir_b else 0

        byte_count_a = dir_a_count * self.__thumbnail_size_x * self.__thumbnail_size_y * 3
        byte_count_b = dir_b_count * self.__thumbnail_size_x * self.__thumbnail_size_y * 3

        dir_b = self.p_root_dir_b if self.has_dir_b else ""

        target = max(len(self.p_root_dir_a), len(dir_b), len('the two dirs '))

        if print_results:
            print(
                f"Estimated disk usage by {fill(self.p_root_dir_a, target)}: " + h(byte_count_a, "B") +
                " bytes")
            if self.has_dir_b:
                print(
                    f"Estimated disk usage by {fill(self.p_root_dir_b, target)}: " + h(byte_count_b, "B") +
                    " bytes")
                print(f"Estimated disk usage by {fill('the two dirs ', target)}: " +
                      h(byte_count_b + byte_count_a, "B") + "bytes")

        return byte_count_a, byte_count_b

    def check_create_thumbnail_dir(self):
        """
        Create the thumbnail directories if they don't exist already.

        :return:
        """
        if not os.path.exists(self.thumb_dir_a):
            os.makedirs(self.thumb_dir_a)

        if self.has_dir_b and not os.path.exists(self.thumb_dir_b):
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
        directory = self.thumb_dir_a if dir_a else self.thumb_dir_b

        # return the name if it existed already
        if name is not None:
            return os.path.join(directory, name[1])

        name = self.db.generate_new_thumb_name(key, filename, dir_a=dir_a)
        return os.path.join(directory, name)

    def first_loop_iteration(self, compute_thumbnails: bool = True, compute_hash: bool = False, amount: int = 4,
                             gpu_proc: int = 0, cpu_proc: int = None, purge: bool = True):
        """
        Perform the preprocessing step. I.e. compute hashes, get image sizes, resize the images and store the
        thumbnails.

        ----------------------------------------------------------------------------------------------------------------

        Hashing:
        After the image has been resized, the bits of each r, g and b value are shifted by the amount specified in the
        amount parameter. If the amount is greater than 0, the bytes are right shifted, if the amount is smaller than 0,
        the pixels are left shifted.

        ----------------------------------------------------------------------------------------------------------------

        The program doesn't support hdr image formats and only allocates one byte per channel per pixel. Consequently
        10bit images for example are not supported. They are down-converted. # TODO Verify!!!


        :param compute_thumbnails: Resize images and store them temporarily
        :param compute_hash: Compute hashes of the image
        :param amount: shift amount before hash
        :param gpu_proc: number of processes using gpu [not implemented]
        :param cpu_proc: number of cpu processes. Default number of system cores.
        :param purge: if the database should be purged before the loop runs.
        :return:
        """

        assert gpu_proc >= 0, "Number of GPU Processes needs to be greater than zero"
        if cpu_proc is None:
            cpu_proc = mp.cpu_count()

        if gpu_proc > 0:
            print("Currently not implemented, adding to cpu procs.")

        # store thumbnails if possible.
        if compute_hash:
            if amount == 0:
                print("WARNING: amount 0, only EXACT duplicates are detected like this.")

            if amount > 7 or amount < -7:
                raise ValueError("amount my only be in range [-7, 7]")

            self.db.create_hash_table(purge=purge)

        # thumbnail are required to exist for both.
        if compute_thumbnails or compute_hash:
            self.db.create_thumb_table(secondary_folder=self.has_dir_b)
            self.check_create_thumbnail_dir()

        self.cpu_handles = []
        self.gpu_handles = []

        self.first_loop_in = mp.Queue()
        self.first_loop_out = mp.Queue()

        # prefill loop
        for i in range(cpu_proc + gpu_proc):
            arg = self.__generate_first_loop_obj(amount=amount, compute_hash=compute_hash,
                                                 compute_thumbnails=compute_thumbnails)

            # stop if there's nothing left to do.
            if arg is None:
                break

            self.first_loop_in.put(arg.to_json())

        # start processes for cpu
        for i in range(cpu_proc):
            p = mp.Process(target=parallel_resize, args=(self.first_loop_in, self.first_loop_out, i, False))
            p.start()
            self.cpu_handles.append(p)

        # start processes for gpu
        for i in range(cpu_proc, gpu_proc + cpu_proc):
            p = mp.Process(target=parallel_resize, args=(self.first_loop_in, self.first_loop_out, i, True))
            p.start()
            self.gpu_handles.append(p)

        # turn main loop into handler and perform monitoring of the threads.
        run = True
        none_counter = 0
        timeout = 0

        # handle the running state of the loop
        while run:
            if self.handle_result_of_first_loop(self.first_loop_out, compute_hash):
                arg = self.__generate_first_loop_obj(amount, compute_hash, compute_thumbnails)

                # if there's no task left, stop the loop.
                if arg is None:
                    none_counter += 1
                    self.first_loop_in.put(None)

                else:
                    self.first_loop_in.put(arg.to_json())
                    timeout = 0
            else:
                time.sleep(1)
                timeout += 1

            # if this point is reached, all processes should be done and the queues empty.
            if none_counter >= cpu_proc + gpu_proc:
                run = False

            # at this point we should have been idling for 60s
            if timeout > 60:
                print("Timeout reached, stopping.")
                run = False

        self.send_termination_signal(first_loop=True)

        counter = 0
        # try to handle any remaining results that are in the queue.
        while counter < 5:
            if not self.handle_result_of_first_loop(self.first_loop_out, compute_hash):
                counter += 1
                continue

            counter = 0

        self.join_all_children()
        assert self.first_loop_out.empty(), f"Result queue is not empty after all processes have been killed.\n " \
                                            f"Remaining: {self.first_loop_out.qsize()}"
        print("All Images have been preprocessed.")

    def __generate_first_loop_obj(self, amount: int, compute_hash: bool, compute_thumbnails: bool) \
            -> Union[PreprocessArguments, None]:
        """
        Short wrapper function which creates the PreprocessingArguments and updates the DB.

        :param amount: shift amount for hash
        :param compute_hash: if hash is to be computed
        :param compute_thumbnails: if thumbnail is to be computed and stored
        :return: PreprocessingArguments (on success), None if nothing was found.
        """
        task = self.db.get_next_to_process()

        # if there's no task left, stop the loop.
        if task is None:
            return None

        # generate a new argument
        arg = PreprocessArguments(
            amount=amount,
            key=task["key"],
            in_path=task["path"],
            out_path=self.generate_thumbnail_path(dir_a=task["dir_a"], filename=task["filename"],
                                                  key=task["key"]),
            compute_hash=compute_hash,
            store_thumb=compute_thumbnails,
            size_x=self.thumbnail_size_x,
            size_y=self.thumbnail_size_y,
        )
        self.db.mark_processing(task)

        self.first_loop_in.put(arg.to_json())

        return arg

    def handle_result_of_first_loop(self, res_q: mp.Queue, compute_hash: bool) -> bool:
        """
        Dequeues a result of the first loop results queue and updates the database accordingly.

        :param res_q: results queue
        :param compute_hash: if the hash was computed
        :return: if a result was handled.
        """
        # retrieve the result from the queue
        try:
            res = res_q.get(timeout=1.0)
        except queue.Empty:
            return False

        # sanitize result
        assert type(res) is str, "Result is not a string"
        result_obj = PreprocessResults.from_json(res)

        # Handle the case when an error occurred.
        if not result_obj.success:
            self.db.update_dir_error(key=result_obj.key, msg=result_obj.error)
            return True

        # store the hash if computed
        if compute_hash:
            # Drop hashes if they are only partly computed.
            if not self.db.has_all_hashes(dir_a=result_obj.dir_a, dir_key=result_obj.key):
                self.db.del_all_hashes(dir_a=result_obj.dir_a, dir_key=result_obj.key)

            # Store all hashes
            self.db.insert_hash(dir_a=result_obj.dir_a, dir_key=result_obj.key, file_hash=result_obj.hash_0,
                                rotation=0)
            self.db.insert_hash(dir_a=result_obj.dir_a, dir_key=result_obj.key, file_hash=result_obj.hash_90,
                                rotation=90)
            self.db.insert_hash(dir_a=result_obj.dir_a, dir_key=result_obj.key, file_hash=result_obj.hash_180,
                                rotation=180)
            self.db.insert_hash(dir_a=result_obj.dir_a, dir_key=result_obj.key, file_hash=result_obj.hash_270,
                                rotation=270)

        # mark file as processed only if the other data was inserted.
        self.db.update_dir_success(key=result_obj.key, dir_a=result_obj.dir_a, px=result_obj.original_x,
                                   py=result_obj.original_y)

        # to be sure commit here.
        self.db.con.commit()
        return True

    def clean_up(self, thumbs: bool = True, db: bool = True):
        """
        Remove thumbnails and db.

        :param thumbs: Delete Thumbnail directories
        :param db: Delete Database
        :return:
        """
        if thumbs:
            print("Deleting Thumbnails")
            try:
                shutil.rmtree(self.thumb_dir_a)
                print(f"Deleted {self.thumb_dir_a}")
            except FileNotFoundError:
                pass
            try:
                shutil.rmtree(self.thumb_dir_b)
                print(f"Deleted {self.thumb_dir_b}")
            except FileNotFoundError:
                pass

        if db:
            self.db.disconnect()
            self.db = None
            os.remove(self.db.path)
            print("Deleted temporary database")

    def create_plot_dir(self, diff_location: str, purge: bool = False):
        """
        Verifies the provided directory, creates if it doesn't exist.
        Initializes the Database for plot names as well.

        :param diff_location: path to plot where the plots are to be saved
        :param purge: purge the plot database before running.
        :return:
        """
        if diff_location is None:
            raise ValueError("If plots are to be generated, an output folder needs to be specified.")
        if not os.path.isdir(diff_location):
            raise ValueError("Plot location doesn't specify a valid directory path")

        if not os.path.exists(diff_location):
            os.makedirs(diff_location)

        self.plot_output_dir = diff_location
        self.db.create_plot_table(purge=purge)

    # TODO matching hash
    def second_loop_iteration(self, only_matching_aspect: bool = False, only_matching_hash: bool = False,
                              make_diff_plots: bool = False, similarity_threshold: float = 200.0, gpu_proc: int = 0,
                              cpu_proc: int = None, diff_location: str = None):
        """
        Similarity old values: high - 0.15, medium 200, low 1000

        :param only_matching_aspect: The images must match precisely in their size (in px)
        :param only_matching_hash: The images must have at least one matching hash.
        :param make_diff_plots: If the images which are duplicates should be plotted.
        :param similarity_threshold: The mean square average between pictures for them to be considered identical.
        :param gpu_proc: number of gpu processes. (Currently not implemented)
        :param cpu_proc: number of cpu processes. Default number of cpus on the system.
        :param diff_location: Where the plots should be stored (needs to be provided if make_diff_plots is true)
        :return:
        """
        assert gpu_proc >= 0, "Number of GPU Processes needs to be greater than zero"
        if cpu_proc is None:
            cpu_proc = mp.cpu_count()

        # storing arguments in attributes to reduce number of args of function
        self.matching_aspect = only_matching_aspect
        self.make_diff_plots = make_diff_plots
        self.matching_hash = only_matching_hash

        self.has_thumb_a = self.db.test_thumb_table_existence(dir_a=True)
        self.has_thumb_b = self.db.test_thumb_table_existence(dir_a=False)

        if make_diff_plots:
            self.create_plot_dir(diff_location=diff_location)

            if type(similarity_threshold) is int:
                similarity_threshold = float(similarity_threshold)

            if similarity_threshold < 0:
                raise ValueError("Similarity needs to be greater than 0")

        self.similarity_threshold = similarity_threshold

        self.cpu_handles = []
        self.gpu_handles = []

        # create queues
        self.second_loop_out = mp.Queue()
        self.second_loop_in = mp.Queue()

        if not self.less_optimized:
            self.second_loop_in = [mp.Queue() for _ in range(cpu_proc + gpu_proc)]
            child_args = [(self.second_loop_in[i], self.second_loop_out, i, False if i < cpu_proc else True)
                          for i in range(gpu_proc + cpu_proc)]
        else:
            child_args = [(self.second_loop_in, self.second_loop_out, i, False if i < cpu_proc else True)
                          for i in range(gpu_proc + cpu_proc)]

        self.db.create_dif_table()

        # prefill
        self.__init_queues(procs=gpu_proc + cpu_proc)

        # starting all processes
        for i in range(cpu_proc):
            p = mp.Process(target=parallel_compare, args=child_args[i])
            p.start()
            self.cpu_handles.append(p)

        for i in range(cpu_proc, cpu_proc + gpu_proc):
            p = mp.Process(target=parallel_resize, args=child_args[i])
            p.start()
            self.gpu_handles.append(p)

        done = False
        count = 0
        # update everything
        while not done:
            # update the queues and store if there are more tasks to process
            current_count = self.update_queues()
            count += current_count
            print(f"Number of Processed Images: {count}")

            if current_count == 0:
                print("Dequeued 0 elements, stopping")
                done = True

            # exit the while loop if all children have exited.
            _, _, _, all_exited = self.check_children(cpu=cpu_proc > 0, gpu=gpu_proc > 0)
            if all_exited:
                print("All Exited")
                done = True

        # check if it was the children's fault
        _, all_errored, _, _ = self.check_children(cpu=cpu_proc > 0, gpu=gpu_proc > 0)

        if all_errored:
            raise RuntimeError("All child processes exited with an Error")

        self.join_all_children()
        print("All child processes terminated")

        # handle last results:
        self.handle_results_second_queue()

        # check if the tasks were empty.
        assert not self.handle_results_second_queue(), "Existed without having run out of tasks and without all " \
                                                       "processes having stopped."

        self.db.con.commit()
        print("Data should be committed")

    def update_queues(self):
        results = self.__refill_queues()
        return self.handle_results_second_queue(results)

    def __refill_queues(self) -> Union[int, None]:
        """
        Call to either the optimized or non optimized filler.

        :return:
        """
        # testing if the
        if type(self.second_loop_queue_status) is dict:
            return self.__refill_queues_small_non_optimized()

        assert type(self.second_loop_queue_status) is list, f"Unexpected type of second_loop_queue_status: " \
                                                            f"{type(self.second_loop_queue_status).__name__}, " \
                                                            f"valid are list and dict"

        return self.__refill_queues_optimized()

    def __refill_queues_optimized(self):
        """
        Performs the optimized filling of the queues.

        :return:
        """
        inserted = 0
        for p in range(len(self.second_loop_in)):
            # fetch possible candidates for the row.
            row_a, row_b = self.__fetch_rows(p=p)

            # if the rows are empty => Nothing left to do, skip updating for this process
            if len(row_a) == 0 and len(row_b) == 0:
                self.second_loop_in[p].put(None)
                continue

            try:
                inserted_count = 100 - self.second_loop_in[p].qsize()

            # exception can occur on Unix Systems like MacOS because they don't implement sem_getvalue()
            # docs: https://docs.python.org/3/library/multiprocessing.html#multiprocessing.Queue
            except NotImplementedError:
                inserted_count = 100

            not_full = True
            iterations = 0
            while not_full:
                # break if the queue is full
                if self.second_loop_in[p].full():
                    break

                if self.second_loop_base_a:
                    for i in range(len(row_b)):
                        insertion_success = self.schedule_pair(row_a=self.second_loop_queue_status[p]["row_a"],
                                                               row_b=row_b[i], queue_index=p)
                        inserted_count -= int(insertion_success)
                        inserted += int(insertion_success)

                else:
                    for i in range(len(row_a)):
                        insertion_success = self.schedule_pair(row_a=row_a[i],
                                                               row_b=self.second_loop_queue_status[p]["row_b"],
                                                               queue_index=p)
                        inserted_count -= int(insertion_success)
                        inserted += int(insertion_success)

                # print(f"Row lengths: row_a {len(row_a)}, row_b {len(row_b)}, iteration {iterations}")
                iterations += 1

                # update last key
                if self.has_dir_b:
                    if not self.second_loop_base_a:
                        self.second_loop_queue_status[p]["last_key"] = row_a[-1]["key"]
                    else:
                        self.second_loop_queue_status[p]["last_key"] = row_b[-1]["key"]
                else:
                    self.second_loop_queue_status[p]["last_key"] = row_b[-1]["key"]

                row_a, row_b = self.__fetch_rows(p=p)

                # try to increment key. If the increment method returns False, then no more keys are available, so
                # stop trying to add more to the queue
                if len(row_a) == 0 and len(row_b) == 0:
                    # we don't have any images left to process.
                    if not self.__increment_fixed_image(p=p):
                        break

                    row_a, row_b = self.__fetch_rows(p=p)

                    # case when we are at the last image (which can only be compared against itself,
                    # ergo nothing to do)
                    if len(row_a) == 0 and len(row_b) == 0:
                        print("End of Images Reached")
                        break

                if inserted_count <= 0:
                    not_full = False

        return inserted if inserted > 0 else None

    def __refill_queues_small_non_optimized(self, init: bool = False) -> Union[int, None]:
        """
        Refill the queues with the non optimized algorithm which just stupidly goes along.

        :param init: if init, start all loops from 0 and initialize the status to dict
        :return: number of images inserted into queues.
        """
        last_a = None
        last_b = None

        if not init:
            last_a = self.second_loop_queue_status["last_a"]
            last_b = self.second_loop_queue_status["last_b"]

        # initialize loop vars
        procs = len(self.cpu_handles) + len(self.gpu_handles)
        queue_index = 0

        add_count = 0

        start_a = 0
        start_b = 0

        # things that can happen independently of b
        rows_a = self.db.fetch_many_after_key(directory_a=True, count=max(procs, 100))
        rows_b = rows_a

        # get start index of constant rows_a
        if not init:
            # cannot be issue with last_a being None since for that init should be true which it cannot here.
            for i in range(len(rows_a)):
                if rows_a[i]["key"] == last_a:
                    start_a = i

        # We have a dir_b, replace rows_b with actual rows form that table
        if self.has_dir_b:
            # fetching rows from table b
            rows_b = self.db.fetch_many_after_key(directory_a=False, count=max(procs, 100))

        # get start index
        if not init:
            for i in range(len(rows_b)):
                if rows_b[i]["key"] == last_b:
                    start_b = i

            # check if we have processed every entry. if so, return False, since we have not added anything to the
            # queues.
            if start_a == len(rows_a) - 1 and start_b == len(rows_b) - 1:
                return 0

        # since the number of entries is small, we can just perform a basic packaged for loop.
        for i in range(start_a, len(rows_a)):
            if i != start_a:
                start_b = int(self.has_dir_b) * (i + 1)  # i + 1 if not dir b, else 0

            for j in range(start_b, len(rows_a)):
                # All queues full, no need to continue
                if self.second_loop_in[queue_index].full():
                    break

                row_a = rows_a[i]
                row_b = rows_b[j]

                if self.schedule_pair(row_a=row_a, row_b=row_b, queue_index=queue_index):
                    # update the remaining loop variables
                    queue_index = (queue_index + 1) % procs
                    add_count += 1

                last_a = row_a["key"]
                last_b = row_b["key"]

        # store the current indices to be sure. The update loop function would trigger and throw the remaining
        # stuff out.
        self.second_loop_queue_status = {"last_a": last_a, "last_b": last_b}
        return add_count if add_count > 0 else None

    def __refill_queues_non_optimized(self, init: bool = False) -> Union[int, None]:
        """
        Refilling queues without the load optimized algorithm.

        :param init: Create new status, and initialize the dict
        :return: number of images inserted into queues.
        """
        assert self.less_optimized, "This functions needs to be called in the less_optimized mode since it assumes " \
                                    "that the attribute second_loop_in is of type mp.Queue and not List[mp.Queue]"
        # initialize loop vars
        procs = len(self.cpu_handles) + len(self.gpu_handles)

        add_count = 0
        current_count = 0

        last_a = None
        last_b = None

        if not init:
            last_a = self.second_loop_queue_status["last_a"]
            last_b = self.second_loop_queue_status["last_b"]

        if not init:
            current_a = self.db.fetch_one_key(key=last_a, directory_a=True)
            next_a = self.db.fetch_many_after_key(directory_a=True, starting=last_a, count=1)
            if len(next_a) == 0:
                next_a = None
        else:
            # Case of init
            rows = self.db.fetch_many_after_key(directory_a=True, starting=last_a, count=2)
            if len(rows) == 0:
                raise ValueError("No Rows in Directory A Table")

            elif len(rows) == 1:
                current_a = rows[0]
                next_a = None

            else:
                current_a = rows[0]
                next_a = rows[1]

        while add_count < procs * 100:

            # fetch the rows for the next queue
            rows_b = self.db.fetch_many_after_key(directory_a=not self.__has_dir_b, starting=last_b, count=100 * procs)

            # end reached. increment the indexes
            if len(rows_b) == 0:
                # We have reached the end.
                if next_a is None:
                    self.second_loop_queue_status = {"last_a": last_a, "last_b": last_b}
                    return add_count if add_count > 0 else None

                # increment the variables.
                current_a = next_a
                last_a = current_a["key"]
                rows = self.db.fetch_many_after_key(directory_a=True, starting=last_a, count=1)

                # resetting the next rows
                if len(rows) == 0:
                    next_a = None
                else:
                    next_a = rows[0]

                last_b = None

                # updating the last_b bc we can save us some effort if we don't compute the all to all but the triangle
                # matrix.
                if not self.has_dir_b:
                    last_b = last_a

                # We go back to the beginning just for good measure.
                continue

            # scheduling the rows
            for i in range(len(rows_b)):
                row = rows_b[i]

                if self.second_loop_in.full():
                    if i != 0:
                        # updating the last_b entry
                        last_b = rows_b[i - 1]["key"]

                    current_count = 0
                    continue

                success = self.schedule_pair(row_a=current_a, row_b=row, queue_index=None)
                current_count += int(success)
                add_count += int(success)

                # limit reached
                if current_count >= 100:
                    if i != 0:
                        # updating the last_b entry
                        last_b = rows_b[i - 1]["key"]

                    current_count = 0
                    continue

            last_b = rows_b[-1]["key"]

        self.second_loop_queue_status = {"last_a": last_a, "last_b": last_b}
        return add_count if add_count > 0 else None

    def __init_queues(self, procs: int):
        """
        Initialize the state describing variables as well as the queues for the second loop.

        :param procs: number of processes that are running
        :return:
        """
        # from a fetch the first set of images
        rows = self.db.fetch_many_after_key(directory_a=True, count=procs)
        self.second_loop_base_a = True

        # check if folder a has enough, so we can iterate using the files as fixed during an iteration and then switch
        # the file.
        if len(rows) < procs:
            if self.has_dir_b:

                # trying to use the directory b as a fixed directory
                rows = self.db.fetch_many_after_key(directory_a=False, count=procs)
                if len(rows) < procs:
                    self.__refill_queues_small_non_optimized(init=True)
                    return
                else:
                    self.second_loop_base_a = False
            else:
                self.__refill_queues_small_non_optimized(init=True)
                return

        # we are using less optimized, so we are going straight for the not optimized algorithm.
        if self.less_optimized:
            self.__refill_queues_non_optimized(init=True)
            return

        # populating the files of the second loop.
        self.second_loop_queue_status = []

        if self.second_loop_base_a:
            for row in rows:
                temp = {"row_a": row, "last_key": None if self.has_dir_b else row["key"]}

                self.second_loop_queue_status.append(temp)
        else:
            for row in rows:
                temp = {"row_b": row, "last_key": None}

                self.second_loop_queue_status.append(temp)

        self.__refill_queues_optimized()

    def __increment_fixed_image(self, p: int):
        """
        Given a process p, it searches for the next 'row' in the matching matrix to find the next key to keep constant
        for the process p

        :param p: index of process spec in self.second_loop_queue_status
        :return: True -> free image found, False, -> no new image found.
        """
        # TODO implement smart algorithm to find next image for the process that is now done.
        next_key = 0

        # get the limit for the next key
        for i in range(len(self.second_loop_queue_status)):
            if self.has_dir_b:
                if not self.second_loop_base_a:
                    next_key = max(self.second_loop_queue_status[i]["row_b"]["key"], next_key)
                    continue

            next_key = max(self.second_loop_queue_status[i]["row_a"]["key"], next_key)

        # process case, when we're looking to move the dir_b
        if self.has_dir_b:
            if not self.second_loop_base_a:
                rows = self.db.fetch_many_after_key(directory_a=False, starting=next_key, count=1)

                # no completely unprocessed key found
                if len(rows) == 0:
                    if not self.second_loop_in[p].full():
                        self.second_loop_in[p].put(None)
                    return False

                # update the dict
                self.second_loop_queue_status[p] = {"row_b": rows[0], "last_key": None}
                return True

        rows = self.db.fetch_many_after_key(directory_a=True, starting=next_key, count=1)

        # no completely unprocessed key found
        if len(rows) == 0:
            if not self.second_loop_in[p].full():
                self.second_loop_in[p].put(None)
            return False

        # update the dict
        self.second_loop_queue_status[p] = {"row_a": rows[0], "last_key": rows[0]["key"]}
        return True

    def __fetch_rows(self, p: int, count: int = 100) -> Tuple[list, list]:
        """
        Fetch the next up to 100 rows for the ingest process into the children.

        :param p: Index of the process
        :return:
        """
        row_a = []
        row_b = []
        assert type(self.second_loop_queue_status) is list, "__fetch_rows called with not_optimized process"

        # we have a directory b
        if self.has_dir_b:

            # we don't keep the images of dir_a fixed but the ones of dir_b
            if not self.second_loop_base_a:
                row_a = self.db.fetch_many_after_key(directory_a=True, count=count,
                                                     starting=self.second_loop_queue_status[p]["last_key"])
            # we keep the images of dir a fixed
            else:
                row_b = self.db.fetch_many_after_key(directory_a=False, count=count,
                                                     starting=self.second_loop_queue_status[p]["last_key"])
        # we don't have a directory b
        else:
            row_b = self.db.fetch_many_after_key(directory_a=True, count=count,
                                                 starting=self.second_loop_queue_status[p]["last_key"])
        return row_a, row_b

    def schedule_pair(self, row_a: dict, row_b: dict, queue_index: Union[None, int]):
        """
        Given two rows from the database, performs the checks necessary to schedule them. If they pass, send them to the
        respective queue.

        :param row_a: first row (from dir_a)
        :param row_b: second row (form dir_a or dir_b)
        :param queue_index: index of the queue to insert into.
        :return:
        """
        thumb_a_path = None
        thumb_b_path = None

        if self.has_dir_b:
            if self.has_thumb_a:
                thumb_a_path = self.get_thumb_path_from_db(key=row_a["key"], dir_a=True)
            if self.has_thumb_b:
                thumb_b_path = self.get_thumb_path_from_db(key=row_b["key"], dir_a=False)

        else:
            # all to all one dir
            if self.has_thumb_a:
                thumb_a_path = self.get_thumb_path_from_db(key=row_a["key"], dir_a=True)
                thumb_b_path = self.get_thumb_path_from_db(key=row_b["key"], dir_a=True)

        # performing match if desired
        if self.matching_aspect:
            if not self.match_aspect(row_a=row_a, row_b=row_b):
                return False

        # Aspect matches => Create Task object and send to process
        arg = CompareImageArguments(
            img_a=row_a["path"],
            img_b=row_b["path"],
            thumb_a=thumb_a_path,
            thumb_b=thumb_b_path,
            key_a=row_a["key"],
            key_b=row_b["key"],
            store_path=self.create_plt_name(key_a=row_a["key"], key_b=row_b["key"]),
            store_compare=self.make_diff_plots,
            compare_threshold=self.similarity_threshold,
            size_x=self.thumbnail_size_x,
            size_y=self.thumbnail_size_y,
            is_dir_b=self.has_dir_b
        )

        # send task to process
        if not self.less_optimized:
            self.second_loop_in[queue_index].put(arg.to_json())
        else:
            self.second_loop_in.put(arg.to_json())
        return True

    def create_plt_name(self, key_a: int, key_b: int) -> Union[None, str]:
        """
        Small function to create a fully qualified path to store the plots.

        :param key_a: key if the first image
        :param key_b: key of the second image
        :return: path to the plot or None
        """
        if not self.make_diff_plots:
            return None

        nm = self.db.make_plot_name(key_a=key_a, key_b=key_b)
        return os.path.join(self.plot_output_dir, nm)

    @staticmethod
    def match_aspect(row_a: dict, row_b: dict):
        """
        Match the result of two select queries with dict wrapping and make sure the aspect ratio matches at all.

        :param row_a: first dict of row
        :param row_b: second dict of row
        :return:
        """
        if row_a["px"] == row_b["px"] and row_a["py"] == row_b["py"]:
            return True
        elif row_a["px"] == row_b["py"] and row_a["py"] == row_b["px"]:
            return True
        return False

    def handle_results_second_queue(self, max_number: int = None) -> int:
        """
        Dequeue up to max_number of entries of the result queue of the second loop and insert the results into the
        database.

        :param max_number: maximum number of elements to dequeue, if None, dequeue until queue is empty.
        :return: -> Number actually dequeued elements
        """
        # TODO test for existence (for stop recovery)
        if max_number is None:
            number_dequeues = 0

            while True:
                if not self.__process_one_second_result():
                    return number_dequeues

                number_dequeues += 1

        # we have a max_number
        for i in range(max_number):
            if not self.__process_one_second_result():
                return i

        return max_number

    def __process_one_second_result(self) -> bool:
        """
        Perform dequeue of one element of the second process results queue. Insert the result into the database
        subsequently.

        :return: True -> inserted one element, False, timeout reached for fetching the next element.
        (Useful to prevent infinite loops)
        """
        try:
            res = self.second_loop_out.get(timeout=0.1)
        except queue.Empty:
            return False

        assert type(res) is str, "Result of comparison was not string"
        res_obj = CompareImageResults.from_json(res)

        # store in database
        if res_obj.success:
            self.db.insert_dif_success(key_a=res_obj.key_a, key_b=res_obj.key_b, dif=res_obj.min_avg_diff,
                                       b_dir_b=res_obj.is_dir_b)
        else:
            self.db.insert_dif_error(key_a=res_obj.key_a, key_b=res_obj.key_b, error=res_obj.error,
                                     b_dir_b=res_obj.is_dir_b)
        return True

    def send_termination_signal(self, first_loop: bool = False):
        """
        Sends None in the queues to the child processes, which is the termination signal for them.

        :param first_loop: if the termination signal needs to be sent to the children of the first or the second loop
        :return:
        """
        if first_loop:
            for i in range((len(self.cpu_handles) + len(self.gpu_handles)) * 4):
                self.first_loop_in.put(None)

            return
        for q in self.second_loop_in:
            [q.put(None) for _ in range(4)]

    def join_all_children(self):
        """
        Check the results of all spawned processes and verify they produced a True as a result ergo, they computed
        successfully.

        :return:
        """
        cpu_proc = len(self.cpu_handles)

        # all processes should be done now, iterating through and killing them if they're still alive.
        for i in range(len(self.cpu_handles)):
            p = self.cpu_handles[i]
            try:
                print(f"Trying to join process {i} Process Alive State is {p.is_alive()}")
                p.join(1)
                if p.is_alive():
                    print(f"Process {i} timed out. Alive state: {p.is_alive()}; killing it.")
                    p.kill()
            except TimeoutError:
                print(f"Process {i} timed out. Alive state: {p.is_alive()}; killing it.")
                p.kill()

        for i in range(len(self.gpu_handles)):
            p = self.gpu_handles[i]
            try:
                print(f"Trying to join process {i + cpu_proc} Process State is {p.is_alive()}")
                p.join(1)
                if p.is_alive():
                    print(f"Process {i} timed out. Alive state: {p.is_alive()}; killing it.")
                    p.kill()
            except TimeoutError:
                print(f"Process {i + cpu_proc} timed out. Alive state: {p.is_alive()}; killing it.")
                p.kill()

    def check_children(self, gpu: bool = False, cpu: bool = False):
        """
        Iterator over specified child processes and verify if any or all exited and produced an error.

        If nothing is selected, teh default is ,
        all_error is true,
        all_exited is true,
        error is false and
        exited is false.

        :param gpu: Test the gpu processes
        :param cpu: Test the cpu processes
        :return: error, all_error, exited, all_exited
        """
        # error, all_error, exited, all_exited
        error = False
        all_error = True
        exited = False
        all_exited = True

        # info, results can be fetched twice
        # check on the gpu tasks
        if gpu:
            error, all_error, exited, all_exited = self.check_processes(self.gpu_handles)

        if cpu:
            er, a_er, ex, a_ex = self.check_processes(self.cpu_handles)
            error = error or er
            all_error = all_error and a_er
            exited = exited or ex
            all_exited = all_exited and a_ex

        return error, all_error, exited, all_exited

    @staticmethod
    def check_processes(processes: List[mp.Process]) -> Tuple[bool, bool, bool, bool]:
        """
        Given a list of Futures, check for errors and if they are done.

        :param processes: List of futures to check
        :return: exited, all_exited
        """
        exited = False
        all_exited = True
        error = False
        all_error = False

        for p in processes:
            # if it is running, it has not exited and not errored
            if not p.is_alive():
                e = p.exitcode

                if e is not None:
                    if e != 0:
                        error = True
                    else:
                        all_error = False

                else:
                    print("WARNING: process is not alive but no exit code available")

            else:
                all_error = False
                all_exited = False

        return error, all_error, exited, all_exited

    def get_thumb_path_from_db(self, key: int, dir_a: bool) -> Union[None, str]:
        """
        Get a new thumbnail name from the database. Combine it with the specified path from this object.

        :param key: key in directory table
        :param dir_a: if the file is in directory a
        :return: thumbnail path or None
        """
        thumb_name = self.db.get_thumb_name(key=key, dir_a=dir_a)

        # exit immediately if the file doesn't exist
        if thumb_name is None:
            return None

        thumb_dir = self.thumb_dir_a if dir_a else self.thumb_dir_b
        return os.path.join(thumb_dir, thumb_name[1])

    def get_duplicates(self, similarity: float = None):
        """
        Builds the duplicates clusters. The function returns the

        :param similarity:
        :return:
        """
        clusters = self.build_loose_duplicate_cluster(similarity)
        return self.find_best_image(clusters)

    def spawn_duplicate_worker(self, queue_size: int = 1000, start_id: int = None, threshold: float = 200) \
            -> Tuple[mp.Queue, th.Thread]:
        """
        Function creates a worker thread which continuously enqueues dicts of each matching pair into the returned
        transfer queue.

        The queue will contain dicts with the following keys:
        key: id of that dif pair in the dif table. (can be provided as start id)
        key_a: key of the first file in the directory table
        key_b: key of the second file in the directory table
        b_dir_b: if the second file is in the b directory or the a directory
        path_X: path to file a or b
        filename_X: filename of file a or b
        px_X: horizontal pixel count of file a or b
        py_X: vertical pixel count of file a or b

        :param queue_size: max_size the queue can reach
        :param start_id: from which key the thread should start adding the matching pairs
                (in case the process got stopped)
        :param threshold: differernce value below something must lay for it to be considered to be a duplicate.
        :return: queue containing dicts of the matching pairs, thread object that is filling the queue.
        """
        transfer_queue = mp.Queue(maxsize=queue_size)
        process = th.Thread(target=self.continuous_dequeue_worker, args=(transfer_queue, start_id, threshold))
        process.start()
        return transfer_queue, process

    def continuous_dequeue_worker(self, out_queue: mp.Queue, start: int = None, threshold: float = 200):
        """
        Worker function for get_duplicates. Performs the fetching from db, wrapping in dicts and putting in queue.

        The queue will contain dicts with the following keys:
        key: id of that dif pair in the dif table. (can be provided as start id)
        key_a: key of the first file in the directory table
        key_b: key of the second file in the directory table
        b_dir_b: if the second file is in the b directory or the a directory
        path_X: path to file a or b
        filename_X: filename of file a or b
        px_X: horizontal pixel count of file a or b
        py_X: vertical pixel count of file a or b

        :param out_queue: queue to put the wrapped results into
        :param start: starting key in dif table
        :param threshold: measurement under which the difference must lay.
        :return: None
        """
        # get initial number of pairs and make sure they are not empty.
        pairs = self.db.get_many_pairs(threshold=threshold, start_key=start)
        if len(pairs) == 0:
            return

        while True:
            # process each pair and put it in a queue.
            for p in pairs:
                key_a = self.db.fetch_one_key(key=p["key_a"], directory_a=True)
                key_b = self.db.fetch_one_key(key=p["key_b"], directory_a=not p["b_dir_b"])
                p["path_a"] = key_a["path_a"]
                p["filename_a"] = key_a["filename_a"]
                p["px_a"] = key_a["px_a"]
                p["py_a"] = key_a["py_a"]
                p["path_b"] = key_b["path_b"]
                p["filename_b"] = key_b["filename_b"]
                p["px_b"] = key_b["px_b"]
                p["py_b"] = key_b["py_b"]
                del p["dif"]
                del p["error"]
                del p["success"]

                out_queue.put(p, block=True)

            last_key = pairs[-1]["key"]
            pairs = self.db.get_many_pairs(threshold=threshold, start_key=last_key)

            if len(pairs) == 0:
                return

    def build_loose_duplicate_cluster(self, similarity: float = None):
        """
        Function generates a list of dicts containing duplicates. Each dict in the list satisfies that there exists at
        least **one** path between each two images. It is **not** guaranteed that within a cluster each pair of images
        matches the similarity threshold.

        This function is implemented in **RAM** only. If the dataset to deduplicate is too large, it is possible that
        this function fails due to insufficient memory. A Database driven solution might exist in the future.

        Alternatively, there's also the functionality to create a process which reads out the database and fills a
        queue. That way each pair of duplicates images can be processed separately by an external application.
        See *spawn_duplicate_worker*

        :param similarity: The average difference between the pixels that should be allowed. If left empty, it reuses
        the value from the call to second_loop_iteration
        :return:
        """
        if similarity is None:
            similarity = self.similarity_threshold

        if similarity <= 0:
            raise ValueError("No Similarity provided and / or similarity_threshold from second loop not usable.")

        all_duplicate_pairs = self.db.get_all_matching_pairs(similarity)

        clusters: Dict[str, list] = {}
        cluster_id: dict = {}

        next_id = 0
        count = 0
        for row in all_duplicate_pairs:
            if count % 100 == 0:
                print(f"Done with {count}", end="\r", flush=True)
            count += 1

            # get the data from the rows
            key_a = row[1]
            key_b = row[2]
            b_dir_b = int(row[3])  # could be realized through self.has_dir_B

            # prepare for the data structure of ram
            graph_key_a = f"a_{key_a}"
            graph_key_b = f"b_{key_b}" * b_dir_b + f"a_{key_b}" * (1 - b_dir_b)

            # get the cluster for the keys
            cluster_id_a = cluster_id.get(graph_key_a)
            cluster_id_b = cluster_id.get(graph_key_b)

            next_id = self.process_pair(cluster_id_a, cluster_id_b, next_id, clusters, cluster_id,
                                        graph_key_a, graph_key_b)

        return clusters

    @staticmethod
    def process_pair(cluster_id_a: str, cluster_id_b: str, next_id: int, clusters: Dict[str, list], cluster_id: dict,
                     graph_key_a: str, graph_key_b: str):
        """
        Given a pair of graph_keys and cluster_ids, update the clusters and the cluster_ids dict accordingly.

        :param cluster_id_a: The id of the cluster in which graph_key_a is.
        :param cluster_id_b: The id of the cluster in which graph_key_b is.
        :param next_id: The next cluster_id that should be used if a new one was to be created
        :param clusters: Dict containing the clusters. [cluster_id, list of graph_keys]
        :param cluster_id: Dict containing the cluster_ids of every graph_key
        :param graph_key_a: The key of image_a in correct format
        :param graph_key_b: The key of image_b in correct format
        :return: the next id.
        """

        # No key is in a cluster, creating a new one.
        if cluster_id_a is None and cluster_id_b is None:
            new_cluster_id = str(next_id)

            clusters[new_cluster_id] = [graph_key_a, graph_key_b]
            cluster_id[graph_key_a] = new_cluster_id
            cluster_id[graph_key_b] = new_cluster_id
            return next_id + 1

        # We add image_a to the cluster in which image_b is located.
        elif cluster_id_a is None and cluster_id_b is not None:
            clusters[cluster_id_b].append(graph_key_a)
            cluster_id[graph_key_a] = cluster_id_b
            return next_id

        # We add image_b to the cluster in which image_a is located
        elif cluster_id_a is not None and cluster_id_b is None:
            clusters[cluster_id_a].append(graph_key_b)
            cluster_id[graph_key_b] = cluster_id_a

        # We have two clusters that need to be merged. or a duplicate row
        else:
            if cluster_id_a == cluster_id_b:
                print("WARNING: Duplicate row found!!!\n")

            # We merge the two clusters into one.
            else:
                print("DEBUGGING; Merging clusters\n")
                # Select the smaller cluster to merge it into the larger cluster
                if len(clusters[cluster_id_a]) < len(clusters[cluster_id_b]):

                    # changing the cluster id
                    for graph_key in clusters[cluster_id_a]:
                        cluster_id[graph_key] = cluster_id_b

                    # copy the stuff over.
                    clusters[cluster_id_b].extend(clusters[cluster_id_a])

                    # dropping cluster_a
                    del clusters[cluster_id_a]

                else:
                    # changing the cluster id
                    for graph_key in clusters[cluster_id_b]:
                        cluster_id[graph_key] = cluster_id_a

                    # copy the stuff over.
                    clusters[cluster_id_a].extend(clusters[cluster_id_b])

                    # dropping cluster_a
                    del clusters[cluster_id_b]
                return next_id

    def find_best_image(self, cluster: Dict[str, list], comparator: FunctionType = None):
        """
        Given a dict of clusters, go through the clusters and determine the best image based on a comparator function.

        :param comparator: function to use to determine best image in set of duplicates.
        :param cluster: dict containing lists.
        :return: dict containing the diplicate clusters and a list of all lower quality image filepaths.
        """
        fp_list = []
        for cluster_id, images in cluster.items():
            if len(images) > 1000:
                print("DEBUG: Excessive amount of duplicates found.")

            if len(images) == 0:
                print("WARNING: Found empty images list")

            filepaths = []

            for image in images:
                directory, key = image.split("_")
                info = self.db.fetch_one_key(key=key, directory_a=directory == "a")
                filepaths.append(info["path"])

            fp_list.append((filepaths, comparator))

        # create an executor
        ppe = ProcessPoolExecutor()
        results = ppe.map(find_best_image, fp_list)

        # process results
        lower_quality = []
        output = {}
        for result in results:
            # unpacking tuple
            res_dict, dups = result

            # updating global info.
            lower_quality.extend(dups)
            res_dict["duplicates"] = dups
            output[datetime.datetime.utcnow().timestamp()] = res_dict

        return output, lower_quality

    # ------------------------------------------------------------------------------------------------------------------
    # PROPERTIES
    # ------------------------------------------------------------------------------------------------------------------

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
        if value is None:
            self.__p_root_dir_b = None
            self.__thumb_dir_b = None
            self.__has_dir_b = False

        elif os.path.exists(value):
            self.__p_root_dir_b = value
            self.__thumb_dir_b = os.path.join(self.__p_root_dir_b, ".temp_thumbnails")
            self.__has_dir_b = True
        else:
            raise ValueError("The root dir b is not None yet it doesn't exist")

    @property
    def thumb_dir_a(self):
        return self.__thumb_dir_a

    @property
    def thumb_dir_b(self):
        return self.__thumb_dir_b

    @property
    def has_dir_b(self):
        return self.__has_dir_b

    @property
    def similarity_threshold(self):
        return self.__similarity_threshold

    @similarity_threshold.setter
    def similarity_threshold(self, value):
        if type(value) is not float or value < 0:
            raise ValueError("similarity threshold needs to be float and greater than 0.")
        self.__similarity_threshold = value
