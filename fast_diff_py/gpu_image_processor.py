import cupy as cp
from types import FunctionType
import numpy as np
from fast_diff_py.cpu_image_processor import CPUImageProcessing


squared_diff_generic = cp.ElementwiseKernel(
    in_params='T x, T y',
    out_params='T z',
    operation='z = (x - y) * (x - y)',
    name='squared_diff_generic')


squared_diff_generic_reduce = cp.ReductionKernel(
    'T x, T y',
    'T z',
    '(x - y) * (x - y)',
    'a + b',
    'z = a',
    '0',
    'squared_diff_generic_reduce')


class GPUImageProcessing(CPUImageProcessing):
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
        # difference = cp.array(image_a).astype("float") - cp.array(image_b).astype("float")
        # sq_diff = cp.square(difference)
        # sq_diff = squared_diff_generic(cp.array(image_a).astype("float"), cp.array(image_b).astype("float"))
        # sum_diff = cp.sum(sq_diff)
        sum_diff = squared_diff_generic_reduce(cp.array(image_a).astype("float"), cp.array(image_b).astype("float"))
        px_count = image_a.shape[0] * image_a.shape[1]
        return float(sum_diff / px_count)
