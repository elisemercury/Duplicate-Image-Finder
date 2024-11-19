import os.path

import fast_diff_py.config_new as cfg
from fast_diff_py.config_new import FirstLoopConfig
from fast_diff_py.fast_dif_new import FastDifPy
import shutil

paths = {"path_a": "/home/alisot2000/Desktop/SAMPLE_MIRA/dir_a/",
     "path_b": "/home/alisot2000/Desktop/SAMPLE_MIRA/dir_b/",
     "path_c": "/home/alisot2000/Desktop/SAMPLE_MIRA/dir_c/",
         "tq-a": "/media/alisot2000/MacBeth/TQ-Picture-Benchmark",
         "imdb": "/media/alisot2000/MacBeth/IMDB-Bench",
         "wb_a": "/media/alisot2000/MacBeth/workbench/dir_a/",
         "wb_b": "/media/alisot2000/MacBeth/workbench/dir_b/",
         "wbl_a": "/media/alisot2000/MacBeth/workbench_large/dir_a/",
         "wbl_b": "/media/alisot2000/MacBeth/workbench_large/dir_b/"}

for p in paths.values():
    try:
        shutil.rmtree(path=os.path.join(p, ".temp_thumb"))
    except FileNotFoundError:
        print("thumbs already deleted")

    try:
        os.remove(path=os.path.join(p, ".fast_diff.db"))
    except FileNotFoundError:
        print("temp db already deleted")

    try:
        shutil.rmtree(path=os.path.join(p, "diff_plot"))
    except FileNotFoundError:
        print("diff_plot folder already deleted")

    # os.makedirs(f"{p}diff_plot")

flc = FirstLoopConfig(compute_hash=False, compress=True)
# fdo = FastDifPy(dir_a="/home/alisot2000/Desktop/SAMPLE_MIRA/dir_a/", dir_b="/home/alisot2000/Desktop/SAMPLE_MIRA/dir_b", cpu_proc=16)
# fdo = FastDifPy(dir_a="/home/alisot2000/Desktop/SAMPLE_MIRA/dir_a/", dir_b="/home/alisot2000/Desktop/SAMPLE_MIRA/dir_b", cpu_proc=16)
# fdo = FastDifPy(dir_a=paths["path_a"], dir_b=paths["path_c"], cpu_proc=16, batch_size=10, first_loop=flc)
# fdo = FastDifPy(dir_a=paths["path_a"], cpu_proc=1, first_loop=cfg.FirstLoopConfig(compute_hash=False, compress=False))
fdo = FastDifPy(dir_a=paths["tq-a"], cpu_proc=16, batch_size=100, first_loop=cfg.FirstLoopConfig(compute_hash=True, compress=False))

# fdo = FastDifPy(dir_a="/home/alisot2000/Desktop/SAMPLE_MIRA/dir_b/", cpu_proc=16)
fdo.db.create_directory_table_and_index()
if fdo.config.first_loop.compute_hash:
    fdo.db.create_hash_table_and_index()
fdo.perform_index()
fdo.cond_switch_a_b()
fdo.db.set_keys_zero_index()
fdo.print_fs_usage()
fdo.db.commit()
fdo.first_loop()