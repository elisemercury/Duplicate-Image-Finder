import os.path
from typing import Tuple, List
from dataclasses import dataclass
import numpy as np

import fast_diff_py.img_processing as imgp


class ImageCache:
    offset: int  # The offset from the key in the db to the index in the array
    img_shape: Tuple[int, int, int]
    data: np.ndarray[np.uint8]
    size: int

    def __init__(self, offset: int, size: int, img_shape: Tuple[int, int, int]):
        """
        Initialize a Cache Object storing a list of images
        """
        self.img_shape = img_shape
        self.offset = offset
        self.size = size
        np.ndarray((size, *img_shape), dtype=np.uint8)

    def get_image(self, key: int) -> np.ndarray[np.uint8]:
        """
        Get an image from the cache, returns a copy from the cache not the cache itself.
        """
        return self.data[key - self.offset].copy()

    def fill_thumbnails(self, thumbnail_dir: str):
        """
        Fill the cache with images from the thumbnail directory
        """
        for i in range(self.size):
            try:
                self.data[i] = imgp.load_std_image(img_path=os.path.join(thumbnail_dir, f"{i+self.offset}.png"),
                                                   target_size=(self.img_shape[0], self.img_shape[1]),
                                                   resize=False)
            # We encountered a value error -> The image didn't have the right shape when loaded.
            except ValueError as e:
                print(f"Thumbnail is not of correct size {i+self.offset}")
                raise e

            except Exception as e:
                print(f"Error loading image {i+self.offset}: {e}")
                self.data[i] = np.zeros(self.img_shape, dtype=np.uint8)

    def fill_original(self, paths: List[str]):
        """
        Fill the cache with images from the original paths

        Precondition: Length of Paths needs to be equal to the size of the cache

        :param paths: The paths to the original images
        """
        if len(paths) != self.size:
            raise ValueError("Paths and size of cache do not match")

        for i in range(self.size):
            try:
                self.data[i] = imgp.load_std_image(img_path=paths[i],
                                                   target_size=(self.img_shape[0], self.img_shape[1]),
                                                   resize=True)
            except Exception as e:
                print(f"Error loading image {i+self.offset}: {e}")
                self.data[i] = np.zeros(self.img_shape, dtype=np.uint8)

@dataclass
class BatchCache:
    x: ImageCache
    y: ImageCache

