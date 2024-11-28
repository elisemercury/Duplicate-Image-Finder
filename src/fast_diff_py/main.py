import fast_diff_py.config as cfg
import fast_diff_py.fast_dif as fdn
from fast_diff_py.fast_dif import FastDifPy
import shutil
import os

from fast_diff_py.img_processing import make_dif_plot

paths = {"path_a": "/home/alisot2000/Desktop/SAMPLE_MIRA/dir_a/",
     "path_b": "/home/alisot2000/Desktop/SAMPLE_MIRA/dir_b/",
     "path_c": "/home/alisot2000/Desktop/SAMPLE_MIRA/dir_c/",
         "tq-a": "/media/alisot2000/MacBeth/TQ-Picture-Benchmark",
         "imdb": "/media/alisot2000/MacBeth/IMDB-Bench",
         "wb_a": "/media/alisot2000/MacBeth/workbench/dir_a/",
         "wb_b": "/media/alisot2000/MacBeth/workbench/dir_b/",
         # "wbl_a": "/media/alisot2000/MacBeth/workbench_large/dir_a/",
         # "wbl_b": "/media/alisot2000/MacBeth/workbench_large/dir_b/"
         }

if False:
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

        try:
            os.remove(path=os.path.join(p, ".task.json"))
        except FileNotFoundError:
            print("task already deleted")

flc = cfg.FirstLoopConfig(compute_hash=True, compress=True)
config = cfg.Config(delete_db=False, delete_thumb=False, first_loop=flc,
                    root_dir_a=paths["path_a"],
                    state=cfg.Progress.FIRST_LOOP_DONE,
                    db_path="/home/alisot2000/Desktop/SAMPLE_MIRA/dir_a/.fast_diff.db",
                    thumb_dir="/home/alisot2000/Desktop/SAMPLE_MIRA/dir_a/.temp_thumb",
                    retain_progress=False)

fdo = FastDifPy(config=config)
fdo.db.debug_execute("DROP TABLE IF EXISTS dif_table")
# fdo = FastDifPy(dir_a=paths["path_a"], dir_b=paths["path_c"])
# fdo = FastDifPy(dir_a=paths["wb_a"], dir_b=paths["wb_b"])
# fdo.full_index()
# fdo.first_loop()
fdo.second_loop(parallel=True, skip_matching_hash=True, match_aspect_by=1.01,
                make_diff_plots=True,
                plot_output_dir="/home/alisot2000/Desktop/SAMPLE_MIRA/dir_a/diff_plot")
print("-"*120)
for x in fdo.get_diff_pairs(matching_hash=True):
    print(x)
print("-"*120)

for x in fdo.get_diff_clusters(dir_a=True, matching_hash=True):
    print(x)
print("-"*120)

for x in fdo.get_diff_clusters(dir_a=False, matching_hash=True):
    print(x)
print("-"*120)
fdo.commit()
fdo.cleanup()