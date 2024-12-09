import fast_diff_py.config as cfg
from fast_diff_py.fast_dif import FastDifPy
import argparse


def dif(dir_a: str, dir_b: str, purge: bool = False,  **kwargs):
    """
    kwargs are all attributes of the Config class, except for root_dir_a and root_dir_b

    :param dir_a: The first directory to compare
    :param dir_b: The second directory to compare
    :param purge: Delete any existing progress should it exist

    :return: FastDifPy object
    """
    fdo = FastDifPy(dir_a=dir_a, dir_b=dir_b, purge=purge, **kwargs)

    # Keep progress, we're not done
    fdo.config.retain_progress = True
    fdo.config.delete_db = False
    fdo.config.delete_thumb = False

    # Run the index
    if fdo.config.state == cfg.Progress.INIT:
        if fdo.db.dir_table_exists():
            fdo.db.drop_directory_table()

        fdo.full_index()

    # Exit in sigint
    if not fdo.run:
        fdo.commit()
        fdo.cleanup()
        return

    # Run the first loop
    if fdo.config.state in (cfg.Progress.INDEXED_DIRS, cfg.Progress.FIRST_LOOP_IN_PROGRESS):
        fdo.first_loop()

    # Exit on sigint
    if not fdo.run:
        print("First Loop Exited")
        fdo.commit()
        fdo.cleanup()
        return

    # Run the second loop
    if fdo.config.state in (cfg.Progress.SECOND_LOOP_IN_PROGRESS, cfg.Progress.FIRST_LOOP_DONE):
        fdo.second_loop()

    if not fdo.run:
        fdo.commit()
        fdo.cleanup()
        return

    # We're done, clean up
    fdo.config.retain_progress = False
    fdo.config.delete_db = True
    fdo.config.delete_thumb = True

    return fdo

    # Keep progress, we're not done
    fdo.config.retain_progress = True
    fdo.config.delete_db = False
    fdo.config.delete_thumb = False

    # Run the index
    if fdo.config.state == cfg.Progress.INIT:
        if fdo.db.dir_table_exists():
            fdo.db.drop_directory_table()

        fdo.full_index()

    # Exit in sigint
    if not fdo.run:
        fdo.commit()
        fdo.cleanup()
        return

    # Run the first loop
    if fdo.config.state in (cfg.Progress.INDEXED_DIRS, cfg.Progress.FIRST_LOOP_IN_PROGRESS):
        fdo.first_loop()

    # Exit on sigint
    if not fdo.run:
        print("First Loop Exited")
        fdo.commit()
        fdo.cleanup()
        return

    # Run the second loop
    if fdo.config.state in (cfg.Progress.SECOND_LOOP_IN_PROGRESS, cfg.Progress.FIRST_LOOP_DONE):
        fdo.second_loop()

    if not fdo.run:
        fdo.commit()
        fdo.cleanup()
        return

    # We're done, clean up
    fdo.config.retain_progress = False
    fdo.config.delete_db = True
    fdo.config.delete_thumb = True

    return fdo

