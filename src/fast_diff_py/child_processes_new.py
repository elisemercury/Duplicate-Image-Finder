import logging
import multiprocessing as mp
import os
import queue
import time
import traceback
import datetime
from logging.handlers import QueueHandler
from typing import Tuple, Callable, Dict, Optional, Union

import numpy as np

import fast_diff_py.img_processing as imgp
from fast_diff_py.base_process import GracefulWorker
from fast_diff_py.cache import BatchCache
from fast_diff_py.datatransfer_new import PreprocessArg, PreprocessResult, BatchCompareArgs, BatchCompareResult, \
    ItemCompareArgs, ItemCompareResult


class ChildProcess(GracefulWorker):
    logger: logging.Logger = None
    log_queue: mp.Queue = None
    timeout: int
    processing_fn: Callable[..., ...] = None

    # Queues:
    cmd_queue: mp.Queue
    res_queue: mp.Queue

    block_timeout: int = 0.01

    def __init__(self, identifier: int,
                 cmd_queue: mp.Queue,
                 res_queue: mp.Queue,
                 log_queue: mp.Queue,
                 log_level: int = logging.DEBUG,
                 timeout: int = 30):

        super().__init__(identifier)
        self.timeout = timeout
        self.cmd_queue = cmd_queue
        self.res_queue = res_queue
        self.prep_logging(level=log_level, q=log_queue)

        self.fetch_arg = 0
        self.put_res = 0

    def main(self):
        """
        Main function to run the child process
        """
        self.set_processing_function()

        count = 0
        while count < self.timeout and self.run:
            try:
                s = datetime.datetime.now(datetime.UTC)
                arg = self.cmd_queue.get(block=True, timeout=self.block_timeout)
                self.fetch_arg += (datetime.datetime.now(datetime.UTC) - s).total_seconds()
                count = 0
            except queue.Empty:
                self.logger.warning("Starving...")
                count += self.block_timeout
                continue

            # Break if we get a None
            if arg is None:
                self.res_queue.put(None)
                self.logger.info("Received None. Shutting down")
                self.print_stats()
                return

            # Batching support via lists
            if isinstance(arg, list):
                res = []
                for a in arg:
                    res.append(self.processing_fn(a))
                self.res_queue.put(res)
            else:
                # Perform the processing
                s = datetime.datetime.now(datetime.UTC)
                self.res_queue.put(self.processing_fn(arg))
                self.put_res += (datetime.datetime.now(datetime.UTC) - s).total_seconds()

        if count >= self.timeout:
            self.res_queue.put(None)
            self.logger.warning("Timeout reached. Shutting down")

        self.print_stats()

    def set_processing_function(self):
        """
        Set the processing function based on the configuration
        """
        raise NotImplementedError("This function needs to be implemented in the child class")

    def prep_logging(self, level: int = logging.DEBUG, q: mp.Queue = None):
        """
        Prepare the logging for the child process
        """
        self.logger = logging.getLogger(f"Child_{self.identifier:03}")
        self.logger.setLevel(level)
        self.log_queue = q
        q_handler = QueueHandler(q)
        self.logger.addHandler(q_handler)

    def print_stats(self):
        """
        Print timing statistics needed for debugging
        """
        self.logger.info(f"Fetching Args took: {self.fetch_arg}")
        self.logger.info(f"Putting Results took: {self.put_res}")


