import skimage.color
import matplotlib.pyplot as plt
import numpy as np
import cv2
import os
import time
import collections

class dif:

    def __init__(self, directory_A, directory_B=None, similarity="normal", px_size=50, sort_output=False, show_output=False, show_progress=False, delete=False, silent_del=False):
        """
        directory_A (str)......folder path to search for duplicate/similar images
        directory_B (str)......second folder path to search for duplicate/similar images
        similarity (str)......."normal" = searches for duplicates, recommended setting, MSE < 200
                               "high" = serached for exact duplicates, extremly sensitive to details, MSE < 0.1
                               "low" = searches for similar images, MSE < 1000
        px_size (int)..........recommended not to change default value
                               resize images to px_size height x width (in pixels) before being compared
                               the higher the pixel size, the more computational ressources and time required 
        sort_output (bool).....False = adds the duplicate images to output dictionary in the order they were found
                               True = sorts the duplicate images in the output dictionars alphabetically 
        show_output (bool).....False = omits the output and doesn't show found images
                               True = shows duplicate/similar images found in output            
        show_progress (bool)...False = shows where your lengthy processing currently is
        delete (bool)..........! please use with care, as this cannot be undone
                               lower resolution duplicate images that were found are automatically deleted
        silent_del (bool)......! please use with care, as this cannot be undone
                               True = skips the asking for user confirmation when deleting lower resolution duplicate images
                               will only work if "delete" AND "silent_del" are both == True

        OUTPUT (set)...........a dictionary with the filename of the duplicate images 
                             and a set of lower resultion images of all duplicates
        """
        start_time = time.time()        
        print("DifPy process initializing...", end="\r")

        if directory_B != None:
            # process both directories
            dif._process_directory(directory_A)
            dif._process_directory(directory_B)
        else:
            # process one directory
            dif._process_directory(directory_A)
            directory_B = directory_A

        dif._validate_parameters(sort_output, show_output, show_progress, similarity, px_size, delete, silent_del)

        if directory_B == directory_A:
            result, lower_quality, total = dif._search_one_dir(directory_A, 
                                                               similarity, px_size, 
                                                               sort_output, show_output, show_progress)
        else:
            result, lower_quality, total = dif._search_two_dirs(directory_A, directory_B,
                                                                similarity, px_size, 
                                                                sort_output, show_output, show_progress)
        if sort_output == True:
            result = collections.OrderedDict(sorted(result.items()))

        end_time = time.time()
        time_elapsed = np.round(end_time - start_time, 4)
        stats = dif._generate_stats(directory_A, directory_B, 
                                    time.localtime(start_time), time.localtime(end_time), time_elapsed, 
                                    similarity, total, len(result))

        self.result = result
        self.lower_quality = lower_quality
        self.stats = stats

        if len(result) == 1:
            images = "image"
        else:
            images = "images"
        print("Found", len(result), images, "with one or more duplicate/similar images in", time_elapsed, "seconds.")

        if len(result) != 0:
            if delete:
                if not silent_del:
                    usr = input("Are you sure you want to delete all lower resolution duplicate images? \nThis cannot be undone. (y/n)")
                    if str(usr) == "y":
                        dif._delete_imgs(set(lower_quality))
                    else:
                        print("Image deletion canceled.")
                else:
                    dif._delete_imgs(set(lower_quality))

    # Function that searches one directory for duplicate/similar images
    def _search_one_dir(directory_A, similarity="normal", px_size=50, sort_output=False, show_output=False, show_progress=False):

        img_matrices_A, filenames_A = dif._create_imgs_matrix(directory_A, px_size)
        total = len(img_matrices_A)
        result = {}
        lower_quality = []

        ref = dif._map_similarity(similarity)

        # find duplicates/similar images within one folder
        for count_A, imageMatrix_A in enumerate(img_matrices_A):
            if show_progress:
                dif._show_progress(count_A, img_matrices_A)
            for count_B, imageMatrix_B in enumerate(img_matrices_A):
                if count_B > count_A and count_A != len(img_matrices_A):
                    rotations = 0
                    while rotations <= 3:
                        if rotations != 0:
                            imageMatrix_B = dif._rotate_img(imageMatrix_B)

                        err = dif._mse(imageMatrix_A, imageMatrix_B)
                        if err < ref:
                            if show_output:
                                dif._show_img_figs(imageMatrix_A, imageMatrix_B, err)
                                dif._show_file_info(str("..." + directory_A[-35:]) + "/" + filenames_A[count_A],
                                                    str("..." + directory_A[-35:]) + "/" + filenames_A[count_B])
                            if filenames_A[count_A] in result.keys():
                                result[filenames_A[count_A]]["duplicates"] = result[filenames_A[count_A]]["duplicates"] + [directory_A + "/" + filenames_A[count_B]]
                            else:
                                result[filenames_A[count_A]] = {"location": directory_A + "/" + filenames_A[count_A],
                                                                "duplicates": [directory_A + "/" + filenames_A[count_B]]}
                            high, low = dif._check_img_quality(directory_A, directory_A, filenames_A[count_A], filenames_A[count_B])
                            lower_quality.append(low)
                            break
                        else:
                            rotations += 1
                            
        if sort_output == True:
            result = collections.OrderedDict(sorted(result.items()))
        return result, lower_quality, total

    # Function that searches two directories for duplicate/similar images
    def _search_two_dirs(directory_A, directory_B=None, similarity="normal", px_size=50, sort_output=False, show_output=False, show_progress=False):

        img_matrices_A, filenames_A = dif._create_imgs_matrix(directory_A, px_size)
        img_matrices_B, filenames_B = dif._create_imgs_matrix(directory_B, px_size)
        total = len(img_matrices_A) + len(img_matrices_B)
        result = {}
        lower_quality = []

        ref = dif._map_similarity(similarity)

        # find duplicates/similar images between two folders
        for count_A, imageMatrix_A in enumerate(img_matrices_A):
            if show_progress:
                dif._show_progress(count_A, img_matrices_A)
            for count_B, imageMatrix_B in enumerate(img_matrices_B):
                rotations = 0
                while rotations <= 3:
                    if rotations != 0:
                        imageMatrix_B = dif._rotate_img(imageMatrix_B)
                        
                    err = dif._mse(imageMatrix_A, imageMatrix_B)
                    if err < ref:
                        if show_output:
                            dif._show_img_figs(imageMatrix_A, imageMatrix_B, err)
                            dif._show_file_info(str("..." + directory_A[-35:]) + "/" + filenames_A[count_A],
                                                str("..." + directory_B[-35:]) + "/" + filenames_B[count_B])
                        if filenames_A[count_A] in result.keys():
                            result[filenames_A[count_A]]["duplicates"] = result[filenames_A[count_A]]["duplicates"] + [directory_B + "/" + filenames_B[count_B]]
                        else:
                            result[filenames_A[count_A]] = {"location": directory_A + "/" + filenames_A[count_A],
                                                            "duplicates": [directory_B + "/" + filenames_B[count_B]]}
                        try:
                            high, low = dif._check_img_quality(directory_A, directory_B, filenames_A[count_A], filenames_B[count_B])
                            lower_quality.append(low)
                        except: 
                            pass
                        break
                    else:
                        rotations += 1

        if sort_output == True:
            result = collections.OrderedDict(sorted(result.items()))

        return result, lower_quality, total

    # Function that processes the directories that were input as parameters
    def _process_directory(directory):
        # check if directories are valid
        directory += os.sep
        if not os.path.isdir(directory):
            raise FileNotFoundError(f"Directory: " + directory + " does not exist")
        return directory

    # Function that validates the input parameters of DifPy
    def _validate_parameters(sort_output, show_output, show_progress, similarity, px_size, delete, silent_del):
        # validate the parameters of the function
        if sort_output != True and sort_output != False:
            raise ValueError('Invalid value for "sort_output" parameter.')
        if show_output != True and show_output != False:
            raise ValueError('Invalid value for "show_output" parameter.')
        if show_progress != True and show_progress != False:
            raise ValueError('Invalid value for "show_progress" parameter.')
        if similarity not in ["low", "normal", "high"]:
            raise ValueError('Invalid value for "similarity" parameter.')
        if px_size < 10 or px_size > 5000:
            raise ValueError('Invalid value for "px_size" parameter.')
        if delete != True and delete != False:
            raise ValueError('Invalid value for "delete" parameter.')
        if silent_del != True and silent_del != False:
            raise ValueError('Invalid value for "silent_del" parameter.')

    # Function that creates a list of matrices for each image found in the folders
    def _create_imgs_matrix(directory, px_size):
        directory = dif._process_directory(directory)
        img_filenames = []
        # create list of all files in directory
        folder_files = [filename for filename in os.listdir(directory)]

        # create images matrix
        imgs_matrix = []
        for filename in folder_files:
            path = os.path.join(directory, filename)
            # check if the file is not a folder
            if not os.path.isdir(path):
                try:
                    img = cv2.imdecode(np.fromfile(
                        path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
                    if type(img) == np.ndarray:
                        img = img[..., 0:3]
                        img = cv2.resize(img, dsize=(
                            px_size, px_size), interpolation=cv2.INTER_CUBIC)
                        
                        if len(img.shape) == 2:
                            img = skimage.color.gray2rgb(img)
                        imgs_matrix.append(img)
                        img_filenames.append(filename)
                except:
                    pass
        return imgs_matrix, img_filenames

    # Function that maps the similarity grade to the respective MSE value
    def _map_similarity(similarity):
        if similarity == "low":
            ref = 1000
        # search for exact duplicate images, extremly sensitive, MSE < 0.1
        elif similarity == "high":
            ref = 0.1
        # normal, search for duplicates, recommended, MSE < 200
        else:
            ref = 200
        return ref

    # Function that calulates the mean squared error (mse) between two image matrices
    def _mse(imageA, imageB):
        err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
        err /= float(imageA.shape[0] * imageA.shape[1])
        return err

    # Function that plots two compared image files and their mse
    def _show_img_figs(imageA, imageB, err):
        fig = plt.figure()
        plt.suptitle("MSE: %.2f" % (err))
        # plot first image
        ax = fig.add_subplot(1, 2, 1)
        plt.imshow(imageA, cmap=plt.cm.gray)
        plt.axis("off")
        # plot second image
        ax = fig.add_subplot(1, 2, 2)
        plt.imshow(imageB, cmap=plt.cm.gray)
        plt.axis("off")
        # show the images
        plt.show()

    # Function for printing filename info of plotted image files
    def _show_file_info(imageA, imageB):
        print("""Duplicate files:\n{} and \n{}""".format(imageA, imageB))

    # Function that displays a progress bar during the search
    def _show_progress(count, img_matrix):
        if count+1 == len(img_matrix):
            print("DifPy processing images: [{}/{}] [{:.0%}]".format(count, len(img_matrix), count/len(img_matrix)), end="\r")
            print("DifPy processing images: [{}/{}] [{:.0%}]".format(count+1, len(img_matrix), (count+1)/len(img_matrix)))            
        else:
            print("DifPy processing images: [{}/{}] [{:.0%}]".format(count, len(img_matrix), count/len(img_matrix)), end="\r")

    # Function for rotating an image matrix by a 90 degree angle
    def _rotate_img(image):
        image = np.rot90(image, k=1, axes=(0, 1))
        return image

    # Function for checking the quality of compared images, appends the lower quality image to the list
    def _check_img_quality(directoryA, directoryB, imageA, imageB):
        dirA = dif._process_directory(directoryA)
        dirB = dif._process_directory(directoryB)
        size_imgA = os.stat(os.path.join(dirA, imageA)).st_size
        size_imgB = os.stat(os.path.join(dirB, imageB)).st_size
        if size_imgA >= size_imgB:
            return directoryA + "/" + imageA, directoryB + "/" + imageB
        else:
            return directoryB + "/" + imageB, directoryA + "/" + imageA
    
    # Function that generates a dictionary for statistics around the completed DifPy process
    def _generate_stats(directoryA, directoryB, start_time, end_time, time_elapsed, similarity, total_searched, total_found):
        stats = {}
        stats["directory_1"] = directoryA
        if directoryB != None:
            stats["directory_2"] = directoryB
        stats["duration"] = {"start_date": time.strftime("%Y-%m-%d", start_time),
                             "start_time": time.strftime("%H:%M:%S", start_time),
                             "end_date": time.strftime("%Y-%m-%d", end_time),
                             "end_time": time.strftime("%H:%M:%S", end_time),
                             "seconds_elapsed": time_elapsed}
        stats["similarity_grade"] = similarity
        stats["similarity_mse"] = dif._map_similarity(similarity)
        stats["total_images_searched"] = total_searched
        stats["total_images_found"] = total_found
        return stats

    # Function for deleting the lower quality images that were found after the search
    def _delete_imgs(lower_quality_set):
        deleted = 0
        for file in lower_quality_set:
            print("\nDeletion in progress...", end="\r")
            try:
                os.remove(file)
                print("Deleted file:", file, end="\r")
                deleted += 1
            except:
                print("Could not delete file:", file, end="\r")
        print("\n***\nDeleted", deleted, "images.")