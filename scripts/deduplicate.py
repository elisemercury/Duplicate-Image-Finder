import datetime
import os.path
import time

import fast_diff_py.config as cfg
from fast_diff_py.config import FirstLoopConfig
from fast_diff_py.fast_dif import FastDifPy
import shutil

# while datetime.datetime.now().hour < 3 and datetime.datetime.now().minute < 59:
#     print(f"Waiting ...")
#     time.sleep(300)


paths = {"path_a": "/home/alisot2000/Desktop/SAMPLE_MIRA/dir_a/",
     "path_b": "/home/alisot2000/Desktop/SAMPLE_MIRA/dir_b/",
     "path_c": "/home/alisot2000/Desktop/SAMPLE_MIRA/dir_c/",
         "tq-a": "/media/alisot2000/MacBeth/TQ-Picture-Benchmark",
         "imdb": "/media/alisot2000/MacBeth/IMDB-Bench",
         "wb_a": "/media/alisot2000/MacBeth/workbench/dir_a/",
         "wb_b": "/media/alisot2000/MacBeth/workbench/dir_b/",
         "wbl_a": "/media/alisot2000/MacBeth/workbench_large/dir_a/",
         "wbl_b": "/media/alisot2000/MacBeth/workbench_large/dir_b/"}

flc = FirstLoopConfig(compute_hash=True, compress=True)
config = cfg.Config(delete_db=False, delete_thumb=False, first_loop=flc,
                    root_dir_a=paths["path_a"], root_dir_b=paths["path_c"],
                    state=cfg.Progress.FIRST_LOOP_DONE,
                    db_path="/media/alisot2000/MacBeth/workbench_large/dir_a/.fast_diff.db",
                    thumb_dir="/media/alisot2000/MacBeth/workbench_large/dir_a/.temp_thumb",
                    retain_progress=False)

fdo = FastDifPy(urge=True, config=config)
# fdo.config = config
fdo.config.first_loop = flc

info_str = []
for i in range(8):
    batched =  i // 4 == 0
    ram_cache = i // 2 % 2 == 0
    compressed = i % 2 == 0

    b_str = "Batched" if batched else "Item"
    r_str = "RAM" if ram_cache else "Disk"
    c_str = "Compressed" if compressed else "Uncompressed"

    # Ram Cache and Uncompressed is discarded because child process timeout.
    if not compressed or not ram_cache or not batched:
        print(f"SKIPPING: {b_str} Processing, {r_str} Cache, {c_str} Images")
        info_str.append(f"{b_str} Processing, {r_str} Cache, {c_str} Images, took -1s")
        continue

    print(f"STARTING: {b_str} Processing, {r_str} Cache, {c_str} Images")

    fdo.db.debug_execute("DROP TABLE IF EXISTS dif_table")
    fdo.db.debug_execute("DROP TABLE IF EXISTS dif_error_table")
    # fdo.db.create_diff_table_and_index()
    # fdo.second_loop(use_ram_cache=False, batched_processing=False, make_diff_plots=True, plot_output_dir="/home/alisot2000/Desktop/SAMPLE_MIRA/dir_a/diff_plot", diff_threshold=200)
    fdo.config.first_loop.compress = compressed
    # fdo.config.second_loop.cpu_proc = 16
    print(f"Call Second Loop")
    # fdo.config.batch_size_max_sl = 1000
    begin = datetime.datetime.now(datetime.UTC)
    # fdo.second_loop(use_ram_cache=ram_cache, batched_args=batched, diff_threshold=200, gpu_proc=2, cpu_proc=14)
    fdo.second_loop(use_ram_cache=ram_cache, batched_args=batched, diff_threshold=200, cpu_proc=16)
    end = datetime.datetime.now(datetime.UTC)

    print(f"{b_str} Processing, {r_str} Cache, {c_str} Images, took {(end - begin).total_seconds()}")
    info_str.append(f"{b_str} Processing, {r_str} Cache, {c_str} Images, took {(end - begin).total_seconds()}")

    with open("info.txt", "w") as f:
        f.write("\n".join(info_str))

with open("info.txt", "w") as f:
    f.write("\n".join(info_str))
fdo.cleanup()