class FirstLoopWorker(ChildProcess):
    processing_fn: Callable[[PreprocessArg], PreprocessResult] = None

    def __init__(self, identifier: int,
                 compress: bool,
                 do_hash: bool,
                 target_size: Tuple[int, int],
                 cmd_queue: mp.Queue,
                 res_queue: mp.Queue,
                 log_queue: mp.Queue,
                 shift_amount: int = None,
                 thumb_dir: str = None,
                 hash_fn: Callable = None,
                 log_level: int = logging.DEBUG,
                 timeout: int = 30):
        """
        Initialize the First Loop Worker

        :param identifier: The identifier of the worker
        :param log_level: The log level of the worker
        :param log_queue: The queue to log to
        """
        super().__init__(identifier=identifier,
                         log_queue=log_queue,
                         cmd_queue=cmd_queue,
                         res_queue=res_queue,
                         log_level=log_level,
                         timeout=timeout)

        if do_hash is False and compress is False:
            raise ValueError("At least one of do_hash or compress must be True")

        self.do_hash = do_hash
        self.compress = compress
        self.shift_amount = shift_amount
        self.thumb_dir = thumb_dir
        self.target_size = target_size

        if hash_fn is not None:
            self.hash_fn = hash_fn
        else:
            self.hash_fn = imgp.hash_file

    def prep_logging(self, level: int = logging.DEBUG, q: mp.Queue = None):
        """
        Prepare the logging for the child process
        """
        self.logger = logging.getLogger(f"FirstLoopWorker_{self.identifier:03}")
        self.logger.setLevel(level)
        self.log_queue = q
        q_handler = QueueHandler(q)
        self.logger.addHandler(q_handler)

    def set_processing_function(self):
        """
        Set the first loop function to the correct function based on the configuration
        """
        if self.do_hash and self.compress:
            self.processing_fn = self.compress_and_hash
        elif self.do_hash:
            self.processing_fn = self.compute_hash
        elif self.compress:
            self.processing_fn = self.compress_only
        else:
            raise ValueError("At least one of do_hash or compress must be True")

    def compute_hash(self, arg: PreprocessArg) -> PreprocessResult:
        """
        Compute only the hash for a given image.

        :param arg: The PreprocessArg containing the file path
        """
        try:
            img: np.ndarray = imgp.load_std_image(img_path=arg.file_path, target_size=self.target_size, resize=True)
            h0, h90, h180, h270 = imgp.compute_img_hashes(image_mat=img,
                                                          temp_dir=self.thumb_dir,
                                                          temp_name=f"{self.identifier}_temp.png",
                                                          shift_amount=self.shift_amount,
                                                          hash_fn=self.hash_fn)

            return PreprocessResult(key=arg.key, hash_0=h0, hash_90=h90, hash_180=h180, hash_270=h270,
                                    org_x=img.shape[0], org_y=img.shape[1])
        except Exception as e:
            self.logger.error(f"Error in processing batch: {e}")
            tb = traceback.format_exc()
            return PreprocessResult(key=arg.key, error=tb)

    def compress_only(self, arg: PreprocessArg) -> PreprocessResult:
        """
        Compute the thumbnail for a given image.

        :param arg: The PreprocessArg containing the file path
        """
        try:
            img: np.ndarray = imgp.load_std_image(img_path=arg.file_path, target_size=self.target_size, resize=True)
            imgp.store_image(img, os.path.join(self.thumb_dir, f"{arg.key}.png"))
            return PreprocessResult(key=arg.key, org_x=img.shape[0], org_y=img.shape[1])
        except Exception as e:
            self.logger.error(f"Error in processing batch: {e}")
            tb = traceback.format_exc()
            return PreprocessResult(key=arg.key, error=tb)

    def compress_and_hash(self, arg: PreprocessArg):
        """
        Compute hash and store thumbnail.

        :param arg: The PreprocessArg containing the file path
        """
        try:
            img: np.ndarray = imgp.load_std_image(img_path=arg.file_path, target_size=self.target_size, resize=True)
            hash_0, hash_90, hash_180, hash_270 = imgp.compute_img_hashes(image_mat=img,
                                                                          temp_dir=self.thumb_dir,
                                                                          temp_name=f"{self.identifier}_temp.png",
                                                                          shift_amount=self.shift_amount,
                                                                          hash_fn=self.hash_fn)
            imgp.store_image(img, os.path.join(self.thumb_dir, f"{arg.key}.png"))

            return PreprocessResult(key=arg.key,
                                    org_x=img.shape[0], org_y=img.shape[1],
                                    hash_0=hash_0, hash_90=hash_90, hash_180=hash_180, hash_270=hash_270)
        except Exception as e:
            self.logger.error(f"Error in processing batch: {e}")
            tb = traceback.format_exc()
            return PreprocessResult(key=arg.key, error=tb)


