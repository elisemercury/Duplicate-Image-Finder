"""
fast_diff_py - Python package for finding duplicate or similar images within folders
https://github.com/elisemercury/Duplicate-Image-Finder,
Fast implementation by Alexander Sotoudeh
https://github.com/AliSot2000/Fast-Image-Deduplicator
"""

from datetime import datetime
import os
import time
import argparse
import json
import warnings
import fastDif
warnings.filterwarnings('ignore')


def build_low_quality_and_delete(res: dict, del_img: bool = False):
    deleted = 0
    low_quality = []
    # delete lower quality images
    for original in res.values():
        for file in original["duplicates"]:
            if del_img:
                print("\nDeletion in progress...", end="\r")
                try:
                    os.remove(file)
                    print("Deleted file:", file, end="\r")
                    deleted += 1
                except:
                    print("Could not delete file:", file, end="\r")
            low_quality.append(file)
    print("\n***\nDeleted", deleted, "images.")
    return low_quality

def parse_similarity(similarity):
    try:
        similarity = float(similarity)
        ref = similarity
    except ValueError:
        if similarity == "low":
            ref = 1000
        # search for exact duplicate images, extremly sensitive, MSE < 0.1
        elif similarity == "high":
            ref = 0.1
        # normal, search for duplicates, recommended, MSE < 200
        else:
            ref = 200
    return ref


def type_str_int(x):
    try:
        return int(x)
    except:
        return x

def stats(dir_a: str,  start: datetime, end: datetime, similarity, total_searched, total_found, dir_b: str = None):
        stats = {}
        stats["directory_1"] = dir_a
        if dir_b != None:
            stats["directory_2"] = dir_b
        else:
            stats["directory_2"] = None
        stats["duration"] = {"start_date": start.strftime("%Y-%m-%d"),
                             "start_time": start.strftime("%H:%M:%S"),
                             "end_date": end.strftime("%Y-%m-%d"),
                             "end_time": end.strftime("%H:%M:%S"),
                             "seconds_elapsed": (end - start).total_seconds()}
        if isinstance(similarity, int):
            stats["similarity_grade"] = "manual"
        else:
            stats["similarity_grade"] = similarity
        stats["similarity_mse"] = parse_similarity(similarity)
        stats["total_files_searched"] = total_searched
        stats["total_dupl_sim_found"] = total_found
        return stats


