from database import Database
import os
from typing import List, Tuple
import warnings
from utils import *
import multiprocessing as mp
import queue
from datatransfer import *
from image_processor import ImageProcessing
from concurrent.futures import ProcessPoolExecutor, Future

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

# TODO test cuda functionality
# TODO create unified handler for the parallel functions
# TODO Make a skeleton for the parallel process
# TODO Test the whole shit.
# TODO Implement process stop recovery.
# TODO single processing handler
# TODO add handler in main function for second foor loop
# TODO Harakiri method. More reckless method.
# TODO Reset Processing Class if the arguments are switched.


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
        print("Cupy version currenetly not implemented")

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


def parallel_compare(in_q: mp.Queue, out_q: mp.Queue, identifier: int, try_cupy: bool) -> bool:
    """
    Parallel implementation of first loop iteration.

    :param in_q: input queue containing arguments dict or
    :param out_q: output queue containing only json strings of obj
    :param identifier: id of running thread
    :param try_cupy: check if cupy is available and use cupy instead.
    :return: True, running was successful and no error encountered, otherwise exit without return or return False
    """
    timeout = 0

    # try to use cupy if it is indicated by arguments
    cupy_avail = False
    if try_cupy:
        print("Cupy version currently not implemented")

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

        print(f"{identifier:03}: Done with {os.path.basename(args.in_path)}")

        # Sending the result to the handler
        out_q.put(result.to_json())

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

    # relative to child processes
    first_loop_in: mp.Queue = None  # the tasks sent to the child processes
    first_loop_out: mp.Queue = None  # the results coming from the child processes

    second_loop_in: List[mp.Queue] = None
    second_loop_out: mp.Queue = None
    second_loop_queue_status: List[dict] = None

    cpu_handles = None
    gpu_handles = None

    def __init__(self, directory_a: str, directory_b: str = None, test_db: bool = True):
        """
        Provide the directories to be searched. If a different implementation of the database is used,
        set the test_db to false.

        :param directory_a: first directory to search for differentiation.
        :param directory_b: second directory to compare against. Otherwise, comparison will be done against directory
        itself.
        :param test_db: Weather or not the code should test for the presence of the default sqlite database.
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

    def index_the_dirs(self):
        """
        List all the files in directory_a and possibly directory_b and store the paths and filenames in the temporary
        database.
        :return:
        """
        # create the tables in the database
        self.db.create_directory_tables(secondary_folder=self.p_root_dir_b is not None)

        self.recursive_index(True)
        if self.p_root_dir_b is not None:
            self.recursive_index(False)

    def recursive_index(self, dir_a: bool = True, path: str = None, ignore_thumbnail: bool = True):
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

        print(
            f"Estimated disk usage by {fill(str(len(self.p_root_dir_a)), target)}: " + h(byte_count_a, "B") + " bytes"
        )
        print(
            f"Estimated disk usage by {fill(str(len(self.p_root_dir_b)), target)}: " + h(byte_count_b, "B") + " bytes"
        )
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
        return os.path.join(directory, name)

    def first_loop_iteration(self, compute_thumbnails: bool = True, compute_hash: bool = False, amount: int = 4,
                             gpu_proc: int = 0, cpu_proc: int = 16):

        # TODO MAKE EVERYTHING WITH ProcesspoolExecutor
        # store thumbnails if possible.
        if compute_hash:
            if amount == 0:
                print("WARNING: amount 0, only EXACT duplicates are detected like this.")

            if amount > 7 or amount < -7:
                raise ValueError("amount my only be in range [-7, 7]")

            self.db.create_hash_table()

        # thumbnail are required to exist for both.
        if compute_thumbnails or compute_hash:
            self.db.create_thumb_table(secondary_folder=self.p_root_dir_b is not None)
            self.check_create_thumbnail_dir()

        cpu_handles = []
        gpu_handles = []

        self.first_loop_in = mp.Queue(maxsize=(cpu_proc + gpu_proc) * 2)
        self.first_loop_out = mp.Queue()

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
                size_y=self.thumbnail_size_y,
            )

            self.first_loop_in.put(arg.to_json())

        # start processes for cpu
        for i in range(cpu_proc):
            p = mp.Process(target=parallel_resize, args=(self.first_loop_in, self.first_loop_out, i, False))
            p.start()
            cpu_handles.append(p)

        # start processes for gpu
        for i in range(cpu_proc, gpu_proc + cpu_proc):
            p = mp.Process(target=parallel_resize, args=(self.first_loop_in, self.first_loop_out, i, True))
            p.start()
            gpu_handles.append(p)

        # turn main loop into handler and perform monitoring of the threads.
        run = True
        none_counter = 0
        timeout = 0

        # handle the running state of the loop
        while run:
            if self.handle_result_of_first_loop(self.first_loop_out, compute_hash):
                task = self.db.get_next_to_process()

                # if there's no task left, stop the loop.
                if task is None:
                    none_counter += 1
                    self.first_loop_in.put(None)

                else:
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

                    self.first_loop_in.put(arg.to_json())
                    timeout = 0
            else:
                timeout += 1

            # if this point is reached, all processes should be done and the queues empty.
            if none_counter >= cpu_proc + gpu_proc:
                run = False

            # at this point we should have been idling for 60s
            if timeout > 60:
                print("Timeout reached, stopping.")
                run = False

        # adding Nones just for good measure.
        counter = 0
        while not self.first_loop_in.full() and counter < 1000:
            self.first_loop_in.put(None)
            counter += 1

        # all processes should be done now, iterating through and killing them if they're still alive.
        for i in range(len(cpu_handles)):
            p = cpu_handles[i]
            try:
                print(f"Trying to join process {i} Process State is {p.is_alive()}")
                p.join(60)
            except TimeoutError:
                print(f"Process {i} timed out. Alive state: {p.is_alive()}; killing it.")
                p.kill()

        for i in range(len(gpu_handles)):
            p = gpu_handles[i]
            try:
                print(f"Trying to join process {i + cpu_proc} Process State is {p.is_alive()}")
                p.join(60)
            except TimeoutError:
                print(f"Process {i + cpu_proc} timed out. Alive state: {p.is_alive()}; killing it.")
                p.kill()

        # try to handle any remaining results that are in the queue.
        for _ in range((cpu_proc + gpu_proc) * 2):
            if not self.handle_result_of_first_loop(self.first_loop_out, compute_hash):
                break

        assert self.first_loop_out.empty(), "Result queue is not empty after all processes have been killed."
        print("All Images have been preprocessed.")

    def handle_result_of_first_loop(self, res_q: mp.Queue, compute_hash: bool) -> bool:
        """
        Dequeues a result of the results queue and updates the database accordingly.
        :param res_q: results queue
        :param compute_hash: if the hash was computed
        :return: if a result was handled.
        """
        # retrieve the result from the queue
        try:
            res = res_q.get(timeout=1)
        except queue.Empty:
            return False

        # sanitize result
        assert type(res) is str, "Result is not a string"
        result_obj = PreprocessResults.from_json(res)

        # Handle the case when an error occurred.
        if not result_obj.success:
            self.db.update_dir_error(key=result_obj.key, dir_a=result_obj.dir_a, msg=result_obj.error)
            return True

        # store the hash if computed
        if compute_hash:
            # Drop hashes if they are only partly computed.
            if not self.db.has_all_hashes(dir_a=result_obj.dir_a, dir_key=result_obj.key):
                self.db.del_all_hashes(dir_a=result_obj.dir_a, dir_key=result_obj.key)

            # Store all hashes
            self.db.insert_hash(dir_a=result_obj.dir_a, dir_key=result_obj.key, fhash=result_obj.hash_0, rotation=0)
            self.db.insert_hash(dir_a=result_obj.dir_a, dir_key=result_obj.key, fhash=result_obj.hash_90, rotation=90)
            self.db.insert_hash(dir_a=result_obj.dir_a, dir_key=result_obj.key, fhash=result_obj.hash_180, rotation=180)
            self.db.insert_hash(dir_a=result_obj.dir_a, dir_key=result_obj.key, fhash=result_obj.hash_270, rotation=270)

        # mark file as processed only if the other data was inserted.
        self.db.update_dir_success(key=result_obj.key, dir_a=result_obj.dir_a, px=result_obj.original_x,
                                   py=result_obj.original_y)

        # to be sure commit here.
        self.db.con.commit()
        return True

    def clean_up(self):
        # TODO remove the thumbnails
        # TODO remove database (if desired)
        print("Not implemented yet")

    def second_loop_iteration(self, similarity_threshold: float, make_diff_plots: bool, default_diff_location: str,
                            only_matching_aspect: bool, only_same_hash: bool, gpu_proc: int = 0, cpu_proc: int = 16):

        self.cpu_handles = []
        self.gpu_handles = []

        # create queues
        self.second_loop_out = mp.Queue()
        self.second_loop_in = [mp.Queue(100) for _ in range(cpu_proc + gpu_proc)]

        child_args = [(self.second_loop_in[i], self.second_loop_out, i, False if i < cpu_proc else True)
                      for i in range(gpu_proc, cpu_proc)]

        # prefill


        # create process pool.
        ex = ProcessPoolExecutor(max_workers=cpu_proc + gpu_proc)

        # starting all processes
        for i in range(cpu_proc):
            self.cpu_handles.append(ex.submit(parallel_compare, child_args[i]))

        for i in range(cpu_proc, cpu_proc + gpu_proc):
            self.gpu_handles.append(ex.submit(parallel_compare, child_args[i]))

        done = False

        # update everything
        while not done:
            # update the queues and store if there are more tasks to process
            done = not self.update_queues()

            # exit the while loop if all children have exited.
            _, _, _, all_exited = self.check_children(cpu=cpu_proc > 0, gpu=gpu_proc > 0)
            if all_exited:
                done = True

        # check if it was the children's fault
        _, all_errored, _, _ = self.check_children(cpu=cpu_proc > 0, gpu=gpu_proc > 0)

        if all_errored:
            raise RuntimeError("All child processes exited with an Error")

        if self.join_all_children():
            print("All child processes terminated sucessfully and without errors")

        ex.shutdown()

        # check if the tasks were empty.
        assert not self.update_queues(), "Existed without having run out of tasks and without all processes " \
                                         "having stopped."

    def join_all_children(self):
        success = True

        for f in self.gpu_handles:
            success = success and f.result()

        for g in self.cpu_handles:
            success = success and g.result()

        return success

    def check_children(self, gpu: bool = False, cpu: bool = False):
        # error, all_error, exited, all_exited
        error = False
        all_error = True
        exited = False
        all_exited = True

        # info, results can be fetched twice
        # check on the gpu tasks
        if gpu:
            error, all_error, exited, all_exited = self.check_futures(self.gpu_handles)

        if cpu:
            er, a_er, ex, a_ex = self.check_futures(self.cpu_handles)
            error = error or er
            all_error = all_error and a_er
            exited = exited or ex
            all_exited = all_exited and a_ex

        return error, all_error, exited, all_exited

    @staticmethod
    def check_futures(futs: List[Future]) -> Tuple[bool, bool, bool, bool]:
        error = False
        all_error = True
        exited = False
        all_exited = True

        for fut in futs:
            # if it is running, it has not exited and not errored
            if not fut.running():
                e = None

                # try to fetch the error of the task
                try:
                    e = fut.exception(timeout=1)
                except TimeoutError:
                    print("Failed to get exception from Process")

                # update the flags
                if e is None:
                    all_error = False
                else:
                    print(f"Error occurred: {e}")
                    error = True

                exited = exited or fut.done()

            else:
                all_error = False
                all_exited = False

        return error, all_error, exited, all_exited
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
        if os.path.exists(value):
            self.__p_root_dir_b = value
            self.__thumb_dir_b = os.path.join(self.__p_root_dir_b, ".temp_thumbnails")

    @property
    def thumb_dir_a(self):
        return self.__thumb_dir_a

    @property
    def thumb_dir_b(self):
        return self.__thumb_dir_b
