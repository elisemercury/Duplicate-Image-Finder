import skimage.measure
import matplotlib.pyplot as plt
import numpy as np
import cv2
import os
import imghdr
import time

""" 
Duplicate Image Finder (DIF): function that searches a given directory for images and finds duplicate/similar images among them.
Outputs the number of found duplicate/similar image pairs with a list of the filenames having lower resolution.
"""

class dif:
    def __init__(directory, show_imgs=False, similarity="normal", px_size=50, delete=False):
        """
        directory (str)......folder path to search for duplicate/similar images
        show_imgs (bool).....False = omits the output and doesn't show found images
                             True = shows duplicate/similar images found in output
        similarity (str)....."normal" = searches for duplicates, recommended setting, MSE < 200
                             "high" = serached for exact duplicates, extremly sensitive to details, MSE < 0.1
                             "low" = searches for similar images, MSE < 1000
        px_size (int)........recommended not to change default value
                             resize images to px_size height x width (in pixels) before being compared
                             the higher the pixel size, the more computational ressources and time required 
        delete (bool)........! please use with care, as this cannot be undone
                             lower resolution duplicate images that were found are automatically deleted
        
        OUTPUT (set).........a set of the filenames of the lower resolution duplicate images
        """
        # list where the found duplicate/similar images are stored
        duplicates = []
        lower_res = []

        imgs_matrix = dif.create_imgs_matrix(directory, px_size)

        # search for similar images, MSE < 1000
        if similarity == "low":
            ref = 1000
        # search for exact duplicate images, extremly sensitive, MSE < 0.1
        elif similarity == "high":
            ref = 0.1
        # normal, search for duplicates, recommended, MSE < 200
        else:
            ref = 200

        main_img = 0
        compared_img = 1
        nrows, ncols = px_size, px_size
        srow_A = 0
        erow_A = nrows
        srow_B = erow_A
        erow_B = srow_B + nrows       

        while erow_B <= imgs_matrix.shape[0]:
            while compared_img < (len(image_files)):
                # select two images from imgs_matrix
                imgA = imgs_matrix[srow_A : erow_A, # rows
                                   0      : ncols]  # columns
                imgB = imgs_matrix[srow_B : erow_B, # rows
                                   0      : ncols]  # columns
                # compare the images
                rotations = 0
                while image_files[main_img] not in duplicates and rotations <= 3:
                    if rotations != 0:
                        imgB = dif.rotate_img(imgB)
                    err = dif.mse(imgA, imgB)
                    if err < ref:
                        if show_imgs == True:
                            dif.show_img_figs(imgA, imgB, err)
                            dif.show_file_info(compared_img, main_img)
                        dif.add_to_list(image_files[main_img], duplicates)
                        dif.check_img_quality(directory, image_files[main_img], image_files[compared_img], lower_res)
                    rotations += 1
                srow_B += nrows
                erow_B += nrows
                compared_img += 1

            srow_A += nrows
            erow_A += nrows
            srow_B = erow_A
            erow_B = srow_B + nrows
            main_img += 1
            compared_img = main_img + 1

        msg = "\n***\nFound " + str(len(duplicates))  + " duplicate image pairs in " + str(len(image_files)) + " total images.\n\nThe following files have lower resolution:"
        print(msg)
        print(lower_res, "\n")
        time.sleep(0.5)
        
        if delete==True:
            usr = input("Are you sure you want to delete all lower resolution duplicate images? (y/n)")
            if str(usr) == "y":
                dif.delete_imgs(directory, set(lower_res))
            else:
                print("Image deletion canceled.")
                return set(lower_res)
        else:
            return set(lower_res)

    # Function that searches the folder for image files, converts them to a matrix
    def create_imgs_matrix(directory, px_size):
        global image_files   
        image_files = []
        # create list of all files in directory     
        folder_files = [filename for filename in os.listdir(directory)]  

        # create images matrix   
        counter = 0
        for filename in folder_files: 
            if not os.path.isdir(directory + filename) and imghdr.what(directory + filename):
                img = cv2.imdecode(np.fromfile(directory + filename, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
                if type(img) == np.ndarray:
                    img = img[...,0:3]
                    img = cv2.resize(img, dsize=(px_size, px_size), interpolation=cv2.INTER_CUBIC)
                    if counter == 0:
                        imgs_matrix = img
                        image_files.append(filename)
                        counter += 1
                    else:
                        imgs_matrix = np.concatenate((imgs_matrix, img))
                        image_files.append(filename)
        return imgs_matrix

    # Function that calulates the mean squared error (mse) between two image matrices
    def mse(imageA, imageB):
        err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
        err /= float(imageA.shape[0] * imageA.shape[1])
        return err

    # Function that plots two compared image files and their mse
    def show_img_figs(imageA, imageB, err):
        fig = plt.figure()
        plt.suptitle("MSE: %.2f" % (err))
        # plot first image
        ax = fig.add_subplot(1, 2, 1)
        plt.imshow(imageA, cmap = plt.cm.gray)
        plt.axis("off")
        # plot second image
        ax = fig.add_subplot(1, 2, 2)
        plt.imshow(imageB, cmap = plt.cm.gray)
        plt.axis("off")
        # show the images
        plt.show()

    #Function for rotating an image matrix by a 90 degree angle
    def rotate_img(image):
        image = np.rot90(image, k=1, axes=(0, 1))
        return image

    # Function for printing filename info of plotted image files
    def show_file_info(compared_img, main_img):
        print("Duplicate file: " + image_files[main_img] + " and " + image_files[compared_img])

    # Function for appending items to a list
    def add_to_list(filename, list):
        list.append(filename)

    # Function for checking the quality of compared images, appends the lower quality image to the list
    def check_img_quality(directory, imageA, imageB, list):
        size_imgA = os.stat(directory + imageA).st_size
        size_imgB = os.stat(directory + imageB).st_size
        if size_imgA > size_imgB:
            dif.add_to_list(imageB, list)
        else:
            dif.add_to_list(imageA, list)
    
    def delete_imgs(directory, filenames_set):
        print("\nDeletion in progress...")
        deleted = 0
        for filename in filenames_set:
            try:
                os.remove(directory + filename) 
                print("Deleted file:" , filename)
                deleted += 1
            except:
                print("Could not delete file:" , filename)
        print("\n***\nDeleted" , deleted , "duplicates.")
            