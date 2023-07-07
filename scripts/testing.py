import src.fast_diff_py.fastDif as fd
import os
import shutil
import time
import datetime
import numpy as np

# 190 images, smart algo
# [18.591363, 18.364407, 18.511604, 18.338064, 18.330935, 18.544899, 18.467676, 19.420712, 19.513579, 18.828884]
# [18.789752, 18.758811, 19.667944, 18.948554, 18.343499, 18.275264, 18.514084, 18.481093, 18.410804, 18.479221]
# a_avg = 18.67905745

# 190 images, stupid algo
# [18.637781, 18.666943, 18.435386, 18.444084, 18.300197, 18.67817, 18.695168, 19.075404, 18.486223, 18.547648]
# [18.560379, 18.60586, 18.655276, 18.578035, 18.55135, 18.618809, 18.429161, 18.568195, 18.63155, 18.71328]
# 18.59394495


# 619 Images, smart algo
# Laptop
# Duration: [47.90702, 48.287607, 48.580843, 49.340098, 48.446712, 49.135304, 49.087072, 47.521362, 49.151893,
# 49.653997, 50.327011, 50.467689, 48.671009, 49.204964, 49.404421, 49.427319, 49.251755, 49.798225, 48.61945, 48.21468]
# Average: 49.02492155
# Variance: 0.541188938391546
# Racklette
# Duration: [40.354952, 40.800322, 39.39068, 42.202993, 40.225713, 39.91432, 39.623994, 39.769116, 40.409505, 40.357542,
# 39.462493, 40.564647, 40.747331, 39.831456, 41.278501, 39.239248, 40.082427, 39.544192, 40.551606, 40.435766]
# Average: 40.2393402
# Variance :0.475523102780559

# 619 Images, stupid algo
# Duration: [48.788511, 48.234032, 47.746268, 47.949184, 47.92275, 48.124926, 47.869854, 47.839274, 47.4967, 47.444251,
# 47.899086, 49.624345, 47.991451, 47.933214, 47.87156, 47.784479, 48.048354, 47.903865, 47.736512, 48.0959]
# Average: 48.015225799999996
# Variance :0.2085860846912598
# Racklette
# Duration: [42.538031, 39.571676, 41.159493, 41.460059, 39.042059, 40.277603, 42.808652, 42.603189, 40.932833,
# 40.010581, 42.87253, 40.529503, 39.357598, 43.222427, 44.45214, 42.532737, 43.283528, 40.487823, 39.192696, 43.338764]
# Average: 41.4836961
# Variance :2.549386857978189
# 8 CPU
# Duration: [50.20955, 49.648556, 49.841921, 51.966297, 50.136144, 49.323914, 51.034806, 49.482655, 49.131145,
# 49.252365, 51.750388, 49.87059, 50.434232, 51.671721, 51.040157, 49.841194, 50.101303, 50.308542, 50.003987, 50.087713]
# Average: 50.256859000000006
# Variance :0.6575649701107


def test_block():
    try:
        shutil.rmtree(path="/home/alisot2000/Desktop/SAMPLE_MIRA/ola/.temp_thumbnails")
    except FileNotFoundError:
        print("thumbs already deleted")

    try:
        os.remove(path="/home/alisot2000/Desktop/SAMPLE_MIRA/ola/diff.db")
    except FileNotFoundError:
        print("temp db already deleted")

    try:
        shutil.rmtree(path="/home/alisot2000/Desktop/SAMPLE_MIRA/ola/diff_plot")
    except FileNotFoundError:
        print("diff_plot folder already deleted")

    os.makedirs("/home/alisot2000/Desktop/SAMPLE_MIRA/ola/diff_plot")

    time.sleep(1)
    print("FS Should have had enough time to update.")

    db = fd.FastDifPy(directory_a="/home/alisot2000/Desktop/SAMPLE_MIRA/ola/")
    db.index_the_dirs()
    db.estimate_disk_usage()

    db.first_loop_iteration(compute_hash=True, amount=4, cpu_proc=16)

    db.second_loop_iteration(only_matching_aspect=False,
                             make_diff_plots=False,
                             diff_location="/home/alisot2000/Desktop/SAMPLE_MIRA/ola/diff_plot",
                             similarity_threshold=200.0,
                             cpu_proc=16)

    db.print_preprocessing_errors()

    clusters, low_quality = db.get_duplicates()
    db.clean_up()
    print(clusters)
    print(low_quality)


if __name__ == "__main__":
    durations = []

    for i in range(20):
        start_time = datetime.datetime.now()
        test_block()
        stop_time = datetime.datetime.now()
        # Remove one second for os to update file system
        durations.append((stop_time - start_time).total_seconds() - 1)

    print(f"Duration: {durations}")
    print(f"Average: {np.average(durations)}")
    print(f"Variance :{np.var(durations)}")

    # ------------------------------------------------------------------------------------------------------------------

    # try:
    #     shutil.rmtree(path="/home/alisot2000/Desktop/SAMPLE_MIRA/SMALL/.temp_thumbnails")
    # except FileNotFoundError:
    #     print("thumbs already deleted")
    #
    # try:
    #     os.remove(path="/home/alisot2000/Desktop/SAMPLE_MIRA/SMALL/diff.db")
    # except FileNotFoundError:
    #     print("temp db already deleted")
    #
    # try:
    #     shutil.rmtree(path="/home/alisot2000/Desktop/SAMPLE_MIRA/SMALL/diff_plot")
    # except FileNotFoundError:
    #     print("diff_plot folder already deleted")
    #
    # os.makedirs("/home/alisot2000/Desktop/SAMPLE_MIRA/SMALL/diff_plot")
    #
    # db = fd.FastDifPy(directory_a="/home/alisot2000/Desktop/SAMPLE_MIRA/SMALL/")
    # db.index_the_dirs()
    # db.db.con.commit()
    # db.estimate_disk_usage()
    # db.first_loop_iteration(compute_hash=True, amount=4)
    # db.second_loop_iteration(only_matching_aspect=False,
    #                          make_diff_plots=True,
    #                          diff_location="/home/alisot2000/Desktop/SAMPLE_MIRA/JOIN/diff_plot",
    #                          similarity_threshold=200.0)