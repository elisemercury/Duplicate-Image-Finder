"""
Use this file to generate test cases for duplicates. Two modes are supported:
- Partition
- Copy

## Partition Mode.
Partition mode is used to test for dir_a and dir_b. It has a probability to duplicate a file in both directories
and a probability with which a file is moved to the dir_b.
probability of duplication = 0.001 (is evaluated first)
probability of moving to dir_b = 0.5
The files can be moved or symlinked.

## Copy Mode
In Copy Mode, the files are copied with a probability to a secondary directory. The files in the initial directory are
always left. leading to a directory of duplicates and a directory of originals.
"""

import os
import random
from typing import Tuple
import shutil

def remove_prefix(text, prefix):
    """
    Remove a prefix from a string
    """
    if text.startswith(prefix):
        return text[len(prefix):]
    return text

def partition(source: str, dir_a: str, dir_b: str,pd: float = 0.001, pb: float = 0.5, sym: bool = False) -> Tuple[int, int, int]:
    """
    Partition mode to generate duplicates. Uses Symlinks in dir_a and dir_b to link to the files in the src directory

    :param source: The source directory
    :param dir_a: The first directory
    :param dir_b: The second directory
    :param pd: The probability of duplication
    :param pb: The probability of moving to dir_b
    :return: Number of files in dir a, number of files in dir b, number of duplicates
    """

    def partition_internal(src: str, cur: str, dir_a: str, dir_b: str, pd: float, pb: float, sym: bool) -> Tuple[int, int, int]:
        a, b, d = 0, 0, 0
        abs_src = os.path.abspath(src)
        abs_a = os.path.abspath(dir_a)
        abs_b = os.path.abspath(dir_b)
        cp = os.path.join(abs_src, cur)
        ca = os.path.join(abs_a, cur)
        cb = os.path.join(abs_b, cur)

        for f in os.listdir(cp):
            # If it's a directory, we need to recurse
            if os.path.isdir(os.path.join(cp, f)):
                na, nb, nd = partition_internal(src, os.path.join(cur, f), dir_a, dir_b, pd, pb, sym)
                a += na
                b += nb
                d += nd

            # If it's a file, we need to copy it
            elif os.path.isfile(os.path.join(cp, f)):
                # Duplicate the file
                if random.random() < pd:
                    # Create directory in dir_a
                    if not os.path.exists(ca):
                        os.makedirs(ca)

                    # Create directory in dir_b
                    if not os.path.exists(cb):
                        os.makedirs(cb)

                    if sym:
                        os.symlink(os.path.join(cp, f), os.path.join(ca, f))
                        os.symlink(os.path.join(cp, f), os.path.join(cb, f))
                    else:
                        shutil.move(os.path.join(cp, f), os.path.join(ca, f))
                        shutil.copy(os.path.join(ca, f), os.path.join(cb, f))
                    a, b, d = a + 1, b + 1, d + 1

                # Symlink to either or
                else:
                    # Symlink to dir_b
                    if random.random() < pb:
                        if not os.path.exists(cb):
                            os.makedirs(cb)
                        if sym:
                            os.symlink(os.path.join(cp, f), os.path.join(cb, f))
                        else:
                            shutil.move(os.path.join(cp, f), os.path.join(cb, f))
                        b += 1

                    # Symlink to dir_a
                    else:
                        if not os.path.exists(ca):
                            os.makedirs(ca)
                        if sym:
                            os.symlink(os.path.join(cp, f), os.path.join(ca, f))
                        else:
                            shutil.move(os.path.join(cp, f), os.path.join(ca, f))
                        a += 1
            else:
                print(f"Skipping {f}")

        return a, b, d

    return partition_internal(source, "", dir_a, dir_b, pd, pb, sym=sym)

def duplicate(src: str, dst: str, pc: float = 0.5) -> Tuple[int, int]:
    """
    Duplicate mode to generate duplicates.

    :param src: The first directory
    :param dst: The second directory
    :param pc: The probability of copying
    :return: Number of files in dir a, number of files in dir b
    """
    ...
    return 0, 0


if __name__ == "__main__":
    print(partition(source="/media/alisot2000/MacBeth/dedup_benchmarks/TQ-Picture-Benchmark/", dir_a="/media/alisot2000/MacBeth/workbench/dir_a", dir_b="/media/alisot2000/MacBeth/workbench/dir_b", pd=0.01, pb=0.5))