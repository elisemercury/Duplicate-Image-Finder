from fast_diff_py.cpu_image_processor import CPUImageProcessing
from fast_diff_py.mariadb_database import MariaDBDatabase
from fast_diff_py.fast_diff_base import FastDiffPyBase
from fast_diff_py.datatransfer import PreprocessArguments, PreprocessResults, CompareImageArguments, CompareImageResults
from fast_diff_py.datatransfer import Messages
import multiprocessing as mp
from multiprocessing.connection import Connection
import warnings
import queue
import os
from typing import Tuple, Union, List
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
            print(f"{identifier:03} Timeout Parallel Compare")
            timeout += 1
            continue

        if args_str is None:
            print(f"{identifier:03} Terminating Parallel Compare")
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


def build_base_obj(config: dict, db_config: dict) -> FastDiffPyBase:
    """
    Instantiate a FastDiffPyBase object and add the appropriate database.

    :param config: config for the FastDiffPyBase class
    :param db_config: config required for database.
    :return:
    """
    fdb = FastDiffPyBase(cfg=config)
    if db_config["type"] == "mariadb":
        mdb = MariaDBDatabase(user=db_config["user"],
                              password=db_config["password"],
                              host=db_config["host"],
                              port=db_config["port"],
                              database=db_config["database"],
                              table_suffix=db_config["table_suffix"],
                              **db_config["kwargs"],
                              purge=False)
        fdb.db = mdb
    else:
        raise ValueError(f"Unsupported database type {db_config['type']}")

    return fdb


def first_loop_enqueue_worker(target_queue: mp.Queue, com: Connection, config: dict, db_config: dict):
    """
    Enqueues until all images have been processed and the Nones have been submitted as well.

    :param target_queue: queue to enqueue the tasks into
    :param com: Pipe for communication with parent process
    :param config: config dict form parent object
    :param db_config: config for database to connect to it.
    :return:
    """
    fdb = build_base_obj(config=config, db_config=db_config)

    none_counter = 0
    insert_counter = 0
    current_task = None
    timeout = 0

    # Scheduling of tasks
    while True:
        if com.poll(timeout=0.01):
            msg = com.recv()

            # Iterate over message types and perform associated action.
            if msg == Messages.Stop:
                fdb.db.commit()
                return

        # fetching a new task if the current task is empty
        if current_task is None:
            current_task = fdb.generate_first_loop_obj()

        # exit loop if all elements are processed.
        if current_task is None:
            break

        # submit to queue
        try:
            target_queue.put(current_task.to_json(), timeout=1.0)
            fdb.db.commit()
            insert_counter += 1
            timeout = 0
            current_task = None
        except queue.Full:
            timeout += 1

        # prevent immortal process.
        if timeout > 60:
            com.send("First Loop Enqueue Worker timeout. Exit.")
            fdb.db.commit()
            return

        # Progress to parent
        if insert_counter % 100 == 0:
            com.send(f"Submitted: {insert_counter}")

    # Scheduling of tasks
    while True:
        if com.poll(timeout=0.01):
            msg = com.recv()

            # Iterate over message types and perform associated action.
            if msg == Messages.Stop:
                fdb.db.commit()
                return

        if none_counter >= fdb.config.fl_cpu_proc:
            fdb.db.commit()
            return

        # submit to queue
        try:
            target_queue.put(None, timeout=0.1)
            none_counter += 1
            timeout = 0
        except queue.Full:
            timeout += 1

        # prevent immortal process.
        if timeout > 60:
            com.send("First Loop Enqueue Worker timeout. Exit.")
            fdb.db.commit()
            return


