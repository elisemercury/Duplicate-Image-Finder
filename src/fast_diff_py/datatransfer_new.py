from typing import Optional, List, Dict, Union, Tuple

from pydantic import BaseModel, Field, ConfigDict

class PreprocessArg(BaseModel):
    """
    Args for the preprocess function
    """
    file_path: str = Field(...,
                            description="The path to the file to preprocess")
    key: int = Field(...,
                        description="The key in the db where to store the hash")

    model_config = ConfigDict(
        populate_by_name=True
    )

class PreprocessResult(BaseModel):
    """
    Return type for the preprocess function
    """
    key: int = Field(...,
                     description="The key in the db where the hash is stored")

    org_x: Optional[int] = Field(-1,
                      description="The original x size of the image, empty on error")

    org_y: Optional[int] = Field(-1,
                        description="The original y size of the image, empty on error")

    hash_0: Optional[Union[str, int]] = Field(None,
                                       description="The hash of the image at 0 degrees")
    hash_90: Optional[Union[str, int]] = Field(None,
                                        description="The hash of the image at 90 degrees")
    hash_180: Optional[Union[str, int]] = Field(None,
                                         description="The hash of the image at 180 degrees")
    hash_270: Optional[Union[str, int]] = Field(None,
                                         description="The hash of the image at 270 degrees")

    error: Optional[str] = Field(None,
                                    description="The error message if the function failed")

    model_config = ConfigDict(
        populate_by_name=True
    )


class SecondLoopArgs(BaseModel):
    """
    The next iteration of the second loop model
    """
    x: int = Field(...,
                   description="The x image of the batch")
    y: int = Field(...,
                   description="The lowest y value of the batch")
    y_batch: int = Field(...,
                        description="The size of the batch")

    # paths
    x_path: Optional[str] = Field(None,
                                  description="Path to the x image")
    y_path: Optional[List[str]] = Field(None,
                                        description="List of Paths to y images")

    # Sizes
    x_size: Optional[Tuple[int, int]] = Field(None,
                                              description="Image Size of the x image")
    y_size: Optional[List[Tuple[int, int]]] = Field(None,
                                                    description="List of Sizes of the y images")

    # Hashes
    x_hashes: Optional[Tuple[int, int, int, int]] = Field(None,
                                                          description="Hashes of x image")
    y_hashes: Optional[List[Tuple[int, int, int, int]]] = Field(None,
                                                                description="List of Hashes of the y images")

    cache_key: int = Field(...,
                           description="The key of the cache to copy")

    model_config = ConfigDict(
        populate_by_name=True
    )


class SecondLoopResults(BaseModel):
    cache_key: int = Field(...,
                           description="The cache key, to update the progress dict")
    x: int = Field(...,
                   description="The row to mark as done in the progress dict")

    errors: List[Tuple[int, int, str]] = Field([],
                                               description="All Errors encountered while processing, key_x, key_y, tb")
    success: List[Tuple[int, int, int, float]] = Field([],
                                                       description="Success of the comparison,"
                                                                   " key_x, key_y, success_type, diff")

    model_config = ConfigDict(
        populate_by_name=True
    )