if __name__ == "__main__":
    # Parameters for when launching difPy via CLI
    # parser = argparse.ArgumentParser(description='Find duplicate or similar images with difPy - https://github.com/elisemercury/Duplicate-Image-Finder')
    # parser.add_argument('-D', '--directory', type=str, nargs='+', help='Paths of the directories to be searched. Default is working dir.', required=False, default=[os.getcwd()])
    # parser.add_argument('-Z', '--output_directory', type=str, help='Output directory path for the difPy result files. Default is working dir.', required=False, default=None)
    # parser.add_argument('-r', '--recursive', type=lambda x: bool(_help._strtobool(x)), help='Search recursively within the directories.', required=False, choices=[True, False], default=True)
    # parser.add_argument('-i', '--in_folder', type=lambda x: bool(_help._strtobool(x)), help='Search for matches in the union of directories.', required=False, choices=[True, False], default=False)
    # parser.add_argument('-le', '--limit_extensions', type=lambda x: bool(_help._strtobool(x)), help='Limit search to known image file extensions.', required=False, choices=[True, False], default=True)
    # parser.add_argument('-px', '--px_size', type=int, help='Compression size of images in pixels.', required=False, default=50)
    # parser.add_argument('-s', '--similarity', type=_help._convert_str_to_int, help='Similarity grade (mse).', required=False, default='duplicates')
    # parser.add_argument('-ro', '--rotate', type=lambda x: bool(_help._strtobool(x)), help='Rotate images during comparison process.', required=False, choices=[True, False], default=True)
    # parser.add_argument('-la', '--lazy', type=lambda x: bool(_help._strtobool(x)), help='Compares image dimensions before comparison process.', required=False, choices=[True, False], default=True)
    # parser.add_argument('-mv', '--move_to', type=str, help='Output directory path of lower quality images among matches.', required=False, default=None)
    # parser.add_argument('-d', '--delete', type=lambda x: bool(_help._strtobool(x)), help='Delete lower quality images among matches.', required=False, choices=[True, False], default=False)
    # parser.add_argument('-sd', '--silent_del', type=lambda x: bool(_help._strtobool(x)), help='Suppress the user confirmation when deleting images.', required=False, choices=[True, False], default=False)
    # parser.add_argument('-p', '--show_progress', type=lambda x: bool(_help._strtobool(x)), help='Show the real-time progress of difPy.', required=False, choices=[True, False], default=True)
    # parser.add_argument('-proc', '--processes', type=_help._convert_str_to_int, help=' Number of worker processes for multiprocessing.', required=False, default=None)
    # parser.add_argument('-ch', '--chunksize', type=_help._convert_str_to_int, help='Only relevant when dataset > 5k images. Sets the batch size at which the job is simultaneously processed when multiprocessing.', required=False, default=None)
    # parser.add_argument('-l', '--logs', type=lambda x: bool(_help._strtobool(x)), help='(Deprecated) Collect statistics during the process.', required=False, choices=[True, False], default=None)

    # Parameters for when launching difPy via CLI
    parser = argparse.ArgumentParser(description='Find duplicate or similar images with difPy - https://github.com/elisemercury/Duplicate-Image-Finder')
    parser.add_argument('-D', '--directory', type=str, nargs='+', help='Paths of the directories to be searched. Default is working dir.', required=False, default=[os.getcwd()])
    parser.add_argument('-Z', '--output_directory', type=str, help='Output directory path for the difPy result files. Default is working dir.', required=False, default=None)
    parser.add_argument('-r', '--recursive', type=lambda x: bool(_help._strtobool(x)), help='Search recursively within the directories.', required=False, choices=[True, False], default=True)
    parser.add_argument('-i', '--in_folder', type=lambda x: bool(_help._strtobool(x)), help='Search for matches in the union of directories.', required=False, choices=[True, False], default=False)
    parser.add_argument('-le', '--limit_extensions', type=lambda x: bool(_help._strtobool(x)), help='Limit search to known image file extensions.', required=False, choices=[True, False], default=True)
    parser.add_argument('-px', '--px_size', type=int, help='Compression size of images in pixels.', required=False, default=50)
    parser.add_argument('-s', '--similarity', type=_help._convert_str_to_int, help='Similarity grade (mse).', required=False, default='duplicates')
    parser.add_argument('-ro', '--rotate', type=lambda x: bool(_help._strtobool(x)), help='Rotate images during comparison process.', required=False, choices=[True, False], default=True)
    parser.add_argument('-la', '--lazy', type=lambda x: bool(_help._strtobool(x)), help='Compares image dimensions before comparison process.', required=False, choices=[True, False], default=True)
    parser.add_argument('-mv', '--move_to', type=str, help='Output directory path of lower quality images among matches.', required=False, default=None)
    parser.add_argument('-d', '--delete', type=lambda x: bool(_help._strtobool(x)), help='Delete lower quality images among matches.', required=False, choices=[True, False], default=False)
    parser.add_argument('-sd', '--silent_del', type=lambda x: bool(_help._strtobool(x)), help='Suppress the user confirmation when deleting images.', required=False, choices=[True, False], default=False)
    parser.add_argument('-p', '--show_progress', type=lambda x: bool(_help._strtobool(x)), help='Show the real-time progress of difPy.', required=False, choices=[True, False], default=True)
    parser.add_argument('-proc', '--processes', type=_help._convert_str_to_int, help=' Number of worker processes for multiprocessing.', required=False, default=None)
    parser.add_argument('-ch', '--chunksize', type=_help._convert_str_to_int, help='Only relevant when dataset > 5k images. Sets the batch size at which the job is simultaneously processed when multiprocessing.', required=False, default=None)
    parser.add_argument('-l', '--logs', type=lambda x: bool(_help._strtobool(x)), help='(Deprecated) Collect statistics during the process.', required=False, choices=[True, False], default=None)


    args = parser.parse_args()

    o = dif(dir_a="/home/alisot2000/Desktop/workbench_tiny/dir_a", dir_b="/home/alisot2000/Desktop/workbench_tiny/dir_b", purge=False)
    for p in o.get_diff_pairs():
        print(p)

    for c in o.get_diff_clusters(dir_a=True):
        print(c)

    for c in o.get_diff_clusters(dir_a=False):
        print(c)

    o.cleanup()