class SecondLoopWorker(ChildProcess):
    is_compressed: bool
    has_dir_b: bool
    batched_args: bool
    target_size: Optional[Tuple[int, int]] = None

    ram_cache: Optional[Dict[int, BatchCache]] = None
    plot_dir: Optional[str] = None
    plot_threshold: Optional[float] = None
    delta_fn: Callable[[np.ndarray[np.uint8], np.ndarray[np.uint8]], float]

    key_a: int = -1
    key_b: int = -1

    img_a_mat: Optional[np.ndarray] = None
    img_b_mat: Optional[np.ndarray] = None

    cache_key: Optional[int] = None

    processing_fn: Union[
        Callable[[BatchCompareArgs], BatchCompareResult],
        Callable[[ItemCompareArgs], ItemCompareResult]]

    def __init__(self,
                 identifier: int,
                 cmd_queue: mp.Queue,
                 res_queue: mp.Queue,
                 log_queue: mp.Queue,

                 is_compressed: bool,
                 compare_fn: Callable[[np.ndarray[np.uint8], np.ndarray[np.uint8]], float],
                 target_size: Tuple[int, int],
                 has_dir_b: bool = False,
                 ram_cache: Dict[int, BatchCache] = None,
                 plot_dir: str = None,
                 batched_args: bool = True,
                 thumb_dir: str = None,
                 plot_threshold: float = None,

                 log_level: int = logging.DEBUG,
                 timeout: int = 30):

        super().__init__(identifier=identifier,
                         log_queue=log_queue,
                         cmd_queue=cmd_queue,
                         res_queue=res_queue,
                         log_level=log_level,
                         timeout=timeout)

        # Flags
        self.is_compressed = is_compressed
        self.has_dir_b = has_dir_b
        self.target_size = target_size
        self.ram_cache = ram_cache
        self.plot_dir = plot_dir
        self.plot_threshold = plot_threshold
        self.batched_args = batched_args
        self.thumb_dir = thumb_dir

        self.delta_fn = compare_fn

        # Checks on arguments
        if plot_dir is not None and batched_args:
            raise ValueError("Cannot make plots with batched arguments")

        # Set the processing function
        if self.ram_cache is not None and self.thumb_dir is not None:
            self.generic_fetch_image = self.get_image_from_cache
        elif self.ram_cache is not None and self.thumb_dir is None:
            self.generic_fetch_image = self.get_image_from_cache
        elif self.ram_cache is None and self.thumb_dir is not None:
            self.generic_fetch_image = self.get_thumb_path
        elif self.ram_cache is None and self.thumb_dir is None:
            self.generic_fetch_image = self.get_org_from_path
        else:
            raise ValueError("Tertiem Non Datur. This should not happen")

        self.set_processing_function()

    def generic_fetch_image(self, key: int = None, path: str = None, is_x: bool = True) -> np.ndarray[np.uint8]:
        """
        Generic function to fetch an image
        """
        raise NotImplementedError("This function needs to be implemented in the child class")

    def get_image_from_cache(self, key: int, is_x: bool = True, **kwargs) -> np.ndarray[np.uint8]:
        """
        Get an image from the cache

        :param key: The key of the image (so the key from the directory table)
        :param is_x: Whether we are looking for the x or y image (determines the cache we're going to use
        :kwargs: Additional arguments to match a call from the generic_fetch_image method

        :return: The image from the cache
        """
        if self.ram_cache is None:
            raise ValueError("Cache is not set")

        if is_x:
            return self.ram_cache[self.cache_key].x.get_image(key)
        else:
            return self.ram_cache[self.cache_key].y.get_image(key)

    def get_thumb_path(self, key: int, **kwargs) -> np.ndarray[np.uint8]:
        """
        Load a Thumbnail given a key

        :param key: The key of the image
        :kwargs: Additional arguments to match a call from the generic_fetch_image method

        :return: The image from the thumbnail directory
        """
        p = os.path.join(self.thumb_dir, f"{key}.png")
        return imgp.load_std_image(img_path=p, target_size=self.target_size, resize=False)

    def get_org_from_path(self, path: str, **kwargs) -> np.ndarray[np.uint8]:
        """
        Get an original image from a path

        :param path: The path to the image
        :kwargs: Additional arguments to match a call from the generic_fetch_image method

        :return: The image from the path
        """
        return imgp.load_std_image(img_path=path, target_size=self.target_size, resize=True)

    def process_batch_paths(self, arg: BatchCompareArgs) -> BatchCompareResult:
        """
        Process a batch of images and return the results in the BatchCompareResult format
        Function is intended for no ram cache and no thumb.

        :param arg: The arguments for the batch
        :return: The results of the batch
        """
        self.cache_key = arg.cache_key

        # Get the size we need to walk for the batch
        if self.has_dir_b:
            size = arg.max_size_b
        else:
            size = min(arg.key_b - arg.key_a, arg.max_size_b)

        # Size of the path array
        pb_size = len(arg.path_b)

        # Prepare the diffs and errors
        diffs = []
        errors = {}

        try:
            img_a = self.generic_fetch_image(key=arg.key_a, path=arg.path_a, is_x=True)

            for i in range(size):
                d_key = arg.key - i
                thumb_key = arg.key_b - i
                p_key = pb_size - 1 - i

                try:
                    img_b = self.generic_fetch_image(key=thumb_key, path=arg.path_b[p_key], is_x=False)
                    diff = self.delta_fn(img_a, img_b)
                    diffs.append(diff)
                except Exception as e:
                    self.logger.exception(f"Error in processing Tuple: {arg.key_a}, {thumb_key}", exc_info=e)
                    tb = traceback.format_exc()
                    diffs.append(-1)
                    errors[d_key] = tb

            return BatchCompareResult(key=arg.key,
                                      key_a=arg.key_a, key_b=arg.key_b,
                                      diff=diffs, errors=errors,
                                      cache_key=arg.cache_key)

        except Exception as e:
            self.logger.error(f"Error with image a in batch {arg.key_a}: {e}", exc_info=e)
            tb = traceback.format_exc()
            diffs = [-1 for _ in range(size)]
            errors =  {arg.key - i: tb for i in range(size)}
            return BatchCompareResult(key=arg.key,
                                      key_a=arg.key_a, key_b=arg.key_b,
                                      diff=diffs, errors=errors,
                                      cache_key=arg.cache_key)

    def process_batch_thumb(self, arg: BatchCompareArgs) -> BatchCompareResult:
        """
        Process a batch of images and return the results in the BatchCompareResult format
        Intended for cases when thumbnails exist or when we have a ram cache

        :param arg: The arguments for the batch
        :return: The results of the batch
        """
        self.cache_key = arg.cache_key

        # Get the size we need to walk for the batch
        if self.has_dir_b:
            size = arg.max_size_b
        else:
            size = min(arg.key_b - arg.key_a, arg.max_size_b)

        # Prepare the diffs and errors
        diffs = []
        errors = {}

        try:
            img_a = self.generic_fetch_image(key=arg.key_a, path=arg.path_a, is_x=True)

            for i in range(size):
                d_key = arg.key - i
                thumb_key = arg.key_b - i

                try:
                    img_b = self.generic_fetch_image(key=thumb_key, is_x=False, path="")
                    diff = self.delta_fn(img_a, img_b)
                    diffs.append(diff)
                except Exception as e:
                    self.logger.exception(f"Error in processing Tuple: {arg.key_a}, {thumb_key}", exc_info=e)
                    tb = traceback.format_exc()
                    diffs.append(-1)
                    errors[d_key] = tb

            return BatchCompareResult(key=arg.key,
                                      key_a=arg.key_a, key_b=arg.key_b,
                                      diff=diffs, errors=errors,
                                      cache_key=arg.cache_key)

        except Exception as e:
            self.logger.error(f"Error with image a in batch {arg.key_a}: {e}", exc_info=e)
            tb = traceback.format_exc()
            diffs = [-1 for _ in range(size)]
            errors =  {arg.key - i: tb for i in range(size)}
            return BatchCompareResult(key=arg.key,
                                      key_a=arg.key_a, key_b=arg.key_b,
                                      diff=diffs, errors=errors,
                                      cache_key=arg.cache_key)

    def process_item(self, arg: ItemCompareArgs) -> ItemCompareResult:
        """
        Process a single item
        """
        diff = -1
        try:
            self.cache_key = arg.cache_key

            # Fetch the images
            if self.key_a != arg.key_a:
                self.key_a = arg.key_a
                self.img_a_mat = self.generic_fetch_image(key=arg.key_a, path=arg.path_a, is_x=True)

            if self.key_b != arg.key_b:
                self.key_b = arg.key_b
                self.img_b_mat = self.generic_fetch_image(key=arg.key_b, path=arg.path_b, is_x=False)

            # Typing override
            self.img_a_mat: np.ndarray[np.uint8]
            self.img_b_mat: np.ndarray[np.uint8]

            # Compute the difference
            diff = self.delta_fn(self.img_a_mat, self.img_b_mat)
            res =  ItemCompareResult(key=arg.key, diff=diff)
        except Exception as e:
            self.logger.error(f"Error in processing item: {e}")
            tb = traceback.format_exc()
            res =  ItemCompareResult(key=arg.key, error=tb, diff=diff)

        # Optionally, make plot
        if self.plot_dir is not None and diff < self.plot_threshold:
            try:
                if self.is_compressed:
                    img_a = imgp.load_std_image(img_path=arg.path_a, target_size=self.target_size, resize=False)
                    img_b = imgp.load_std_image(img_path=arg.path_b, target_size=self.target_size, resize=False)
                else:
                    img_a = self.img_a_mat
                    img_b = self.img_b_mat

                imgp.make_dif_plot(min_diff=diff,
                                   img_a=os.path.basename(arg.path_a), img_b=os.path.basename(arg.path_b),
                                   mat_a=img_a, mat_b=img_b,
                                   store_path=os.path.join(self.plot_dir, f"{arg.key}.png"))
            except Exception as e:
                self.logger.exception(f"Error in making plot: {e}", exc_info=e)

        return res

    def set_processing_function(self):
        """
        Set the processing function based on the configuration
        """
        if self.batched_args:
            if self.thumb_dir is None and self.ram_cache is None:
                self.processing_fn = self.process_batch_paths
            else:
                self.processing_fn = self.process_batch_thumb
        else:
            self.processing_fn = self.process_item

    def prep_logging(self, level: int = logging.DEBUG, q: mp.Queue = None):
        """
        Prepare the logging for the child process
        """
        self.logger = logging.getLogger(f"SecondLoopWorker_{self.identifier:03}")
        self.logger.setLevel(level)
        self.log_queue = q
        q_handler = QueueHandler(q)
        self.logger.addHandler(q_handler)
