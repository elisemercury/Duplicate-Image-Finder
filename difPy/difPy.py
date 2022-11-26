from __future__ import annotations

import sys
import itertools
import numpy as np

from PIL import Image
from pathlib import Path


class ProgressHandler:
    '''
    '''
    handle = lambda x, y: None


class ImageMatrix:
    '''
    Represents an image and contains its path, tensor and image object.
    '''

    def __init__(self, path: Path, image: Image, tensor: np.ndarray) -> None:
        '''
        Initialize an ImageMatrix object by specifying its path, tensor and
        Image object.

        Parameters:
            path            file system path of the image
            image           the associated image pillow object
            tensor          the numpy tensor associated with the image

        Returns:
            None
        '''
        self.path = path.absolute()
        self.image = image
        self.tensor = tensor

        self.mse_map = {}
        self.duplicates = []

    def __str__(self) -> str:
        '''
        The string representation of an ImageMatrix is simply it's path.

        Parameters:
            None

        Returns:
            path of the underlying image
        '''
        return str(self.path)
    
    def compare(self, other: ImageMatrix, rotate: bool, threshold: int = 0) -> int:
        '''
        Compare the ImageMatrix object to another one.

        Parameters:
            other           ImageMatrix object to compare to
            rotate          whether to rotate images
            threshold       return immidiately if mse is lower-equal

        Returns:
            the MSE between both ImageMatrix objects
        '''
        errors = []

        for _ in range(3):

            err = np.sum((self.tensor.astype('float') - other.tensor.astype('float')) ** 2)
            err /= float(self.tensor.shape[0] * self.tensor.shape[1])

            if not rotate or err <= threshold:
                return err

            elif rotate:
                other.rotate()
                errors.append(err)

            return min(errors)

    def rotate(self) -> None:
        '''
        Rotates the ImageMatrix object by 90 degrees.

        Parameters:
            None

        Returns:
            None
        '''
        self.tensor = np.rot90(self.tensor, k=1, axes=(0, 1))

    def plot(self) -> None:
        '''
        Plots an ImageMatrix and all it's duplicates.

        Parameters:
            None

        Returns:
            None
        '''
        if not self.duplicates:
            return

        try:
            import matplotlib.pyplot as plt

        except ImportError:
            return

        fig = plt.figure()
        rows = len(self.duplicates) / 4 + 1

        ax = fig.add_subplot(rows, 4, 1)
        ax.set_title('Original')
        plt.imshow(self.tensor, cmap=plt.cm.gray)
        plt.axis("off")

        for ctr in range(len(self.duplicates)):
            ax = fig.add_subplot(rows, 4, ctr + 2)
            ax.set_title(f'MSE: {self.mse_map[self.duplicates[ctr]]}')
            plt.imshow(self.duplicates[ctr].tensor, cmap=plt.cm.gray)
            plt.axis("off")

        plt.show()

    def compare_quality(self, other: ImageMatrix) -> bool:
        '''
        Compares the image quality of the current ImageMatrix to another one.

        Parameters:
            other           ImageMatrix object to compare to

        Returns:
            true if quality of current image is better, false otherwise
        '''
        if self.stat().st_size >= other.stat().st_size:
            return True

        return False

    def to_dict(self) -> dict:
        '''
        Return a dictionary containing some statistics for this ImageMatrix.

        Parameters:
            None

        Returns:
            dict with statistics
        '''
        stats_dict = {
                         'path': str(self.path),
                         'duplicate_count': len(self.duplicates),
                         'duplicates': [{'path': str(x.path), 'mse': self.mse_map[x]} for x in self.duplicates]
                     }

        return stats_dict

    def from_file(path: Path, px_size: int = 50) -> ImageMatrix:
        '''
        Create a new ImageMatrix object from the specified file.

        Parameters:
            path            the file system path of the image
            px_size         optional size to resize the image to

        Returns:
            ImageMatrix
        '''
        image = Image.open(path)

        if px_size is not None:
            image = image.resize((px_size, px_size), resample=Image.Resampling.BICUBIC)

        tensor = np.asarray(image)
        return ImageMatrix(path, image, tensor)

    def from_folder(path: Path, recursive: bool = False, px_size: int = 50) -> list[ImageMatrix]:
        '''
        Create new ImageMatrix objects from the specified folder.

        Parameters:
            path            the file system path of the folder
            recursive       whether to apply recursive search
            px_size         optional size to resize the image to

        Returns:
            list of ImageMatrix objects
        '''
        files = ImageMatrix._glob(path, recursive)
        return ImageMatrix.from_list(files, px_size)

    def from_list(paths: list[Path], px_size: int = 50) -> list[ImageMatrix]:
        '''
        Create new ImageMatrix objects from the specified list of paths.

        Parameters:
            paths            list of paths to create ImageMatrix objects from
            recursive       whether to apply recursive search
            px_size         optional size to resize the image to

        Returns:
            list of ImageMatrix objects
        '''
        total = len(paths)
        current = 0

        image_matrices = []
        for path in paths:

            if not path.is_file():
                return

            current += 1
            ProgressHandler.handle(current, total)

            try:
                image_matrix = ImageMatrix.from_file(path, px_size)
                image_matrices.append(image_matrix)

            except IOError:
                pass

        return image_matrices

    def _glob(path: Path, recursive: bool) -> list[Path]:
        '''
        Helper function to find all files within a Path.

        Parameters:
            path            the path to search in
            recursive       whether to search recursively

        Returns:
            list of path objects associated to files
        '''
        glob_pattern = '*'

        if recursive:
            glob_pattern = '**/*'

        items = path.glob(glob_pattern)
        files = [item for item in items if item.is_file()]

        return files


