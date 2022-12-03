from __future__ import annotations

import itertools
import numpy as np

from PIL import Image
from typing import Any
from pathlib import Path
from operator import attrgetter


class ProgressHandler:
    '''
    '''
    handle = lambda x, y: None

    def __init__(self, handle: callable = handle) -> None:
        '''
        ProgressHandler objects are initialized with the desired progress
        handling function.

        Parameters:
            handler         callable that is used for tracking progress

        Returns:
            None
        '''
        self.handle = handle


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

        self.fast_dup = False

    def __str__(self) -> str:
        '''
        The string representation of an ImageMatrix is simply it's path.

        Parameters:
            None

        Returns:
            path of the underlying image
        '''
        return str(self.path)

    def __eq__(self, other: Any) -> bool:
        '''
        Two ImageMatrix objects are considered equal if their path is the same.

        Parameters:
            other           object to compare with

        Returns:
            None
        '''
        if type(other) is not type(self):
            return False

        return other.path == self.path

    def __hash__(self) -> int:
        '''
        Make ImageMatrix hashable. The hash is computed based on its path.

        Parameters:
            None

        Returns:
            hash
        '''
        return hash(self.path)

    def compare(self, other: ImageMatrix, rotate: bool, threshold: int = 0, fast: bool = False) -> int:
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

        if fast and self.fast_dup:
            return 1000

        if self.path == other.path:
            return 0

        if self in other.duplicates:
            return other.mse_map[self]

        if other in self.duplicates:
            return self.mse_map[other]

        for _ in range(3):

            err = np.sum((self.tensor.astype('float') - other.tensor.astype('float')) ** 2)
            err /= float(self.tensor.shape[0] * self.tensor.shape[1])

            if not rotate:
                return err

            if err < threshold:

                self.duplicates.append(other)
                self.mse_map[other] = err

                other.duplicates.append(self)
                other.mse_map[self] = err

                if fast:
                    other.fast_dup = True

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

    def quality(self) -> int:
        '''
        Returns the size of the underlying image file.

        Parameters:
            None

        Returns:
            size of the underlying image file
        '''
        return self.path.stat().st_size

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

    def from_list(paths: list[Path], px_size: int = 50, pbar: ProgressHandler = None) -> list[ImageMatrix]:
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

        if pbar is None:
            pbar = ProgressHandler()

        image_matrices = []
        for path in paths:

            if not path.is_file():
                return

            try:
                image_matrix = ImageMatrix.from_file(path, px_size)
                image_matrices.append(image_matrix)

                current += 1
                pbar.handle(current, total)

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
        for image_matrix in sorted(self.matrices, key=attrgetter('path')):
            yield image_matrix

    def compare(self, other: ImageMatrixCollection, similarity: int, rotate: bool, fast: bool, pbar: ProgressHandler = None) -> None:
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
        self.multi_compare([other], similarity, rotate, fast, pbar)

    def multi_compare(self, others: list[ImageMatrixCollection], similarity: int, rotate: bool, fast: bool, pbar: ProgressHandler = None) -> None:
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
        current = 0

        if pbar is None:
            pbar = ProgressHandler()

        combinations = self.combinations(others)
        total = len(combinations)

        for comb in combinations:

            current += 1
            pbar.handle(current, total)

            comb[0].compare(comb[1], rotate, similarity, fast)

    def combinations(self, others: list[ImageMatrixCollection]) -> list[tuple[ImageMatrix, ImageMatrix]]:
        '''
        Returns a list of all possible ImageMatrix combinations.

        Parameters:
            other           the other ImageMatrixCollection to build combinations with

        Returns:
            list of possible combinations
        '''
        combinations = []

        for other in others:
            combs = list(itertools.product(self.matrices, other.matrices))
            combinations += combs

        return combinations

    def size(self) -> int:
        '''
        Return the number of ImageMatrix objects within the collection.

        Parameters:
            None

        Returns:
            numer of ImageMatrix objects in the collection.
        '''
        return len(self.matrices)

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

    def remove_matrix(self, matrix: ImageMatrix) -> None:
        '''
        Remove an ImageMatrix from the collection. Also remove all references
        to this matrix in other ImageMatrix objects.

        Parameters:
            matrix          the ImageMatrix to remove

        Returns:
            None
        '''
        self.matrices.remove(matrix)

        for image_matrix in self:

            try:
                image_matrix.duplicates.remove(matrix)

            except ValueError:
                pass

    def get_higher_quality(self, fast: bool = False) -> list[ImageMatrix]:
        '''
        Get a list of unique highes quality images from the collection.

        Parameters:
            fast            whether fast option was used during comparison

        Returns:
            list of unique highest quality images
        '''
        high_qual = []
        processed = []

        for image_matrix in self:

            if image_matrix in processed:
                continue

            current = image_matrix
            quality = image_matrix.quality()
            processed.append(image_matrix)

            for duplicate in image_matrix.duplicates:

                processed.append(duplicate)
                dup_quality = duplicate.quality()

                if dup_quality > quality:

                    current = duplicate
                    quality = dup_quality

                if fast:
                    for dupdup in duplicate.duplicates:

                        try:
                            high_qual.remove(dupdup)

                        except ValueError:
                            pass

            high_qual.append(current)

        return high_qual

    def get_duplicates(self, fast: bool = False) -> list[ImageMatrix]:
        '''
        Return a list of duplicate ImageMatrix collections within the current collection.
        The highest quality image among the duplicates is excluded.

        Parameters:
            fast            whether fast option was used during comparison

        Returns:
            list of duplicates
        '''
        processed = []
        duplicates = set()

        for image_matrix in self:

            if image_matrix in processed:
                continue

            current = image_matrix
            quality = image_matrix.quality()
            processed.append(image_matrix)

            for duplicate in image_matrix.duplicates:

                processed.append(duplicate)
                dup_quality = duplicate.quality()

                if dup_quality > quality:

                    current = duplicate
                    quality = dup_quality

                duplicates.add(duplicate)

                if fast:
                    for dupdup in duplicate.duplicates:
                        duplicates.add(dupdup)
                        processed.append(dupdup)

            try:
                duplicates.remove(current)

            except KeyError:
                pass

        return list(duplicates)

    def from_folder(path: Path, recursive: bool = False, px_size: int = 50) -> ImageMatrixCollection:
        '''
        Create a new ImageMatrixCollection from a folder.

        Parameters:
            path            the file system path for searching images
            recursive       whether to search recursively
            px_size         resizing applied for each image

        Returns:
            ImageMatrixCollection containing all found image files
        '''
        image_matrices = ImageMatrix.from_folder(path, recursive, px_size)
        return ImageMatrixCollection(image_matrices)

    def from_list(paths: list[Path], px_size: int = 50, pbar: ProgressHandler = None) -> ImageMatrixCollection:
        '''
        Create a new ImageMatrixCollection from a list of paths.

        Parameters:
            path            the file system path for searching images
            recursive       whether to search recursively
            px_size         resizing applied for each image

        Returns:
            ImageMatrixCollection containing all specified image files
        '''
        image_matrices = ImageMatrix.from_list(paths, px_size, pbar)
        return ImageMatrixCollection(image_matrices)