def first_loop_dequeue_worker(target_queue: mp.Queue, com: Connection, config: dict, db_config: dict):
    """
    Dequeues until enough Nones have been received.

    :param target_queue: queue to dequeue from
    :param com: communication object to talk to parent.
    :param config: config to instantiate base class.
    :param db_config: config for database.
    :return:
    """
    fdb = build_base_obj(config=config, db_config=db_config)
    none_counter = 0
    result_counter = 0
    timeout = 0

    while none_counter < fdb.config.fl_cpu_proc:
        if com.poll(timeout=0.01):
            msg = com.recv()

            # Iterate over message types and perform associated action.
            if msg == Messages.Stop:
                fdb.db.commit()
                return

        proc_suc, proc_exit = fdb.handle_result_of_first_loop(target_queue)
        result_counter += int(proc_suc)
        none_counter += int(proc_exit)

        if proc_suc or proc_exit:
            timeout = 0
        else:
            timeout += 1

        if timeout > 60:
            com.send("First Loop Dequeue Worker timeout. Exit.")
            fdb.db.commit()
            return

        if result_counter % 100 == 0:
            com.send(f"Done with: {result_counter}")
            fdb.db.commit()

    fdb.db.commit()

def second_loop_enqueue_worker(target_queue: Union[mp.Queue, List[mp.Queue]], com: Connection, config: dict,
                               db_config: dict):
    fdb = build_base_obj(config=config, db_config=db_config)
    last_insert_count = 0
    last_none_count = 0
    timeout = 0

    insert_counter = 0
    none_counter = 0

    while True:
        if com.poll(timeout=0.01):
            msg = com.recv()

            # Iterate over message types and perform associated action.
            if msg == Messages.Stop:
                fdb.db.commit()
                return

        # fetching a new task if the current task is empty
        new_insert_count, new_none_counter = fdb.sl_refill_queues(target_queue)
        if not fdb.config.less_optimized:
            none_counter += new_none_counter
        else:
            none_counter = new_none_counter

        insert_counter += new_insert_count
        fdb.db.commit()

        # Timeout
        if insert_counter == last_insert_count and none_counter == last_none_count:
            timeout += 1
        else:
            timeout = 0
            last_insert_count = insert_counter
            last_none_count = none_counter

        # prevent immortal process.
        if timeout > 60:
            com.send("Second Loop Enqueue Worker timeout. Exit.")
            fdb.db.commit()
            return

        if none_counter >= fdb.config.sl_cpu_proc + fdb.config.sl_gpu_proc:
            com.send("Second Loop Enqueue Worker done. Exit.")
            fdb.db.commit()
            return

        com.send(f"Submitted tally: {insert_counter}")


def second_loop_dequeue_worker(target_queue: mp.Queue, com: Connection, config: dict, db_config: dict):
    fdb = build_base_obj(config=config, db_config=db_config)
    processed_counter = 0
    none_counter = 0

    last_none_counter = 0
    last_processed_counter = 0

    timeout = 0

    while True:
        if com.poll(timeout=0.01):
            msg = com.recv()

            # Iterate over message types and perform associated action.
            if msg == Messages.Stop:
                fdb.db.commit()
                return

        # proc_suc, proc_exit = fdb.process_one_second_result(out_queue=target_queue)
        # processed_counter += int(proc_suc)
        # none_counter += int(proc_exit)
        proc_suc, proc_exit = fdb.process_up_to_second_result(out_queue=target_queue)
        processed_counter += proc_suc
        none_counter += proc_exit

        if last_processed_counter == processed_counter and last_none_counter == none_counter:
            timeout += 0.1
        else:
            timeout = 0

        if processed_counter % 100 == 0:
            fdb.db.commit()

        if processed_counter % 1000 == 0:
            fdb.db.commit()
            com.send(f"Done with: {processed_counter}")

        if timeout >= 60:
            com.send("Second Loop Dequeue Worker timeout. Exit.")
            fdb.db.commit()
            return

        if none_counter >= none_counter >= fdb.config.sl_cpu_proc + fdb.config.sl_gpu_proc:
            com.send("Second Loop Dequeue Worker done. Exit.")
            fdb.db.commit()
            return
