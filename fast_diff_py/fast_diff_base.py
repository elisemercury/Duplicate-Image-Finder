from fast_diff_py.database import Database
import os
from typing import List, Tuple
import multiprocessing as mp
import queue
from fast_diff_py.datatransfer import *
from fast_diff_py.config import FastDiffPyConfig

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
            self.config = FastDiffPyConfig(cfg=cfg)
            self.config.retain_config = False


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

    def sl_refill_queues(self, in_queue: Union[List[mp.Queue], mp.Queue]) -> Tuple[int, int]:
        """
        Call to either the optimized or non optimized filler.

        :return:
        """
        # testing if the
        if self.config.less_optimized:
            return self.__refill_queues_non_optimized(target_queue=in_queue)

        assert type(self.config.sl_queue_status) is list, f"Unexpected type of config.sl_queue_status: " \
                                                            f"{type(self.config.sl_queue_status).__name__}, " \
                                                            f"valid are list and dict"

        if self.config.has_dir_b and self.config.sl_use_special_b_algo:
            return self._refill_queues_optimized_b(in_queue=in_queue)
        else:
            return self._refill_queues_optimized_base(queue_list=in_queue)

    def _smart_increment_fixed_image(self, p: int, in_queue: List[mp.Queue]):
        """
        Given a process p, it searches for the next 'row' in the matching matrix to find the next key to keep constant
        for the process p

        :param p: index of process spec in self.config.sl_queue_status
        :return: True -> free image found, False, -> no new image found.
        """
        next_key = 0

        if "parent" in self.config.sl_queue_status[p].keys():
            if self._smart_check_indirection(p=p):
                return True

            if not in_queue[p].full():
                in_queue[p].put(None)
            return False

        # get the limit for the next key
        for i in range(len(self.config.sl_queue_status)):
            # select proper status
            if "parent" in self.config.sl_queue_status[i].keys():
                target_status = self.config.sl_queue_status[self.config.sl_queue_status[i]["parent"]]
            else:
                target_status = self.config.sl_queue_status[i]

            if self.config.has_dir_b:
                if not self.config.sl_base_a:
                    next_key = max(target_status["row_b"]["key"], next_key)
                    continue

            next_key = max(target_status["row_a"]["key"], next_key)

        # process case, when we're looking to move the dir_b
        if not self.config.sl_base_a:
            rows = self.db.fetch_many_after_key(directory_a=False, starting=next_key, count=1)

            # no completely unprocessed key found
            if len(rows) == 0:
                if not in_queue[p].full():
                    in_queue[p].put(None)
                return False

            # update the dict
            self.config.sl_queue_status[p] = {"row_b": rows[0], "last_key": None}
            return True

        rows = self.db.fetch_many_after_key(directory_a=True, starting=next_key, count=1)

        # no completely unprocessed key found
        if len(rows) == 0:
            if self._smart_check_indirection(p=p):
                # Delete the unnecessary dict entries.
                del self.config.sl_queue_status[p]["last_key"]
                if "row_b" in self.config.sl_queue_status[p].keys():
                    del self.config.sl_queue_status[p]["row_b"]
                if "row_a" in self.config.sl_queue_status[p].keys():
                    del self.config.sl_queue_status[p]["row_a"]

                return True

            if not in_queue[p].full():
                in_queue[p].put(None)
            return False

        # update the dict
        self.config.sl_queue_status[p] = {"row_a": rows[0], "last_key": rows[0]["key"]}
        return True

    def _smart_check_indirection(self, p: int) -> bool:
        """
        Go through all processes and check if a new parent is available (so we coprocess a row in the matrix.)
        If this is not the case, we return False and proceed to put None's into the queue to tell the process to stop.

        :param p: index in the process status list, i.e. the current process id.
        :return: weather a new parent was found or not.
        """
        success = False
        for i in range(len(self.config.sl_queue_status)):
            if "parent" in self.config.sl_queue_status[i].keys():
                continue

            # Cannot be the parent of yourself.
            if i == p:
                continue

            # Find a new parent.
            self.config.sl_queue_status[p]["parent"] = i
            success = True
            break

        # increment the children of the process when it is the time that its row runs out of elements to process too
        for status in self.config.sl_queue_status:
            if "parent" in status.keys() and status["parent"] == p:
                status["parent"] = self.config.sl_queue_status[p]["parent"]

        return success

    def _smart_fetch_rows(self, p: int, count: int = 100) -> Tuple[list, list]:
        """
        Fetch the next up to 100 rows for the ingest process into the children.

        :param p: Index of the process
        :return:
        """
        row_a = []
        row_b = []
        assert type(self.config.sl_queue_status) is list, "__fetch_rows called with not_optimized process"

        # Alias for easier access:
        slqs = self.config.sl_queue_status

        # get the last key.
        if "parent" in slqs[p].keys():
            # get the last_key of the *parent* of the current second_loop_queue_status
            last_key = slqs[slqs[p]["parent"]]["last_key"]
        else:
            # get the last_key from the second_loop_queue_status
            last_key = slqs[p]["last_key"]

        # we don't keep the images of dir_a fixed but the ones of dir_b
        if not self.config.sl_base_a:
            row_a = self.db.fetch_many_after_key(directory_a=True, count=count, starting=last_key)
        # we keep the images of dir_b fixed
        else:
            row_b = self.db.fetch_many_after_key(directory_a=False, count=count, starting=last_key)
        return row_a, row_b


    def _refill_queues_optimized_b(self, in_queue: List[mp.Queue]):
        """
        Performs the optimized filling of the queues.

        :return:
        """
        assert self.config.has_dir_b, "May only be called with directory b selected."
        inserted = 0
        none_count = 0
        for p in range(len(in_queue)):
            # fetch possible candidates for the row.
            row_a, row_b = self._smart_fetch_rows(p=p)

            # if the rows are empty => Nothing left to do, skip updating for this process
            if len(row_a) == 0 and len(row_b) == 0:
                in_queue[p].put(None)
                continue

            inserted_count = 100

            not_full = True
            iterations = 0
            slqs = self.config.sl_queue_status

            while not_full:
                if self.config.sl_base_a:
                    for i in range(len(row_b)):
                        # Fetch the row from self or the parent.
                        row_a_tmp = slqs[slqs[p]["parent"]]["row_a"] if "parent" in slqs[p].keys() else slqs[p]["row_a"]

                        insertion_success, full = self._schedule_pair(row_a=row_a_tmp, row_b=row_b[i],
                                                                      in_queue=in_queue[p])
                        if full:
                            break
                        inserted_count -= int(insertion_success)
                        inserted += int(insertion_success)

                else:
                    for i in range(len(row_a)):
                        # Fetch the row from self or the parent.
                        row_b_tmp = slqs[slqs[p]["parent"]]["row_b"] if "parent" in slqs[p].keys() else slqs[p]["row_b"]

                        insertion_success, full = self._schedule_pair(row_a=row_a[i], row_b=row_b_tmp,
                                                                      in_queue=in_queue[p])
                        if full:
                            break
                        inserted_count -= int(insertion_success)
                        inserted += int(insertion_success)

                iterations += 1

                # get the correct slqs
                target = slqs[slqs[p]["parent"]] if "parent" in slqs[p].keys() else slqs[p]

                # update last key
                if not self.config.sl_base_a:
                    target["last_key"] = row_a[-1]["key"]
                else:
                    target["last_key"] = row_b[-1]["key"]

                row_a, row_b = self._smart_fetch_rows(p=p)

                # try to increment key. If the increment method returns False, then no more keys are available, so
                # stop trying to add more to the queue
                if len(row_a) == 0 and len(row_b) == 0:
                    # we don't have any images left to process.
                    if not self._smart_increment_fixed_image(p=p, in_queue=in_queue):
                        none_count += 1
                        break

                    row_a, row_b = self._smart_fetch_rows(p=p)

                    # case when we are at the last image (which can only be compared against itself,
                    # ergo nothing to do)
                    if len(row_a) == 0 and len(row_b) == 0:
                        break

                if inserted_count <= 0:
                    not_full = False

        return inserted, none_count

    def __refill_queues_non_optimized(self, target_queue: mp.Queue) -> Tuple[int, int]:
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
        assert ["fix_key", "shift_key", "done", "none_count"] == list(
            self.config.sl_queue_status.keys()), "Verify keys of sl_queue_status"

        none_count = 0
        if self.config.sl_queue_status["done"]:
            while self.config.sl_queue_status["none_count"] < self.config.sl_cpu_proc + self.config.sl_gpu_proc:
                try:
                    target_queue.put(None, block=False)
                    none_count += 1
                    self.config.sl_queue_status["none_count"] += 1
                except queue.Full:
                    break
            return 0, none_count

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
                    return add_count, none_count

                # verify that we have at least another image to compare if we don't have dir_b, so the fixed picture
                # is the second to last image in directory_a.
                elif not self.config.has_dir_b and len(next_row) == 1:
                    self.config.sl_queue_status["done"] = True
                    return add_count, none_count

                # We have at least one more row to go:
                self.config.sl_queue_status["fix_key"] = fix_key = next_row[0]["key"]
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
                    return add_count, none_count

                # regardless weather the insert was successful or aborted because of match aspect, set the config.
                self.config.sl_queue_status["shift_key"] = shift_key = row["key"]
                add_count += int(insert_success)

        # We added successfully the full number of images to the queue, return the add count.
        return add_count, none_count


    def _refill_queues_optimized_base(self, queue_list: List[mp.Queue]) -> Tuple[int, int]:
        """
        Performs the optimized filling of the queues.

        :return:
        """
        inserted = 0
        none_count = 0

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
                        none_count += 1
                        break

                    row_a, row_b = self._fetch_rows(p=p)

                    # case when we are at the last image (which can only be compared against itself,
                    # ergo nothing to do)
                    if len(row_a) == 0 and len(row_b) == 0:
                        break

                if inserted_count <= 0:
                    not_full = False

        return inserted, none_count

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

    def process_one_second_result(self, out_queue: mp.Queue) -> Tuple[bool, bool]:
        """
        Perform dequeue of one element of the second process results queue. Insert the result into the database
        subsequently.

        :param out_queue: Queue to dequeue the stuff from.

        :return: element processed (no timeout), if a process exited.
        """
        try:
            res = out_queue.get(block=False)
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

    def process_up_to_second_result(self, out_queue: mp.Queue, count: int = 1000) -> Tuple[int, int]:
        """
        Dequeue up to count elements from the output queue, aggregate the results and add them into one huge sql statement.

        :param out_queue: queue to dequeue from
        :param count: maximum number of elements to dequeue.

        :return: number of tasks processed, number of exited processes
        """

        task_counter = 0
        none_counter = 0
        successes = []
        errors = []

        for i in range(count):
            try:
                res = out_queue.get(timeout=0.1)
            except queue.Empty:
                break

            if res is None:
                none_counter += 1
                continue

            task_counter += 1
            res_obj = CompareImageResults.from_json(res)
            if res_obj.success:
                successes.append(res_obj)
            else:
                errors.append(res_obj)

        self.db.insert_many_diff_success(tasks=successes)
        self.db.insert_many_diff_errors(tasks=errors)
        return task_counter, none_counter