class ImageMatrixCollection:
    '''
    Represents a collection of multiple image matrices.
    '''

    def __init__(self, matrices: list[ImageMatrix]) -> None:
        '''
        Initialize an ImageMatrixCollection with the matrices that are part of it.

        Parameters:
            matrices            list of ImageMatrix objects

        Returns:
            None
        '''
        self.matrices = matrices

    def __iter__(self) -> ImageMatrix:
        '''
        Make ImageMatrixCollection iterable.

        Parameters:
            None

        Returns:
            next ImageMatrix
        '''
        for image_matrix in self.matrices:
            yield image_matrix

    def compare(self, other: ImageMatrixCollection, similarity: int, rotate: bool, fast: bool) -> None:
        '''
        Compare an ImageMatrixCollection to another one. The result of the operation is saved within
        the duplicates array and mse_map dictionary of each ImageMatrix object that was part of the
        operation.

        Parameters:
            other           the other ImageMatrixCollection to compare to
            rotate          whether to apply rotations during comparison
            fast            drop duplicates and do not further process them

        Returns:
            None
        '''
        self.multi_compare([other], similarity, rotate, fast)

    def multi_compare(self, others: list[ImageMatrixCollection], similarity: int, rotate: bool, fast: bool) -> None:
        '''
        Compare an ImageMatrixCollection to others. The result of the operation is saved within
        the duplicates array and mse_map dictionary of each ImageMatrix object that was part of the
        operation.

        Parameters:
            others          a list of ImageMatrixCollection to compare to
            rotate          whether to apply rotations during comparison
            fast            drop duplicates and do not further process them

        Returns:
            None
        '''
        total = 0
        current = 0
        combinations = []

        for other in others:
            combs = list(itertools.product(self.matrices, other.matrices))
            total += len(combs)
            combinations.append(combs)

        for combination in combinations:

            for element in combination:

                current += 1
                ProgressHandler.handle(current, total)

                image_a = element[0]
                image_b = element[1]

                if image_a.path == image_b.path:
                    continue

                if image_a in image_b.duplicates or image_b in image_a.duplicates:
                    continue

                mse = image_a.compare(image_b, rotate, similarity)
                if mse < similarity:

                    image_a.duplicates.append(image_b)
                    image_a.mse_map[image_b] = mse

                    image_b.duplicates.append(image_a)
                    image_b.mse_map[image_a] = mse

    def to_dict(self) -> list[dict]:
        '''
        Create a list of dictionaries containing statistic data about the ImageMatrices
        contained within the collection.

        Parameters:
            None

        Returns:
            list containing statistic data
        '''
        stats = []

        for image_matrix in self:
            stats.append(image_matrix.to_dict())

        return stats

    def from_folder(path: Path, recursive: bool = False, px_size: int = 50) -> ImageMatrixCollection:
        '''
        Create a new ImageMatrixCollection from a folder.

        Parameters:
            path            the file system path for searching images
            recursive       whether to search recursively
            px_size         resizing applied for each image
        '''
        image_matrices = ImageMatrix.from_folder(path, recursive, px_size)
        return ImageMatrixCollection(image_matrices)
