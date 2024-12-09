import datetime
import os.path
import time

import fast_diff_py.config as cfg
from fast_diff_py.config import FirstLoopConfig
from fast_diff_py.fast_dif import FastDifPy
import shutil

from fast_diff_py.img_processing import make_dif_plot

paths = {"path_a": "/home/alisot2000/Desktop/SAMPLE_MIRA/dir_a/",
     "path_b": "/home/alisot2000/Desktop/SAMPLE_MIRA/dir_b/",
     "path_c": "/home/alisot2000/Desktop/SAMPLE_MIRA/dir_c/",
         "tq-a": "/media/alisot2000/MacBeth/TQ-Picture-Benchmark",
         "imdb": "/media/alisot2000/MacBeth/IMDB-Bench",
         # "wb_a": "/media/alisot2000/MacBeth/workbench/dir_a/",
         # "wb_b": "/media/alisot2000/MacBeth/workbench/dir_b/",
         # "wbl_a": "/media/alisot2000/MacBeth/workbench_large/dir_a/",
         # "wbl_b": "/media/alisot2000/MacBeth/workbench_large/dir_b/"
         }

if True:
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
            os.remove(path=os.path.join(p, ".task.json"))
        except FileNotFoundError:
            print("task already deleted")

        try:
            shutil.rmtree(path=os.path.join(p, "diff_plot"))
        except FileNotFoundError:
            print("diff_plot folder already deleted")


start = datetime.datetime.now(datetime.UTC)
flc = FirstLoopConfig(compute_hash=True, compress=True, parallel=True)
# config = cfg.Config(delete_db=False, delete_thumb=False, first_loop=flc, root_dir_a=paths["wbl_a"], root_dir_b=paths["wbl_b"])
config = cfg.Config(delete_db=False,
                    delete_thumb=False,
                    first_loop=flc,
                    root_dir_a=paths["path_a"], root_dir_b=paths["path_c"],
                    db_path="/home/alisot2000/Desktop/SAMPLE_MIRA/dir_a/.fast_diff.db")
fdo = FastDifPy(dir_a=paths["path_a"])
fdo.config.first_loop = flc

# fdo = FastDifPy(dir_a="/home/alisot2000/Desktop/SAMPLE_MIRA/dir_a/", dir_b="/home/alisot2000/Desktop/SAMPLE_MIRA/dir_b", cpu_proc=16)
# fdo = FastDifPy(dir_a="/home/alisot2000/Desktop/SAMPLE_MIRA/dir_a/", dir_b="/home/alisot2000/Desktop/SAMPLE_MIRA/dir_b", cpu_proc=16)
# fdo = FastDifPy(dir_a=paths["path_a"], dir_b=paths["path_c"], cpu_proc=16, batch_size=10, first_loop=flc)
# fdo = FastDifPy(dir_a=paths["path_a"], dir_b=paths["path_c"], cpu_proc=16, batch_size=10, first_loop=flc)
# fdo = FastDifPy(dir_a=paths["path_a"], first_loop=flc, cpu_proc=16, batch_size=10)
# fdo = FastDifPy(dir_a=paths["wbl_a"], dir_b=paths["wbl_b"], config=config)
# fdo = FastDifPy(dir_a=paths["wb_a"], dir_b=paths["wb_b"], first_loop=flc, cpu_proc=16)
# fdo = FastDifPy(dir_a=paths["tq-a"], cpu_proc=16, batch_size=100, first_loop=cfg.FirstLoopConfig(compute_hash=True, compress=False))
# fdo = FastDifPy(config=config, dir_a=paths["path_a"])


# fdo = FastDifPy(dir_a="/home/alisot2000/Desktop/SAMPLE_MIRA/dir_b/", cpu_proc=16)
fdo.full_index()
fdo.print_fs_usage()
fdo.commit()
fdo.first_loop()
fdo.commit()
exit(0)
# fdo.db.create_diff_table_and_index()

# fdo.config.cpu_proc = 0
# if not os.path.exists("/home/alisot2000/Desktop/SAMPLE_MIRA/dir_a/diff_plot"):
#     os.makedirs("/home/alisot2000/Desktop/SAMPLE_MIRA/dir_a/diff_plot")


# fdo = FastDifPy(dir_a=paths["wb_a"], dir_b=paths["wb_b"], first_loop=flc, cpu_proc=16)

begin = datetime.datetime.now(datetime.UTC)
fdo.second_loop(diff_threshold=200)
end = datetime.datetime.now(datetime.UTC)


time.sleep(1)
# print("-"*120)
# for x in fdo.db.get_duplicate_pairs(200):
#     print(x)
# print("-"*120)
# for x in fdo.db.get_cluster(200):
#     print(x)
# print("-"*120)
# for x in fdo.db.get_cluster(200, False):
#     print(x)
# print("-"*120)
# print([x for x in fdo.db.get_duplicate_pairs(200)])
# print([x for x in fdo.db.get_cluster(200, group_a=True)])
# print([x for x in fdo.db.get_cluster(200, group_a=False)])
fdo.cleanup()


