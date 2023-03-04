import cupy as cp
from types import FunctionType
import numpy as np
from fast_diff_py.image_processor import ImageProcessing as CIP


# sample for the idiot I am.
# import matplotlib.pyplot as plt
# import numpy as np
# import cv2
#
# # Some example data to display
# x = np.linspace(0, 2 * np.pi, 400)
# y = np.sin(x ** 2)
#
# fig, ax = plt.subplots()
# ax.plot(x, y)
# ax.set_title('A single plot')
# plt.show()
#
# fig, axs = plt.subplots(2, 2)
# fig.suptitle('Vertically stacked subplots')
# axs[0][0].plot(x, y)
# axs[1][0].plot(x, -y)
#
# im_a = "/home/alisot2000/Desktop/SAMPLE_MIRA/JOIN/20221206_014252.jpg"
# im_b = "/home/alisot2000/Desktop/SAMPLE_MIRA/JOIN/0C2E9779-8E7C-4044-B2D3-07C8F8650527.jpeg"
#
# im_a_mat = cv2.imdecode(np.fromfile(im_a, dtype=np.uint8), cv2.IMREAD_COLOR)
# im_b_mat = cv2.imdecode(np.fromfile(im_b, dtype=np.uint8), cv2.IMREAD_COLOR)
#
# axs[0][1].imshow(im_a_mat, cmap=plt.cm.gray)
# axs[1][1].imshow(im_b_mat, cmap=plt.cm.gray)
#
# plt.show()


class GPUImageProcessing(CIP):
    """
    This class Contains the functions to process a single image or a pari of images.

    The intent of this class is to be instantiated in the parallel processes running as slaves. It gets passed the
    arguments from the slave and then has the ability to reuse parts of the computation from before (say you have an
    all to all comparison, you can have one slave keep one image constant and iterate through the others.)

    The class needs to be aware of the availability of cuda / cupy and use it if indicated by the slave running the
    class.
    """

    def __init__(self, identifier: int, comp: FunctionType = None):
        """
        Identifier provided by the parent process. Used to identify the process in the console.

        Specification of comparison:
        Input: two np.ndarray of the same shape. (the images)
        Output: float value of the computed difference.

        :param identifier: process id (not pid)
        :param comp: comparison function to use. If none is provided, the default is used.
        """
        super().__init__(identifier, comp)

    @staticmethod
    def mse(image_a: np.ndarray, image_b: np.ndarray) -> float:
        """
        A GPU accelerated version of the mean squared error function.
        """
        difference = cp.array(image_a).astype("float") - cp.array(image_b).astype("float")
        sq_diff = cp.square(difference)
        sum_diff = cp.sum(sq_diff)
        px_count = image_a.shape[0] * image_a.shape[1]
        return sum_diff / px_count
