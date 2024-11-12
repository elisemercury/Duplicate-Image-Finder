import cupy as cp


squared_diff_generic = cp.ElementwiseKernel(
    in_params='T x, T y',
    out_params='T z',
    operation='z = (x - y) * (x - y)',
    name='squared_diff_generic')


def mse_gpu(image_a: cp.ndarray, image_b: cp.ndarray) -> float:
    """
    A GPU accelerated version of the mean squared error function.

    :param image_a: The first image to compare
    :param image_b: The second image to compare
    """
    sq_diff = squared_diff_generic(cp.array(image_a).astype("float"), cp.array(image_b).astype("float"))
    sum_diff = cp.sum(sq_diff)

    px_count = image_a.shape[0] * image_a.shape[1]
    return float(sum_diff / px_count)