# Parameters for when launching fast_diff_py via CLI
if __name__ == "__main__":    
    # set CLI arguments
    parser = argparse.ArgumentParser(description='Find duplicate or similar images on your computer with fast_diff_py - https://github.com/elisemercury/Duplicate-Image-Finder')
    parser.add_argument("-A", "--directory_A", type=str, help='Directory to search for images.', required=True)
    parser.add_argument("-B", "--directory_B", type=str, help='(optional) Second directory to search for images.', required=False, nargs='?', default=None)
    parser.add_argument("-Z", "--output_directory", type=str, help='(optional) Output directory for the fast_diff_py result files. Default is working dir.', required=False, nargs='?', default=None)
    parser.add_argument("-s", "--similarity", type=type_str_int, help='(optional) Similarity grade.', required=False, nargs='?', default='normal')
    parser.add_argument("-px", "--px_size", type=int, help='(optional) Compression size of images in pixels.', required=False, nargs='?', default=50)
    parser.add_argument("-p", "--show_progress", type=bool, help='(optional) Shows the real-time progress of fast_diff_py.', required=False, nargs='?', choices=[True, False], default=True)
    parser.add_argument("-o", "--show_output", type=bool, help='(optional) Shows the comapred images in real-time.', required=False, nargs='?', choices=[True, False], default=False)
    parser.add_argument("-d", "--delete", type=bool, help='(optional) Deletes all duplicate images with lower quality.', required=False, nargs='?', choices=[True, False], default=False)
    parser.add_argument("-D", "--silent_del", type=bool, help='(optional) Supresses the user confirmation when deleting images.', required=False, nargs='?', choices=[True, False], default=False)
    args = parser.parse_args()

    warnings.warn("Show_progress does not have an effect but is left for compatibility with difpy")

    use_existing = False
    # verify first if there exists already a config that was in progress.
    if fastDif.test_existing_config():
        while True:
            resp = input("A Config exists from a previous run - do you want to finish it first [y,n]")
            if resp.lower() == "y":
                print("Finishing previous run - your current input arguments will be ignored.")
                use_existing = True
                break
            elif resp.lower() == "n":
                print("Deleting previous config...")
                fastDif.remove_existing_config()
                break
            else:
                print(f"Unsupported response: {resp}, only y and n are allowed.")

    start = datetime.now()
    if use_existing:
        config = fastDif.FastDiffPyConfig()
        print(f"Current progress is: {config.state}")

        comparing_str = f"Comparing directory: {config.p_root_dir_a}"
        if config.has_dir_b:
            comparing_str += f"\nwith: {config.p_root_dir_b}"
        else:
            comparing_str += " with itself."
        print(comparing_str)

        fdp = fastDif.FastDifPy.init_preexisting_config(config=config)
        if config.state is None:
            print("Config empty, terminating.")
            config.retain_config = False
            fdp.clean_up(config=True, db=False, thumbs=False)
            del config
            exit(0)

    else:
        fdp = fastDif.FastDifPy.init_new(directory_a=args.directory_A, directory_b=args.directory_B)
        fdp.config.thumbnail_size_x, fdp.config.thumbnail_size_y = args.px_size, args.px_size
        fdp.config.cli_args = {
            "directory_a": args.directory_A,
            "directory_b": args.directory_B,
            "output_directory": args.output_directory,
            "similarity": parse_similarity(args.similarity),
            "px_size": args.px_size,
            "show_progress": args.show_progress,
            "show_output": args.show_output,
            "delete": args.delete,
            "silent_del": args.silent_del,
        }
        fdp.config.write_to_file()

    if fdp.config.state == "init":
        if fdp.config.cli_args is None:
            print("Config empty, terminating.")
            fdp.config.retain_config = False
            fdp.clean_up(config=True, db=False, thumbs=False)
            del config
            exit(0)

        fdp.index_the_dirs()

    if fdp.config.state == "indexed_dirs" or fdp.config.state == "first_loop_in_progress":
        fdp.first_loop_iteration()

    if fdp.config.state == "first_loop_done" or fdp.config.state=="second_loop_in_progress":
        fdp.second_loop_iteration(
            similarity_threshold=parse_similarity(fdp.config.cli_args["similarity"]),
            make_diff_plots=fdp.config.cli_args["show_output"],
            diff_location=os.path.join(os.path.dirname(__file__), "diff_plots")
        )
        print(f"Comparison images located at {os.path.join(os.path.dirname(__file__), 'diff_plots')}")

    results = fdp.build_loose_duplicate_cluster(parse_similarity(fdp.config.cli_args["similarity"]))
    fdp.clean_up(thumbs=True, config=True, db=True)
    stop = datetime.now()

    delete = False
    if not fdp.config.cli_args["silent_del"]:
        usr = input(
            "Are you sure you want to delete all lower resolution duplicate images? \nThis cannot be undone. (y/n)")
        if str(usr) == "y":
            delete = True
        else:
            print("Image deletion canceled.")

    # Dir count
    a_count = fdp.db.get_dir_count(dir_a=True)
    b_count = fdp.db.get_dir_count(dir_a=False)
    if fdp.config.has_dir_b:
        comp = a_count * b_count
    else:
        comp = a_count * (a_count - 1) / 2

    low_quality = build_low_quality_and_delete(res=results, del_img=delete)
    sts = stats(dir_a=fdp.config.p_root_dir_a,
                dir_b=fdp.config.p_root_dir_b,
                similarity=fdp.config.cli_args["similarity"],
                start=start, end=stop,
                total_found=len(results),
                total_searched=comp)

    # create filenames for the output files
    timestamp =str(time.time()).replace(".", "_")
    result_file = "difPy_results_" + timestamp + ".json"
    lq_file = "difPy_lower_quality_" + timestamp + ".txt"
    stats_file = "difPy_stats_" + timestamp + ".json"

    if fdp.config.cli_args["output_directory"] is not None:
        t_dir = fdp.config.cli_args["output_directory"]
    else:
        t_dir = os.getcwd()

    if not os.path.exists(t_dir):
        os.makedirs(t_dir)

    with open(os.path.join(t_dir, result_file), "w") as file:
        json.dump(results, file)

    with open(os.path.join(t_dir, lq_file), "w") as file:
        file.writelines(low_quality)

    with open(os.path.join(t_dir, stats_file), "w") as file:
        json.dump(sts, file)

    print(f"""\nSaved fast_diff_py results into folder {t_dir} and filenames:\n{result_file} \n{lq_file} \n{stats_file}""")