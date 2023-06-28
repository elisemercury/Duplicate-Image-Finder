from fast_diff_py.cpu_image_processor import CPUImageProcessing
from fast_diff_py.datatransfer import PreprocessArguments, PreprocessResults, CompareImageArguments, CompareImageResults
import multiprocessing as mp
import warnings
import queue
import os
from typing import Tuple
from types import FunctionType

def process_image(proc: CPUImageProcessing, args: PreprocessArguments) -> PreprocessResults:
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


def parallel_resize(iq: mp.Queue, output: mp.Queue, identifier: int, try_cupy: bool, verbose: bool = False) -> bool:
    """
    Parallel implementation of first loop iteration.

    :param iq: input queue containing arguments dict or
    :param output: output queue containing only json strings of obj
    :param identifier: id of running thread
    :param try_cupy: check if cupy is available and use cupy instead.
    :param verbose: If true, adds print statements.
    :return: True, running was successful and no error encountered, otherwise exit without return or return False
    """
    timeout = 0

    # try to use cupy if it is indicated by arguments
    cupy_avail = False
    if try_cupy:
        try:
            import cupy as cp
            cupy_avail = True
        except ImportError:
            warnings.warn(f"{identifier:03}: Cupy not available. Using CPU instead.")

    if cupy_avail:
        from fast_diff_py.gpu_image_processor import GPUImageProcessing
        img_proc = GPUImageProcessing(identifier=identifier)
    else:
        img_proc = CPUImageProcessing(identifier=identifier)

    # stay awake for 60s, otherwise kill
    while timeout < 60:
        try:
            args_str = iq.get(timeout=1)
        except queue.Empty:
            timeout += 1
            # print(f"{identifier:03} Timeout Parallel Resize")
            continue

        if args_str is None:
            # print(f"{identifier:03} Terminating Parallel Resize")
            break

        args = PreprocessArguments.from_json(args_str)
        timeout = 0

        result = process_image(img_proc, args)
        if verbose:
            print(f"{identifier:03}: Done with {os.path.basename(args.in_path)}")

        # Sending the result to the handler
        output.put(result.to_json())

    # Putting a None in the output to detect when all processes have exited.
    output.put(None, block=True)
    return True


def parallel_compare(in_q: mp.Queue, out_q: mp.Queue, identifier: int, try_cupy: bool,
                     sc_size: bool = False, sc_hash: bool = False, verbose: bool = False) -> bool:
    """
    Parallel implementation of first loop iteration.

    :param verbose: adds more print statements to get an overview about the executing workers.
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
        try:
            import cupy as cp
            cupy_avail = True
        except ImportError:
            warnings.warn(f"{identifier:03}: Cupy not available. Using CPU instead.")

    if cupy_avail:
        from fast_diff_py.gpu_image_processor import GPUImageProcessing
        processor = GPUImageProcessing(identifier=identifier)
    else:
        processor = CPUImageProcessing(identifier=identifier)

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
        result = CPUImageProcessing.short_circuit(args=args, sc_size=sc_size, sc_hash=sc_hash)
        if result is not None:
            assert type(result) is CompareImageResults, f"Unexpected Return Type of Short Circuiting function. \n" \
                                                        f"CompareImageResults expected, got {type(result).__name__}"

            if verbose:
                print(f"{identifier:03}: Done with {os.path.basename(args.img_a)} and "
                      f"{os.path.basename(args.img_b)} - short circuiting")

            # Sending the result to the handler
            out_q.put(result.to_json())
            continue

        processor.update_compare_args(args)
        processor.compare_images()
        processor.store_plt_on_threshold()
        result = processor.create_compare_result()

        if verbose:
            print(f"{identifier:03}: Done with {os.path.basename(args.img_a)} and {os.path.basename(args.img_b)}")

        # Sending the result to the handler
        out_q.put(result.to_json())

    out_q.put(None, block=True)
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
