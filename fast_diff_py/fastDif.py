import datetime
import shutil
import sys
import time
from fast_diff_py.database import Database
import os
from typing import List, Tuple, Dict
from types import FunctionType
from fast_diff_py.utils import *
import multiprocessing as mp
import multiprocessing.connection as con
import threading as th
import queue
from fast_diff_py.datatransfer import *
from concurrent.futures import ProcessPoolExecutor
from fast_diff_py.sql_database import SQLiteDatabase
from fast_diff_py.config import FastDiffPyConfig
from fast_diff_py.child_processes import parallel_resize, parallel_compare, find_best_image, \
    first_loop_dequeue_worker, first_loop_enqueue_worker
import logging


"""
Fast implementation of the DifPy Library.
Features:
- Use GPU to accelerate the comparison
- Use Parallelization on multicore CPUs
- Use of aspect ration to ignore images with non-matching aspect ratio
- Use hash based deduplication to find duplicates with color grading
"""

# from contextlib import redirect_stdout
#
# with open('out.txt', 'w') as f:
#     with redirect_stdout(f):
#         print('data')



# TODO single processing handler
# TODO Implement process stop recovery.
# TODO plot table is redundant. Use key from diff table and if create plot insert an empty row in the diff table.
# ----------------------------------------------------------------------------------------------------------------------
# FEATURES
# ----------------------------------------------------------------------------------------------------------------------
# TODO Range in which the aspects must lay for matching_aspect to trigger
# TODO Harakiri method. More reckless method.
# TODO keyboard shortcuts pyinput
# TODO different shift amounts for different colors.
# TODO Arbitrary hash matching function
# TODO Extract hashing_data
# TODO Smart child processes that fetch their info from the db and that have a queue for the next key that needs ot be
#  processed. => Wont allow for smart algo for increment => for very large datasets. (Maybe with check?)

