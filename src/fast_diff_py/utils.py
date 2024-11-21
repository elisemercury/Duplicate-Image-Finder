import base64
import hashlib
import itertools
import json
import pickle
from typing import Any, Union
from dataclasses import dataclass

import numpy as np

"""
File contains a small list of utilities for the main classes. The utilities are not specific to this project but are a 
nice to have.
"""


@dataclass
class BlockProgress:
    x: int
    y: int
    done: bool = False


def hash_np(mat: np.ndarray) -> str:
    """
    Hashes a np array by performing a hash of its underlying buffer.
    :param mat: multidimensional numpy array.
    :return: hash
    """
    sha256_hash = hashlib.sha1()
    sha256_hash.update(pickle.dumps(mat))
    return sha256_hash.hexdigest()


def hash_file(path) -> str:
    """
    Hashes a file with sha256
    :param path: file_path to hash
    :return:
    """
    sha256_hash = hashlib.sha1()
    with open(path, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
        result = sha256_hash.hexdigest()
    return result


def walking_hash(mat: np.ndarray) -> str:
    """
    Given an multidimensional numpy array, walk along each axis in descending order and add each element to the hash

    :param mat: multidimensional array
    :return: hash of array
    """

    sha256_hash = hashlib.sha256()

    def walk(hobj, array):
        # if we're at a leaf, update the hash
        if len(np.shape(array)) == 0:
            hobj.update(array)
            return

        for x in array:
            walk(hobj, x)

    walk(sha256_hash, mat)
    return sha256_hash.hexdigest()


def fill(base: str, length: int, fill_char: str = " ", left: bool = True) -> str:
    """
    Fill a string with a character to a certain length.
    Equivalent to std::left << std::setw(...) << "Something" << std::fill(...) in C++;
    :param base: the thing to extend to certain length
    :param length: length to extend to
    :param fill_char: character to fill up with
    :param left: fill to the left or right
    :return:
    """
    if len(base) >= length:
        return base

    if left:
        return base + fill_char * (length - len(base))
    else:
        return fill_char * (length - len(base)) + base


def sizeof_fmt(num: Union[int, float], suffix: str = "B", base2: bool = False) -> str:
    """
    Return a Human readable number given an integer

    :param num: Number to format human-readable
    :param suffix: Unit Suffix for the Number
    :param base2: If the Output is in Base2 or Base10

    :return: Human-Readable String of the size
    """
    if base2:
        for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
            if abs(num) < 1024.0:
                return f"{num:3.1f}{unit}{suffix}"
            num /= 1024.0
        return f"{num:.1f}Yi{suffix}"
    else:
        for unit in ("", "K", "M", "G", "T", "P", "E", "Z"):
            if abs(num) < 1000.0:
                return f"{num:3.1f}{unit}{suffix}"
            num /= 1000.0
        return f"{num:.1f}Y{suffix}"


def build_start_blocks_ab(a_size: int, b_size: int, block: int):
    """
    Build a list that contains the upper left corner of each block for blocking matrix multiplication. (None Symmetric)

    :param a_size: Number of rows
    :param b_size: Number of columns
    :param block: size of blocks into which to partition the matrix
    """
    a_start = [a for a in range(0, a_size, block)]
    b_start = [b for b in range(0, b_size, block)]
    start_vtx = []

    for elm in itertools.product(a_start, b_start):
        start_vtx.append(BlockProgress(x=elm[0], y=elm[1]))

    return start_vtx


def build_start_blocks_a(a_size: int, block: int):
    """
    Build a list that contains the upper left corner of each block for blocking matrix multiplication. (Symmetric)

    :param a_size: Size of Matrix in rows and columns
    :param block: size of blocks into which to partiton the matrix
    """
    a_start = [a for a in range(0, a_size, block)]
    start_vtx = []

    for elm in itertools.product(a_start, a_start):
        if elm[0] <= elm[1]:
            start_vtx.append(BlockProgress(x=elm[0], y=elm[1]))
    start_vtx.sort(key=lambda b: (b.y> - b.x, b.x + b.y))

    return start_vtx


def to_b64(to_encode: Any):
    """
    Convert an object to a b64 string

    :param to_encode: object to encode
    :return: base64 string
    """
    json_str = json.dumps(to_encode)
    bytes_string = json_str.encode("utf-8")
    return base64.standard_b64encode(bytes_string).decode("utf-8")


def from_b64(b64_string: str):
    """
    Convert a b64 string to a python object

    :param b64_string: a b64 encoded python object
    :return: a python object
    """
    bytes_string = base64.standard_b64decode(b64_string.encode("utf-8"))
    json_string = bytes_string.decode("utf-8")
    return json.loads(json_string)
