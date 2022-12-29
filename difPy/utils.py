import math
import hashlib
import numpy as np

"""
File contains a small list of utilities for the main classes. The utilities are not specific to this project but are a 
nice to have.
"""


def hash_np(mat: np.ndarray) -> str:
    """
    Hashes a np array by performing a hash of its underlying buffer.
    :param mat: multidimensional numpy array.
    :return: hash
    """
    sha256_hash = hashlib.sha256()
    sha256_hash.update(mat.data)
    return sha256_hash.hexdigest()


def hash_file(path) -> str:
    """
    Hashes a file with sha256
    :param path: file_path to hash
    :return:
    """
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
        result = sha256_hash.hexdigest()
    return result


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


def h(x: int, unit: str, base2: bool = False) -> str:
    """
    Convert an integer representing a byte number into a human-readable format. I.e. 3 digits of precision.

    :param x: number to convert
    :param unit: unit to use (e.g. "B" for bytes)
    :param base2: use base 2 (1024) or base 10 (1000) for conversion
    """

    if base2:
        digits = math.log2(x) / 10

        # Quetti-sth (Quetta)
        if digits > 30:
            return f"{x / 2 ** 300:.3f} Qi{unit}"

        # Ronni-sth (Ronna)
        elif digits > 27:
            return f"{x / 2 ** 270:.3f} Ri{unit}"

        # Yotti-sth (Yotta)
        elif digits > 24:
            return f"{x / 2 ** 240:.3f} Yi{unit}"

        # Zetti-sth (Zetta)
        elif digits > 21:
            return f"{x / 2 ** 210:.3f} Zi{unit}"

        # Exi-sth (Exa)
        elif digits > 18:
            return f"{x / 2 ** 180:.3f} Ei{unit}"

        # Petti-sth (Peta)
        elif digits > 15:
            return f"{x / 2 ** 150:.3f} Pi{unit}"

        # Tetti-sth (Tera)
        elif digits > 12:
            return f"{x / 2 ** 120:.3f} Ti{unit}"

        # Gigi-sth (Giga)
        elif digits > 9:
            return f"{x / 2 ** 90:.3f} Gi{unit}"

        # Megi-sth (Mega)
        elif digits > 6:
            return f"{x / 2 ** 60:.3f} Mi{unit}"

        # Kili-sth (Kilo)
        elif digits > 3:
            return f"{x / 2 ** 30:.3f} Ki{unit}"

        # Default
        else:
            return f"{x} {unit}"

    else:
        digits = math.log10(x)

        # Quetta-sth (Quetta)
        if digits > 30:
            return f"{x / 10 ** 30:.3f} Q{unit}"

        # Ronna-sth (Ronna)
        elif digits > 27:
            return f"{x / 10 ** 27:.3f} R{unit}"

        # Yotta-sth (Yotta)
        elif digits > 24:
            return f"{x / 10 ** 24:.3f} Y{unit}"

        # Zetta-sth (Zetta)
        elif digits > 21:
            return f"{x / 10 ** 21:.3f} Z{unit}"

        # Exa-sth (Exa)
        elif digits > 18:
            return f"{x / 10 ** 18:.3f} E{unit}"

        # Petta-sth (Peta)
        elif digits > 15:
            return f"{x / 10 ** 15:.3f} P{unit}"

        # Tetta-sth (Tera)
        elif digits > 12:
            return f"{x / 10 ** 12:.3f} T{unit}"

        # Giga-sth (Giga)
        elif digits > 9:
            return f"{x / 10 ** 9:.3f} G{unit}"

        # Mega-sth (Mega)
        elif digits > 6:
            return f"{x / 10 ** 6:.3f} M{unit}"

        # Kilo-sth (Kilo)
        elif digits > 3:
            return f"{x / 10 ** 3:.3f} K{unit}"

        # Default
        else:
            return f"{x} {unit}"