class FastDiffPyBase:
    __db: Union[Database, None]

    # config
    config: Union[FastDiffPyConfig, None] = None

    def __init__(self, cfg: dict = None):
        """
        Init of Base class.

        Provided the base class is instantiated itself and not just called as the parent for FastDiffPy, the config
        from the main class is copied into this one and stored.

        :param cfg: config dict form parent class.
        """
        if cfg is not None:
            self.config = FastDiffPyConfig()
            self.config.retain_config = False
            self.config._task_dict = cfg


    @property
    def db(self):
        return self.__db

    @db.setter
    def db(self, value):
        self.__db = value
        if self.config.retain_db:
            self.config.database = self.__db.create_config_dump()
            self.config.write_to_file()

    # ------------------------------------------------------------------------------------------------------------------
    # FIRST LOOP COMMON FUNCTIONS
    # ------------------------------------------------------------------------------------------------------------------

    def generate_first_loop_obj(self) \
            -> Union[PreprocessArguments, None]:
        """
        Short wrapper function which creates the PreprocessingArguments and updates the DB.

        :return: PreprocessingArguments (on success), None if nothing was found.
        """
        task = self.db.get_next_to_process()

        # if there's no task left, stop the loop.
        if task is None:
            return None

        # generate a new argument
        arg = PreprocessArguments(
            amount=self.config.fl_shift_amount,
            key=task["key"],
            in_path=task["path"],
            out_path=self.generate_thumbnail_path(dir_a=task["dir_a"], filename=task["filename"],
                                                  key=task["key"]),
            compute_hash=self.config.fl_compute_hash,
            store_thumb=self.config.fl_compute_thumbnails,
            size_x=self.config.thumbnail_size_x,
            size_y=self.config.thumbnail_size_y,
        )
        self.db.mark_processing(task)

        return arg

    def generate_thumbnail_path(self, key: int, filename: str, dir_a: bool):
        """
        Generate the thumbnail_path first tries to fetch the thumbnail name from the db if it exists already,
        otherwise generate a new name.

        :param key: key in the directory_x table
        :param filename: the name of the file with extension
        :param dir_a: if the file is located in directory a or b
        :return: the thumbnail path.
        """
        name = self.db.get_thumb_name(key)
        directory = self.config.thumb_dir_a if dir_a else self.config.thumb_dir_b

        # return the name if it existed already
        if name is not None:
            return os.path.join(directory, name[1])

        name = self.db.generate_new_thumb_name(key, filename, dir_a=dir_a, retry_limit=self.config.retry_limit)
        return os.path.join(directory, name)

    def handle_result_of_first_loop(self, res_q: mp.Queue) -> Tuple[bool, bool]:
        """
        Dequeues a result of the first loop results queue and updates the database accordingly.

        :param res_q: results queue

        :return: if a result was handled, if the process exited.
        """
        # retrieve the result from the queue
        try:
            res = res_q.get(timeout=1.0)
        except queue.Empty:
            return False, False

        if res is None:
            return False, True

        # sanitize result
        assert type(res) is str, "Result is not a string"
        result_obj = PreprocessResults.from_json(res)

        # Handle the case when an error occurred.
        if not result_obj.success:
            self.db.update_dir_error(key=result_obj.key, msg=result_obj.error)
            return True, False

        # store the hash if computed
        if self.config.fl_compute_hash:
            # Drop hashes if they are only partly computed.
            if self.db.has_any_hash(key=result_obj.key):
                self.db.del_all_hashes(key=result_obj.key)

            # Store all hashes
            self.db.insert_hash(key=result_obj.key, file_hash=result_obj.hash_0, rotation=0)
            self.db.insert_hash(key=result_obj.key, file_hash=result_obj.hash_90, rotation=90)
            self.db.insert_hash(key=result_obj.key, file_hash=result_obj.hash_180, rotation=180)
            self.db.insert_hash(key=result_obj.key, file_hash=result_obj.hash_270, rotation=270)

        # mark file as processed only if the other data was inserted.
        self.db.update_dir_success(key=result_obj.key, px=result_obj.original_x, py=result_obj.original_y)

        # to be sure commit here.
        self.db.commit()
        return True, False

    # ------------------------------------------------------------------------------------------------------------------
    # SECOND LOOP COMMON FUNCTIONS
    # ------------------------------------------------------------------------------------------------------------------

    def sl_refill_queues(self, in_queue: Union[List[mp.Queue], mp.Queue]) -> int:
        """
        Call to either the optimized or non optimized filler.

        :return:
        """
        # testing if the
        if type(self.config.sl_queue_status) is dict:
            return self.__refill_queues_non_optimized(target_queue=in_queue)

        assert type(self.config.sl_queue_status) is list, f"Unexpected type of config.sl_queue_status: " \
                                                            f"{type(self.config.sl_queue_status).__name__}, " \
                                                            f"valid are list and dict"

        return self._refill_queues_optimized(queue_list=in_queue)

    def __refill_queues_non_optimized(self, target_queue: mp.Queue) -> Union[int, None]:
        """
        Refilling queues without the load optimized algorithm.

        :param target_queue: queue to insert pairs into.

        :return: number of images inserted into queues.
        """
        # ThIS FUNCTION IS CALLED WHEN WE HAVE ENOUGH IMAGES TO PROCESS.
        # Sanity checks:
        assert self.config.less_optimized, "This functions needs to be called in the less_optimized mode since it " \
                                           "assumes that the attribute second_loop_in is of type mp.Queue and " \
                                           "not List[mp.Queue]"
        assert type(self.config.sl_queue_status) is dict, "less optimized not with dict in sl_queue_status"
        assert ["fix_key", "shift_key", "done"] == list(
            self.config.sl_queue_status.keys()), "Verify keys of sl_queue_status"

        if self.config.sl_queue_status["done"]:
            return 0

        # initialize loop vars
        procs = self.config.sl_cpu_proc + self.config.sl_gpu_proc

        add_count = 0

        # Fetch the place where we left off
        fix_key = self.config.sl_queue_status["fix_key"] # Last submitted a key
        shift_key = self.config.sl_queue_status["shift_key"] # Last submitted b key

        # Fetch the fixed row and the next key
        cur_f_row = self.db.fetch_row_of_key(key=fix_key)

        while add_count < procs * 100:
            shifting_rows = self.db.fetch_many_after_key(directory_a=not self.config.has_dir_b, starting=shift_key,
                                                         count=procs*100 - add_count)

            # We have reached the end of the current cycle and need to increment the fixed row.
            if len(shifting_rows) == 0:
                next_row = self.db.fetch_many_after_key(directory_a=True, starting=fix_key, count=2)

                # We have a directory_b, and we've exhausted every picture in directory_a. => Stop
                if self.config.has_dir_b and len(next_row) == 0:
                    self.config.sl_queue_status["done"] = True
                    return add_count

                # verify that we have at least another image to compare if we don't have dir_b, so the fixed picture
                # is the second to last image in directory_a.
                elif not self.config.has_dir_b and len(next_row) == 1:
                    self.config.sl_queue_status["done"] = True
                    return add_count

                # We have at least one more row to go:
                self.config.sl_queue_status["fix_key"] = fix_key =next_row[0]["key"]
                cur_f_row = next_row[0]

                # The shift key needs to be none since we start from the beginning if we have a directory_b or
                # it needs to be the fixed key since we want to compare everything upwards.
                self.config.sl_queue_status["shift_key"] = shift_key = None if self.config.has_dir_b else fix_key
                # We need to continue since we need to refetch the shifting_rows
                continue

            # go through the shifting rows and schedule them.
            for row in shifting_rows:
                insert_success, queue_full = self._schedule_pair(row_a=cur_f_row, row_b=row, in_queue=target_queue)

                # Queue is full
                if queue_full:
                    return add_count

                # regardless weather the insert was successful or aborted because of match aspect, set the config.
                self.config.sl_queue_status["shift_key"] = shift_key = row["key"]
                add_count += int(insert_success)

        # We added successfully the full number of images to the queue, return the add count.
        return add_count


    def _refill_queues_optimized(self, queue_list: List[mp.Queue]):
        """
        Performs the optimized filling of the queues.

        :return:
        """
        inserted = 0
        for p in range(len(queue_list)):
            # fetch possible candidates for the row.
            row_a, row_b = self._fetch_rows(p=p)

            # if the rows are empty => Nothing left to do, skip updating for this process
            if len(row_a) == 0 and len(row_b) == 0:
                queue_list[p].put(None)
                continue

            inserted_count = 100

            not_full = True
            iterations = 0
            while not_full:
                if self.config.sl_base_a:
                    for i in range(len(row_b)):
                        insertion_success, full = self._schedule_pair(row_a=self.config.sl_queue_status[p]["row_a"],
                                                                      row_b=row_b[i], in_queue=queue_list[p])
                        if full:
                            break
                        inserted_count -= int(insertion_success)
                        inserted += int(insertion_success)

                else:
                    for i in range(len(row_a)):
                        insertion_success, full = self._schedule_pair(row_a=row_a[i],
                                                                      row_b=self.config.sl_queue_status[p]["row_b"],
                                                                      in_queue=queue_list[p])
                        if full:
                            break
                        inserted_count -= int(insertion_success)
                        inserted += int(insertion_success)

                iterations += 1

                # update last key
                if self.config.has_dir_b:
                    if not self.config.sl_base_a:
                        self.config.sl_queue_status[p]["last_key"] = row_a[-1]["key"]
                    else:
                        self.config.sl_queue_status[p]["last_key"] = row_b[-1]["key"]
                else:
                    self.config.sl_queue_status[p]["last_key"] = row_b[-1]["key"]

                row_a, row_b = self._fetch_rows(p=p)

                # try to increment key. If the increment method returns False, then no more keys are available, so
                # stop trying to add more to the queue
                if len(row_a) == 0 and len(row_b) == 0:
                    # we don't have any images left to process.
                    if not self._increment_fixed_image(queue_list=queue_list, p=p):
                        break

                    row_a, row_b = self._fetch_rows(p=p)

                    # case when we are at the last image (which can only be compared against itself,
                    # ergo nothing to do)
                    if len(row_a) == 0 and len(row_b) == 0:
                        break

                if inserted_count <= 0:
                    not_full = False

        return inserted if inserted > 0 else None

    def _schedule_pair(self, row_a: dict, row_b: dict, in_queue: Union[List[mp.Queue], mp.Queue]) -> Tuple[bool, bool]:
        """
        Given two rows from the database, performs the checks necessary to schedule them. If they pass, send them to the
        respective queue.

        :param row_a: first row (from dir_a)
        :param row_b: second row (form dir_a or dir_b)
        :param in_queue: Queue to insert pair into.
        :return: success: element was inserted in queue, full: queue is full
        """
        thumb_a_path = None
        thumb_b_path = None

        if self.config.sl_has_thumb:
            thumb_a_path = self.get_thumb_path_from_db(key=row_a["key"], dir_a=True)
            thumb_b_path = self.get_thumb_path_from_db(key=row_b["key"], dir_a=True)

        # performing match if desired
        if self.config.sl_matching_aspect:
            if not self.match_aspect(row_a=row_a, row_b=row_b):
                return False, False

        # Aspect matches => Create Task object and send to process
        # self.logger.debug(f"Key A: {row_a['key']}, Key B: {row_b['key']}")
        arg = CompareImageArguments(
            img_a=row_a["path"],
            img_b=row_b["path"],
            thumb_a=thumb_a_path,
            thumb_b=thumb_b_path,
            key_a=row_a["key"],
            key_b=row_b["key"],
            store_path=self.create_plt_name(key_a=row_a["key"], key_b=row_b["key"]),
            store_compare=self.config.sl_make_diff_plots,
            compare_threshold=self.config.similarity_threshold,
            size_x=self.config.thumbnail_size_x,
            size_y=self.config.thumbnail_size_y,
        )

        # Emptiness of queue needs to be established before calling this function
        try:
            in_queue.put(arg.to_json(), block=False)
        except queue.Full:
            return False, True
        return True, False

    def _fetch_rows(self, p: int, count: int = 100) -> Tuple[list, list]:
        """
        Fetch the next up to 100 rows for the ingest process into the children.

        :param p: Index of the process
        :return:
        """
        row_a = []
        row_b = []
        assert type(self.config.sl_queue_status) is list, "_fetch_rows called with not_optimized process"

        # we have a directory b
        if self.config.has_dir_b:

            # we don't keep the images of dir_a fixed but the ones of dir_b
            if not self.config.sl_base_a:
                row_a = self.db.fetch_many_after_key(directory_a=True, count=count,
                                                     starting=self.config.sl_queue_status[p]["last_key"])
            # we keep the images of dir a fixed
            else:
                row_b = self.db.fetch_many_after_key(directory_a=False, count=count,
                                                     starting=self.config.sl_queue_status[p]["last_key"])
        # we don't have a directory b
        else:
            row_b = self.db.fetch_many_after_key(directory_a=True, count=count,
                                                 starting=self.config.sl_queue_status[p]["last_key"])
        return row_a, row_b

    def _increment_fixed_image(self, queue_list: List[mp.Queue], p: int):
        """
        Given a process p, it searches for the next 'row' in the matching matrix to find the next key to keep constant
        for the process p

        :param queue_list: list of Queues.
        :param p: index of process spec in self.config.sl_queue_status
        :return: True -> free image found, False, -> no new image found.
        """
        # TODO implement smart algorithm to find next image for the process that is now done.
        next_key = 0

        # get the limit for the next key
        for i in range(len(self.config.sl_queue_status)):
            if self.config.has_dir_b:
                if not self.config.sl_base_a:
                    next_key = max(self.config.sl_queue_status[i]["row_b"]["key"], next_key)
                    continue

            next_key = max(self.config.sl_queue_status[i]["row_a"]["key"], next_key)

        # process case, when we're looking to move the dir_b
        if self.config.has_dir_b:
            if not self.config.sl_base_a:
                rows = self.db.fetch_many_after_key(directory_a=False, starting=next_key, count=1)

                # no completely unprocessed key found
                if len(rows) == 0:
                    if not queue_list[p].full():
                        queue_list[p].put(None)
                    return False

                # update the dict
                self.config.sl_queue_status[p] = {"row_b": rows[0], "last_key": None}
                return True

        rows = self.db.fetch_many_after_key(directory_a=True, starting=next_key, count=1)

        # no completely unprocessed key found
        if len(rows) == 0:
            if not queue_list[p].full():
                queue_list[p].put(None)
            return False

        # update the dict
        self.config.sl_queue_status[p] = {"row_a": rows[0], "last_key": rows[0]["key"]}
        return True

    def get_thumb_path_from_db(self, key: int, dir_a: bool) -> Union[None, str]:
        """
        Get a new thumbnail name from the database. Combine it with the specified path from this object.

        :param key: key in directory table
        :param dir_a: if the file is in directory a
        :return: thumbnail path or None
        """
        thumb_name = self.db.get_thumb_name(key=key)

        # exit immediately if the file doesn't exist
        if thumb_name is None:
            return None

        thumb_dir = self.config.thumb_dir_a if dir_a else self.config.thumb_dir_b
        return os.path.join(thumb_dir, thumb_name[1])

    def create_plt_name(self, key_a: int, key_b: int) -> Union[None, str]:
        """
        Small function to create a fully qualified path to store the plots.

        :param key_a: key if the first image
        :param key_b: key of the second image
        :return: path to the plot or None
        """
        if not self.config.sl_make_diff_plots:
            return None

        nm = self.db.make_plot_name(key_a=key_a, key_b=key_b)
        return os.path.join(self.config.sl_plot_output_dir, nm)

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

    def _process_one_second_result(self, out_queue: mp.Queue) -> Tuple[bool, bool]:
        """
        Perform dequeue of one element of the second process results queue. Insert the result into the database
        subsequently.

        :param out_queue: Queue to dequeue the stuff from.

        :return: element processed (no timeout), if a process exited.
        """
        try:
            res = out_queue.get(timeout=0.1)
        except queue.Empty:
            return False, False

        if res is None:
            return False, True

        assert type(res) is str, "Result of comparison was not string"
        res_obj = CompareImageResults.from_json(res)

        # store in database
        if res_obj.success:
            self.db.insert_diff_success(key_a=res_obj.key_a, key_b=res_obj.key_b, dif=res_obj.min_avg_diff)
        else:
            self.db.insert_diff_error(key_a=res_obj.key_a, key_b=res_obj.key_b, error=res_obj.error)
        return True, False


