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

class BatchCompareArgs(BaseModel):
    key: int = Field(...,
                        description="The key in the db of the end of that diff row.")

    key_a: int = Field(...,
                        description="Key in dir table of start image a")
    key_b: int = Field(...,
                        description="Key in dir table of end image b")

    max_size_b: int = Field(...,
                            description="Maximum distance we can move to the left")

    cache_key: Optional[int] = Field(None,
                                        description="The key in the cache table")

    path_a: Optional[str] = Field(None,
                                    description="The path to the original image a - when there's no RAM Cache")
    path_b: Optional[List[str]] = Field(None,
                                        description="The path to the original set of image b - "
                                                    "when there's no RAM Cache")

class BatchCompareResult(BaseModel):
    """
    Return type for the batch compare function
    """
    key: int = Field(...,
                     description="The key in the db of the end of that diff row. (In theory for diff-plots)")

    key_a: int = Field(...,
                       description="Key in dir table of start image a")
    key_b: int = Field(...,
                       description="Key in dir table of end image b")

    # diff: List[Tuple[int, float]] = Field(...,
    #                     description="First element, key in the dif table, "
    #                                 "second element the difference between the images")
    diff: List[float] = Field(...,
                        description="The difference between the images")

    # Make lookup from the key in the dif table, so relative to the key parameter in the function, so it can be
    # unwrapped and inserted easily
    # errors: List[Tuple[int, str]] = Field(...,
    #                                 description="First element, key in the dif table, "
    #                                             "second element the error message")
    errors: Dict[int, str] = Field(...,
                                   description="The error message if the function failed")

    cache_key: Optional[int] = Field(None,
                                        description="The key in the cache table")

    model_config = ConfigDict(
        populate_by_name=True
    )


class ItemCompareArgs(BaseModel):
    key: int = Field(...,
                        description="The key in the db of the start of that diff row. (In theory for diff-plots)")

    key_a: int = Field(...,
                        description="Key in dir table of start image a")
    key_b: int = Field(...,
                        description="Key in dir table of start image b")

    path_a: str = Field(...,
                        description="The path to the original image a")
    path_b: str = Field(...,
                        description="The path to the original image b")

    cache_key: Optional[int] = Field(None,
                                        description="The key in the cache table")

    model_config = ConfigDict(
        populate_by_name=True
    )


class ItemCompareResult(BaseModel):
    key: int = Field(...,
                     description="The key in the db of the start of that diff row. (In theory for diff-plots)")

    diff: float = Field(...,
                        description="The difference between the images")

    error: Optional[str] = Field(None,
                                    description="The error message if the function failed")