class FastDifPy(FastDiffPyBase):
    # relative to child processes
    first_loop_in: mp.Queue = None  # the tasks sent to the child processes
    first_loop_out: mp.Queue = None  # the results coming from the child processes

    second_loop_in: Union[List[mp.Queue], mp.Queue] = None
    second_loop_out: mp.Queue = None

    # multiprocessing handles
    cpu_handles = None
    gpu_handles = None

    # logger / CLI Output
    logger: logging.Logger = None
    file_handler: logging.FileHandler = None
    stream_handler: logging.StreamHandler = None
    debug_logger: logging.FileHandler = None

    def __init__(self, directory_a: str, directory_b: str = None, default_db: bool = True, **kwargs):
        """
        Provide the directories to be searched. If a different implementation of the database is used,
        set the test_db to false.

        :param directory_a: first directory to search for differentiation.
        :param directory_b: second directory to compare against. Otherwise, comparison will be done against directory
        :param default_db: create a sqlite database in the a_directory.
        itself.

        kwarg:
        ------
        - debug: bool - Enable Debug File in the logs.
        - config_path: str - Path to the config that stores the progress of the program (for progress recovery on stop)
        - config_purge: str - Ignore preexisting config and overwrite it.
        """
        super().__init__()

        config_path = None
        if "config_path" in kwargs.keys():
            config_path = kwargs.get("config_path")

        config_purge = True
        if "config_purge" in kwargs.keys():
            config_purge = kwargs.get("config_purge")

        self.config = FastDiffPyConfig(task_path=config_path, task_purge=config_purge)
        self.config.retain_config = True

        if not self.verify_config():
            # Only set the directory_a and directory_b when the config is not set.
            if not os.path.isdir(directory_a):
                raise NotADirectoryError(f"{directory_a} is not a directory")

            if directory_b is not None and not os.path.isdir(directory_b):
                raise NotADirectoryError(f"{directory_b} is not a directory")

            directory_a = os.path.abspath(directory_a)
            directory_b = os.path.abspath(directory_b) if directory_b is not None else None

            # make sure the paths aren't sub-dirs of each other.
            if directory_b is not None:
                temp_a = directory_a + os.sep
                temp_b = directory_b + os.sep
                if temp_a.startswith(temp_b):
                    raise ValueError(f"{directory_a} is a subdirectory of {directory_b}")
                elif temp_b.startswith(temp_a):
                    raise ValueError(f"{directory_b} is a subdirectory of {directory_a}")

            self.config.p_root_dir_b = directory_b
            self.config.p_root_dir_a = directory_a

            # Creating default database if desired.
            if default_db:
                self.db = SQLiteDatabase(path=os.path.join(self.config.p_root_dir_a, "diff.db"))

            self.config.ignore_paths = []
            self.config.ignore_names = []


        debug = False
        if "debug" in kwargs.keys():
            debug = kwargs.get("debug")

        self.prepare_logging(debug=debug)

        # Setting the first stuff in the config
        self.config.state = "init"
        self.config.write_to_file()

    def verify_config(self, full_depth: bool = False):
        """
        Load the config and verify that the folders match and the content if the directories too.

        :param full_depth: Check that every file in the database exists.

        :return: returns False if no Config is found. otherwise returns true.
        """
        # Empty dict, we have nothing.
        if not os.path.exists(self.config.cfg_path):
            return False

        if full_depth:
            self.verify_dir_content()
        return True

    def verify_dir_content(self):
        """
        Function should go through dir table and make sure every file exists. If a file doesn't exist, raises ValueError.
        :return:
        """
        pass

    def index_the_dirs(self):
        """
        List all the files in directory_a and possibly directory_b and store the paths and filenames in the temporary
        database.

        :return:
        """
        self.__recursive_index(True)
        if self.config.has_dir_b:
            self.__recursive_index(False)

        self.config.state = "indexed_dirs"

        # get the number of images and create short circuit.
        im_num = self.db.get_dir_count()
        a_num = self.db.get_dir_count(dir_a=True)
        self.config.enough_images_to_compare = im_num > 1 and a_num >= 1
        self.config.write_to_file()

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
                path = self.config.p_root_dir_a
            else:
                path = self.config.p_root_dir_b

        for file_name in os.listdir(path):
            full_path = os.path.join(path, file_name)

            # ignore a path if given
            if full_path in self.config.ignore_paths:
                continue

            # ignoring based only on name
            if file_name in self.config.ignore_names:
                continue

            # Thumbnail directory is called .temp_thumbnails
            if file_name.startswith(".temp_thumb") and ignore_thumbnail:
                continue

            # for directories, continue the recursion
            if os.path.isdir(full_path):
                self.__recursive_index(dir_a, full_path)

            if os.path.isfile(full_path):
                # check if the file is supported, then add it to the database
                if os.path.splitext(full_path)[1].lower() in self.config.supported_file_types:
                    self.db.add_file(full_path, file_name, dir_a)

    def estimate_disk_usage(self, print_results: bool = True) -> Tuple[int, int]:
        """
        Estimate the diskusage of the thumbnail directory given the compressed image size.

        :param print_results: print the results to console
        :return: byte_count_a, byte_count_b
        """
        dir_a_count = self.db.get_dir_count(True)
        dir_b_count = self.db.get_dir_count(False)

        if dir_b_count == 0:
            comps = dir_a_count * (dir_a_count-1) / 2
        else:
            comps = dir_a_count * dir_b_count

        byte_count_a = dir_a_count * self.config.thumbnail_size_x * self.config.thumbnail_size_y * 3
        byte_count_b = dir_b_count * self.config.thumbnail_size_x * self.config.thumbnail_size_y * 3

        dir_b = self.config.p_root_dir_b if self.config.has_dir_b else ""

        target = max(len(self.config.p_root_dir_a), len(dir_b), len('the two dirs '))

        if print_results:
            print(
                f"Estimated disk usage by {fill(self.config.p_root_dir_a, target)}: " + h(byte_count_a, "B") +
                " bytes")
            if self.config.has_dir_b:
                print(
                    f"Estimated disk usage by {fill(self.config.p_root_dir_b, target)}: " + h(byte_count_b, "B") +
                    " bytes")
                print(f"Estimated disk usage by {fill('the two dirs ', target)}: " +
                      h(byte_count_b + byte_count_a, "B") + "bytes")

            print(f"Number of Images in Database {dir_a_count + dir_b_count}, Comparisons: {comps}")

        return byte_count_a, byte_count_b

    def clean_up(self, thumbs: bool = True, db: bool = True, config: bool = True):
        """
        Remove thumbnails and db.

        :param thumbs: Delete Thumbnail directories
        :param db: Delete Database
        :param config: Delete the Config file.
        :return:
        """
        if thumbs:
            self.logger.info("Deleting Thumbnails")
            try:
                shutil.rmtree(self.config.thumb_dir_a)
                self.logger.info(f"Deleted {self.config.thumb_dir_a}")
            except FileNotFoundError:
                pass
            if self.config.has_dir_b:
                try:
                    shutil.rmtree(self.config.thumb_dir_b)
                    self.logger.info(f"Deleted {self.config.thumb_dir_b}")
                except FileNotFoundError:
                    pass

        if db:
            self.db.free()
            self.db.disconnect()
            self.db.free()
            self.db = None
            self.logger.info("Deleted temporary database")

        if config:
            cfg_path = self.config.cfg_path
            self.config = None

            if os.path.exists(cfg_path):
                os.remove(cfg_path)
                self.logger.info("Deleted Config")

    # ==================================================================================================================
    # COMMON LOOP FUNCTIONS
    # ==================================================================================================================

    def check_create_thumbnail_dir(self):
        """
        Create the thumbnail directories if they don't exist already.

        :return:
        """
        if not os.path.exists(self.config.thumb_dir_a):
            os.makedirs(self.config.thumb_dir_a)

        if self.config.has_dir_b and not os.path.exists(self.config.thumb_dir_b):
            os.makedirs(self.config.thumb_dir_b)

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

        if self.config.less_optimized:
            for i in range((len(self.cpu_handles) + len(self.gpu_handles)) * 4):
                self.second_loop_in.put(None)
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
                self.logger.info(f"Trying to join process {i} Process Alive State is {p.is_alive()}")
                p.join(1)
                if p.is_alive():
                    self.logger.info(f"Process {i} timed out. Alive state: {p.is_alive()}; killing it.")
                    p.kill()
            except TimeoutError:
                self.logger.warning(f"Process {i} timed out. Alive state: {p.is_alive()}; killing it.")
                p.kill()

        for i in range(len(self.gpu_handles)):
            p = self.gpu_handles[i]
            try:
                self.logger.info(f"Trying to join process {i + cpu_proc} Process State is {p.is_alive()}")
                p.join(1)
                if p.is_alive():
                    self.logger.info(f"Process {i} timed out. Alive state: {p.is_alive()}; killing it.")
                    p.kill()
            except TimeoutError:
                self.logger.warning(f"Process {i + cpu_proc} timed out. Alive state: {p.is_alive()}; killing it.")
                p.kill()

    # ------------------------------------------------------------------------------------------------------------------
    # FIRST LOOP ITERATION; PREPROCESSING / ABSOLUTE MATCHING
    # ------------------------------------------------------------------------------------------------------------------

    def first_loop_iteration(self, compute_thumbnails: bool = True, compute_hash: bool = False, amount: int = 4,
                             cpu_proc: int = None):
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
        10bit images for example are not supported. They are probably down-converted. # TODO Verify!!!


        :param compute_thumbnails: Resize images and store them temporarily
        :param compute_hash: Compute hashes of the image
        :param amount: shift amount before hash
        :param cpu_proc: number of cpu processes. Default number of system cores.
        :return:
        """
        # Writing the arguments to config
        self.config.state = "first_loop_in_progress"
        self.config.fl_compute_thumbnails = compute_thumbnails
        self.config.fl_compute_hash = compute_hash
        self.config.fl_shift_amount = amount
        self.config.fl_cpu_proc = cpu_proc
        self.config.write_to_file()

        # Reset the marked files in any case.
        self.logger.debug("Reset as in progress marked files")
        self.db.reset_first_loop_mark()

        self.config.write_to_file()
        # INFO: Since the database marks files that are

        # Short circuit if there are no images in the database.
        if not self.config.enough_images_to_compare:
            self.logger.debug("No images in database, aborting.")
            return

        if self.config.fl_cpu_proc is None:
            self.config.fl_cpu_proc = mp.cpu_count()

        # store thumbnails if possible.
        if compute_hash:
            if amount == 0:
                self.logger.warning("amount 0, only EXACT duplicates are detected like this.")

            if amount > 7 or amount < -7:
                raise ValueError("amount my only be in range [-7, 7]")

        # thumbnail are required to exist for both.
        if compute_thumbnails or compute_hash:
            self.check_create_thumbnail_dir()

        # reset handles and create queues.
        self.cpu_handles = []
        self.gpu_handles = []

        self.first_loop_in = mp.Queue()
        self.first_loop_out = mp.Queue()

        # var for following while loop:
        run = True

        # prefill loop
        for i in range(self.config.fl_cpu_proc):
            arg = self._generate_first_loop_obj()

            # stop if there's nothing left to do.
            if arg is None:
                self.logger.info("Less images than processes, no continuous euqneueing.")
                run = False
                break

            self.first_loop_in.put(arg.to_json())
            self.config.fl_inserted_counter += 1

        v = self.verbose
        # start processes for cpu
        for i in range(self.config.fl_cpu_proc):
            p = mp.Process(target=parallel_resize, args=(self.first_loop_in, self.first_loop_out, i, False, v))
            p.start()
            self.cpu_handles.append(p)

        # turn main loop into handler and perform monitoring of the threads.
        none_counter = 0
        timeout = 0

        # handle the running state of the loop
        while run:
            if self.config.fl_inserted_counter % 100 == 0:
                self.logger.info(f"Inserted {self.config.fl_inserted_counter} images.")

            if self.handle_result_of_first_loop(self.first_loop_out):
                arg = self._generate_first_loop_obj()

                # if there's no task left, stop the loop.
                if arg is None:
                    none_counter += 1
                    self.first_loop_in.put(None)

                else:
                    self.first_loop_in.put(arg.to_json())
                    self.config.fl_inserted_counter += 1
                    timeout = 0
            else:
                time.sleep(1)
                timeout += 1

            # if this point is reached, all processes should be done and the queues empty.
            if none_counter >= self.config.fl_cpu_proc:
                run = False

            # at this point we should have been idling for 60s
            if timeout > 5:
                self.logger.info("Timeout reached, stopping.")
                run = False

        self.send_termination_signal(first_loop=True)

        counter = 0
        # try to handle any remaining results that are in the queue.
        while counter < 5:
            if not self.handle_result_of_first_loop(self.first_loop_out):
                counter += 1
                continue

            counter = 0

        self.join_all_children()
        assert self.first_loop_out.empty(), f"Result queue is not empty after all processes have been killed.\n " \
                                            f"Remaining: {self.first_loop_out.qsize()}"

        self.config.state = "first_loop_done"
        self.config.write_to_file()
        self.logger.info("All Images have been preprocessed.")

    # ==================================================================================================================
    # SECOND LOOP ITERATION / DIFFERENCE RATING
    # ==================================================================================================================

    def second_loop_iteration(self, only_matching_aspect: bool = False, only_matching_hash: bool = False,
                              make_diff_plots: bool = False, similarity_threshold: Union[int, float] = 200.0, gpu_proc: int = 0,
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
        # TODO check the number of images with self.db.get_dir_count() -> set the less optimized flag there and then
        #   make the adjustment fro there.
        # Writing to config.
        self.config.state = "second_loop_in_progress"
        self.config.sl_gpu_proc = gpu_proc
        self.config.sl_cpu_proc = cpu_proc
        self.config.sl_matching_aspect = only_matching_aspect
        self.config.sl_make_diff_plots = make_diff_plots
        self.config.sl_matching_hash = only_matching_hash
        self.config.similarity_threshold = float(similarity_threshold)
        self.config.state = "second_loop_in_progress"

        # Short circuit if there are no images in the database.
        if not self.config.enough_images_to_compare:
            self.logger.debug("No images in database, aborting.")
            return

        assert gpu_proc >= 0, "Number of GPU Processes needs to be greater than zero"
        if self.config.sl_cpu_proc is None:
            self.config.sl_cpu_proc = mp.cpu_count()

        assert self.config.sl_cpu_proc >= 1, "Number of GPU Processes needs to be greater than zero"

        self.config.sl_has_thumb = self.db.test_thumb_existence()

        if make_diff_plots:
            # diff_location is stored in config in this function.
            self.create_plot_dir(diff_location=diff_location)

        self.config.write_to_file()

        self.__sl_determine_algo()

        self.cpu_handles = []
        self.gpu_handles = []

        # create queues
        self.second_loop_out = mp.Queue()
        self.second_loop_in = mp.Queue()

        if not self.config.less_optimized:
            self.second_loop_in = [mp.Queue() for _ in range(self.config.sl_gpu_proc + self.config.sl_cpu_proc)]

        child_args = [(self.second_loop_in if self.config.less_optimized else self.second_loop_in[i],
                       self.second_loop_out, i, i >= self.config.sl_cpu_proc ,
                       False,
                       False,
                       self.verbose)
                          for i in range(self.config.sl_gpu_proc + self.config.sl_cpu_proc)]

        # prefill
        self.__init_queues()

        # starting all processes
        for i in range(self.config.sl_cpu_proc):
            p = mp.Process(target=parallel_compare, args=child_args[i])
            p.start()
            self.cpu_handles.append(p)

        for i in range(self.config.sl_cpu_proc, self.config.sl_cpu_proc + self.config.sl_gpu_proc):
            p = mp.Process(target=parallel_compare, args=child_args[i])
            p.start()
            self.gpu_handles.append(p)

        # check if we need multiple iterations of the main loop.
        done = self.__require_queue_refill()
        count = 0
        timeout = 0

        # update everything
        while not done:
            # update the queues and store if there are more tasks to process
            current_inserted, current_count = self.update_queues()
            count += current_count
            self.logger.info(f"Number of Processed Images: {count:,}".replace(",", "'"))

            # We have no more images to enqueue
            if current_inserted == 0 or current_inserted is None:
                self.send_termination_signal(first_loop=False)
                self.logger.debug("End of images reached.")
                done = True

            if current_count == 0:
                timeout += 1
                self.logger.debug("Dequeued 0 elements")
                time.sleep(1)

                if timeout > 5:
                    done = True
            else:
                timeout = 0

            # exit the while loop if all children have exited.
            _, _, _, all_exited = self.check_children(cpu=self.config.sl_cpu_proc > 0, gpu=self.config.sl_gpu_proc > 0)
            if all_exited:
                self.logger.debug("All Exited")
                done = True

        # check if it was the children's fault
        _, all_errored, _, _ = self.check_children(cpu=self.config.sl_cpu_proc > 0, gpu=self.config.sl_gpu_proc > 0)

        if all_errored:
            raise RuntimeError("All child processes exited with an Error")

        self.join_all_children()
        self.logger.debug("All child processes terminated")

        while count < 5:
            # handle last results:
            if 0 == self.handle_results_second_queue():
                count += 1
                continue

            count = 0

        # check if the tasks were empty.
        assert not self.handle_results_second_queue(), "Existed without having run out of tasks and without all " \
                                                       "processes having stopped."

        self.db.commit()
        self.config.state = "second_loop_done"
        self.config.write_to_file()
        self.logger.debug("Data should be committed")

    def __sl_determine_algo(self):
        """
        Determine if we use the optimized or non-optimized algorithm. => Important for layout of queues etc.
        Sets *config.sl_base_a* and *config.less_optimized*
        :return:
        """
        proc_count = self.config.sl_cpu_proc + self.config.sl_gpu_proc

        dir_a_count = self.db.get_dir_count(dir_a=True)
        dir_b_count = dir_a_count

        if self.config.has_dir_b:
            dir_b_count = self.db.get_dir_count(dir_a=False)

        if dir_a_count >= proc_count:
            self.config.sl_base_a = True
            return

        # dir_a has less than processes images
        if self.config.has_dir_b and dir_b_count >= proc_count:
            self.config.sl_base_a = False
            return

        # We have fewer images than processes in both folders. => Using less optimized approach
        self.config.less_optimized = True

    def __require_queue_refill(self):
        done = False
        a_count = self.db.get_dir_count(dir_a=True)
        b_count = self.db.get_dir_count(dir_a=False)

        if self.config.has_dir_b:
            comps = a_count * b_count

            if comps < (self.config.sl_cpu_proc + self.config.sl_gpu_proc) * 100:
                self.send_termination_signal(first_loop=False)
                done = True
                self.logger.info("Less comparisons than available space. Not performing continuous enqueue.")

        else:
            comps = a_count * (a_count - 1) / 2
            if comps < (self.config.sl_cpu_proc + self.config.sl_gpu_proc) * 100:
                self.send_termination_signal(first_loop=False)
                done = True
                self.logger.info("Less comparisons than available space. Not performing continuous enqueue.")
        return done

    def create_plot_dir(self, diff_location: str):
        """
        Verifies the provided directory, creates if it doesn't exist.

        :param diff_location: path to plot where the plots are to be saved
        :return:
        """
        if diff_location is None:
            raise ValueError("If plots are to be generated, an output folder needs to be specified.")
        if not os.path.isdir(diff_location):
            raise ValueError("Plot location doesn't specify a valid directory path")

        if not os.path.exists(diff_location):
            os.makedirs(diff_location)

        self.config.sl_plot_output_dir = diff_location

    def update_queues(self):
        enqueued = self.sl_refill_queues(in_queue=self.second_loop_in)
        dequeued = self.handle_results_second_queue(enqueued)
        return enqueued, dequeued

    def __init_queues(self):
        """
        Initialize the state describing variables as well as the queues for the second loop.
        :return:
        """
        processes = self.config.sl_cpu_proc + self.config.sl_gpu_proc
        # we are using less optimized, so we are going straight for the not optimized algorithm.
        if self.config.less_optimized:
            first_key = self.db.fetch_many_after_key(directory_a=True, starting=None, count=1)
            self.config.sl_queue_status = {"fix_key": first_key[0]["key"], "shift_key": None, "done": False}


            # Only on dir to itself - only upper matrix to be computed.
            if not self.config.has_dir_b:
                self.config.sl_queue_status["shift_key"] = first_key[0]["key"]

            return

        # from a fetch the first set of images
        if self.config.sl_base_a:
            rows = self.db.fetch_many_after_key(directory_a=True, count=processes)
        else:
            rows = self.db.fetch_many_after_key(directory_a=False, count=processes)

        # populating the files of the second loop.
        self.config.sl_queue_status = []

        if self.config.sl_base_a:
            for row in rows:
                # The last_key can be set if we have second_loop_base_a and no dir_b because we're looking only at an
                # upper triangular matrix of the Cartesian product of the elements of the image itself.
                temp = {"row_a": row, "last_key": None if self.config.has_dir_b else row["key"]}

                self.config.sl_queue_status.append(temp)
        else:
            for row in rows:
                temp = {"row_b": row, "last_key": None}

                self.config.sl_queue_status.append(temp)

        self._refill_queues_optimized(queue_list=self.second_loop_in)

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
                if not self._process_one_second_result(out_queue=self.second_loop_out):
                    return number_dequeues

                number_dequeues += 1

        # we have a max_number
        for i in range(max_number):
            if not self._process_one_second_result(out_queue=self.second_loop_out):
                return i

        return max_number

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

    def check_processes(self, processes: List[mp.Process]) -> Tuple[bool, bool, bool, bool]:
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
                    self.logger.warning("process is not alive but no exit code available")

            else:
                all_error = False
                all_exited = False

        return error, all_error, exited, all_exited

    # ==================================================================================================================
    # DATA RETRIEVAL FUNCTIONS
    # ==================================================================================================================

    def get_duplicates(self, similarity: float = None, dif_based: bool = True):
        """
        Builds the duplicates clusters. The function returns the

        :param similarity: amount that the dif amount needs to lay below.
        :param dif_based: if the relative difference should be used or hash based matching should be done.
        :return:
        """
        if not self.config.enough_images_to_compare:
            return {}, []

        if not dif_based:
            raise NotImplementedError("hash_based is in todos.")
        clusters = self.build_loose_duplicate_cluster(similarity)
        return self.find_best_image(clusters)

    def spawn_duplicate_pair_worker(self, queue_size: int = 1000, start_id: int = None, threshold: float = 200) \
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
        :param threshold: difference value below something must lay for it to be considered to be a duplicate.
        :return: queue containing dicts of the matching pairs, thread object that is filling the queue.
        """
        transfer_queue = mp.Queue(maxsize=queue_size)
        process = th.Thread(target=self.continuous_dif_pair_dequeue_worker, args=(transfer_queue, start_id, threshold))
        process.start()
        return transfer_queue, process

    def continuous_dif_pair_dequeue_worker(self, out_queue: mp.Queue, start: int = None, threshold: float = 200):
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

        # Perform with JOIN: TODO
        # SELECT * FROM dif_table JOIN directory d on dif_table.key_a = d.key JOIN
        # directory dd on dif_table.key_b = dd.key;
        while True:
            # process each pair and put it in a queue.
            for p in pairs:
                key_a = self.db.fetch_row_of_key(key=p["key_a"])
                key_b = self.db.fetch_row_of_key(key=p["key_b"])
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

    def print_preprocessing_errors(self):
        """
        Function fetches all errors that were encountered during the preprocessing phase and  prints them to the
        console.

        :return:
        """
        last_key = None

        # get the errors as long as there are any
        while True:
            results = self.db.get_many_preprocessing_errors(start_key=last_key, count=1000)

            if len(results) == 0:
                break

            for r in results:
                path = r['path']
                error = r['error']
                print(f"File {path} encountered error:\n{error}")

            last_key = results[-1]['key']

        print("-"*120)

    def print_compare_errors(self):
        """
        Function fetches all errors that were encountered during the comparison of the files and prints them to the
        console.

        :return:
        """
        errors = True
        last_key = None

        while errors:
            results = self.db.get_many_comparison_errors(start_key=last_key)

            if len(results) == 0:
                errors = False

            for r in results:
                path_a = r['a_path']
                path_b = r['b_path']
                error = r['error']
                print(f"Comparison of Files {path_a} and {path_b} encountered error:\n{error}")

            last_key = results[-1]['dif_key']

        print("-"*120)

    def spawn_duplicate_error_worker(self):
        """
        TODO Docstring
        :return:
        """
        raise NotImplementedError("Need to implement that one")

    def spawn_preprocessing_error_worker(self):
        """
        TODO Docstring
        :return:
        """
        raise NotImplementedError("Need to implement that one")

    def continuous_duplicate_error_worker(self):
        """
        TODO docstring
        :return:
        """
        raise NotImplementedError("Need to implement that one")

    def continuous_preprocessing_error_worker(self):
        """
        TODO docstring
        :return:
        """
        raise NotImplementedError("Need to implement that one")

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
            similarity = self.config.similarity_threshold

        if similarity <= 0:
            raise ValueError("No Similarity provided and / or similarity_threshold from second loop not usable.")

        all_duplicate_pairs = self.db.get_all_matching_pairs(similarity)

        clusters: Dict[str, list] = {}
        cluster_id: dict = {}

        next_id = 0
        count = 0
        for row in all_duplicate_pairs:
            if count % 100 == 0:
                if self.verbose:
                    print(f"Done with {count}", end="\r", flush=True)
            count += 1

            # get the data from the rows
            key_a = row[1]
            key_b = row[2]

            assert key_a != key_b, "Key A and Key B are the same, bug in scheduling."

            # get the cluster for the keys
            cluster_id_a = cluster_id.get(key_a)
            cluster_id_b = cluster_id.get(key_b)

            next_id = self.process_pair(cluster_id_a, cluster_id_b, next_id, clusters, cluster_id,
                                        key_a, key_b)

        return clusters

    def process_pair(self, cluster_id_a: str, cluster_id_b: str, next_id: int, clusters: Dict[str, list],
                     cluster_id: dict, graph_key_a: str, graph_key_b: str):
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
            return next_id

        # We have two clusters that need to be merged. or a duplicate row
        else:
            if cluster_id_a == cluster_id_b:
                return next_id

            # We merge the two clusters into one.
            else:
                self.logger.debug("Merging clusters")
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
                self.logger.debug("Excessive amount of duplicates found.")

            if len(images) == 0:
                self.logger.warning("Found empty images list")

            filepaths = []

            for img_key in images:
                info = self.db.fetch_row_of_key(key=img_key)
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
    def verbose(self):
        return self.config.verbose

    @verbose.setter
    def verbose(self, value):
        if type(value) is not bool:
            raise TypeError("Verbose is a boolean")

        self.config.verbose = value

        # update the logging level.
        if self.config.verbose:
            self.stream_handler.setLevel(logging.INFO)
        else:
            self.stream_handler.setLevel(logging.WARNING)

    def prepare_logging(self, console_level: int = logging.DEBUG, debug: bool = False):
        """
        Set's up logging for the class.

        :param console_level: log level of the console. use logging.LEVEL for this.
        :param debug: store the console log also inside a separate file.
        :return:
        """
        self.logger = logging.getLogger("fast_diff_py")

        # reconnecting handlers if previous handlers exist.
        if self.logger.hasHandlers():
            self.logger.debug("Logger has previous handlers, reconnecting them, assuming default config.")
            for handler in self.logger.handlers:
                if type(handler) is logging.StreamHandler:

                    # Follows from type checking
                    handler: logging.StreamHandler
                    self.stream_handler = handler
                if type(handler) is logging.FileHandler:

                    # Follows from Type checking
                    handler: logging.FileHandler
                    if handler.level is logging.WARNING:
                        self.file_handler = handler
                    else:
                        self.debug_logger = handler
            return

        # get location for the logs
        fp = os.path.abspath(os.path.dirname(__file__))

        # create two File handlers one for logging directly to file one for logging to Console
        self.stream_handler = logging.StreamHandler(sys.stdout)
        self.file_handler = logging.FileHandler(os.path.join(fp, "execution.log"))

        # create Formatter t o format the logging messages in the console and in the file
        console_formatter = logging.Formatter('%(asctime)s - %(message)s')
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        # add the formatters to the respective Handlers
        self.stream_handler.setFormatter(console_formatter)
        self.file_handler.setFormatter(file_formatter)

        # Set the logging level to the Handlers
        self.stream_handler.setLevel(console_level)
        self.file_handler.setLevel(logging.WARNING)

        # Add the logging Handlers to the logger instance
        self.logger.addHandler(self.stream_handler)
        self.logger.addHandler(self.file_handler)

        # In case a Debug log is desired create another Handler, add the file formatter and add the Handler to the
        # logger
        if debug:
            self.add_debug_logger(file_formatter, fp)

        # We do not want to pollute the information of the above loggers, so we don't propagate
        # We want our logger to emmit every message to all handlers, so we set it to DEBUG.
        self.logger.propagate = False
        self.logger.setLevel(logging.DEBUG)

    def add_debug_logger(self, file_formatter: logging.Formatter, out_dir: str = None):
        """
        Function gets called if prepare_logging has debug set. It can be called alternatively later on during code
        execution if one wants to get a preciser information about what is going on.

        There can only be one debug logger at a time. If this function is called twice, the old logger will be removed
        and the new one will be added. THIS MAY OVERWRITE THE DEBUG FILE IF THE __out_dir__ IS NOT SET!!!

        :param file_formatter: the formatter with which to create the logs.
        :param out_dir: Directory where the logs should be saved
        :return:
        """

        if out_dir is None:
            out_dir = os.path.abspath(os.path.dirname(__file__))

        if self.debug_logger is None:
            self.debug_logger = logging.FileHandler(os.path.join(out_dir, "debug_execution.log"))
            self.debug_logger.setFormatter(file_formatter)
            self.debug_logger.setLevel(logging.DEBUG)
            self.logger.addHandler(self.debug_logger)

        # remove eventually preexisting logger
        else:
            self.logger.removeHandler(self.debug_logger)
            self.add_debug_logger(file_formatter, out_dir)
