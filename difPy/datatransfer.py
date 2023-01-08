from dataclasses import dataclass
import json
from typing import Union


@dataclass
class PreprocessArguments:
    # TODO different amounts for different colors.
    key: int
    in_path: str
    out_path: str

    size_x: int
    size_y: int

    compute_hash: bool
    store_thumb: bool

    amount: int
    dir_a: bool = True

    @staticmethod
    def from_json(json_string: str):
        """
        Create a PreprocessArguments object from a json dict. (jsonified by the to_json method of the class)
        :param json_string: string to convert to object.
        :return:
        """
        obj_dict = json.loads(json_string)
        keys = obj_dict.keys()

        target_keys = ["in_path", "out_path", "size_x", "size_y", "compute_hash", "amount", "store_thumb", "key",
                       "dir_a"]
        if not all(x in keys for x in target_keys):
            raise ValueError("Provided Json String doesn't contain the necessary keys.")

        return PreprocessArguments(in_path=obj_dict["in_path"],
                                   out_path=obj_dict["out_path"],
                                   size_x=obj_dict["size_x"],
                                   size_y=obj_dict["size_y"],
                                   compute_hash=obj_dict["compute_hash"],
                                   amount=obj_dict["amount"],
                                   store_thumb=obj_dict["store_thumb"],
                                   key=int(obj_dict["key"]),
                                   dir_a=obj_dict["dir_a"])

    def to_dict(self):
        """
        Convert object to dict
        :return:
        """
        return {
            "in_path": self.in_path,
            "out_path": self.out_path,
            "size_x": self.size_x,
            "size_y": self.size_y,
            "compute_hash": self.compute_hash,
            "amount": self.amount,
            "store_thumb": self.store_thumb,
            "key": self.key,
            "dir_a": self.dir_a,
        }

    def to_json(self):
        """
        Convert an Object into json string.
        :return:
        """
        return json.dumps(self.to_dict())


@dataclass
class PreprocessResults:
    key: int
    in_path: str
    out_path: str

    success: bool

    original_x: int
    original_y: int

    hash_0: str
    hash_90: str
    hash_180: str
    hash_270: str

    error: str
    dir_a: bool = True

    @staticmethod
    def from_json(json_string: str):
        """
        Create the PreprocessResults Object from a json dict (jsonified by the to_json method of the object)
        :param json_string: string to convert to object.
        :return:
        """
        obj_dict = json.loads(json_string)
        keys = obj_dict.keys()

        target_keys = ["in_path", "out_path", "original_x", "original_y", "hash_0", "hash_90", "hash_180", "hash_270",
                       "success", "error", "key", "dir_a"]

        if not all(x in keys for x in target_keys):
            raise ValueError("Provided Json String doesn't contain the necessary keys.")

        return PreprocessResults(in_path=obj_dict["in_path"],
                                 out_path=obj_dict["out_path"],
                                 original_x=obj_dict["original_x"],
                                 original_y=obj_dict["original_y"],
                                 success=obj_dict["success"],
                                 hash_0=obj_dict["hash_0"],
                                 hash_90=obj_dict["hash_90"],
                                 hash_180=obj_dict["hash_180"],
                                 hash_270=obj_dict["hash_270"],
                                 error=obj_dict["error"],
                                 key=int(obj_dict["key"]),
                                 dir_a=obj_dict["dir_a"])

    @staticmethod
    def error_obj(in_path: str, out_path: str, error: str, key: int, dir_a: bool):
        return PreprocessResults(
            in_path=in_path,
            out_path=out_path,
            success=False,
            error=error,
            original_x=-1,
            original_y=-1,
            hash_0="<ERROR>",
            hash_90="<ERROR>",
            hash_180="<ERROR>",
            hash_270="<ERROR>",
            key=key,
            dir_a=dir_a,
        )

    @staticmethod
    def no_hash_init(in_path: str, out_path: str, original_x: int, original_y: int, key: int, dir_a: bool):
        return PreprocessResults(
            in_path=in_path,
            out_path=out_path,
            success=True,
            error="<EMPTY>",
            original_x=original_x,
            original_y=original_y,
            hash_0="<EMPTY>",
            hash_90="<EMPTY>",
            hash_180="<EMPTY>",
            hash_270="<EMPTY>",
            key=key,
            dir_a=dir_a,
        )

    def to_dict(self):
        """
        Convert object to dict representation
        :return:
        """
        return {
            "in_path": self.in_path,
            "out_path": self.out_path,
            "original_x": self.original_x,
            "original_y": self.original_y,
            "hash_0": self.hash_0,
            "hash_90": self.hash_90,
            "hash_180": self.hash_180,
            "hash_270": self.hash_270,
            "success": self.success,
            "error": self.error,
            "key": self.key,
            "dir_a": self.dir_a,
        }

    def to_json(self):
        """
        Converts an object into json string.
        :return:
        """
        return json.dumps(self.to_dict())


@dataclass
class CompareImageArguments:
    img_a: str
    img_b: str

    thumb_a: Union[str, None]
    thumb_b: Union[str, None]

    key_a: int
    key_b: int

    store_compare: bool
    compare_threshold: float
    store_path: str

    size_x: int
    size_y: int

    is_dir_b: bool = False

    @staticmethod
    def from_json(json_string: str):
        """
        Create the CompareImageArguments Object from a json dict (jsonified by the to_json method of the object)
        :param json_string: string to convert to object.
        :return:
        """
        obj_dict = json.loads(json_string)
        keys = obj_dict.keys()

        target_keys = ["img_a", "img_b", "thumb_a", "thumb_b", "key_a", "key_b", "store_compare", "compare_threshold",
                       "is_dir_b", "store_path", "size_x", "size_y"]

        if not all(x in keys for x in target_keys):
            raise ValueError("Provided Json String doesn't contain the necessary keys.")

        return CompareImageArguments(img_a=obj_dict["img_a"],
                                     img_b=obj_dict["img_b"],
                                     thumb_a=obj_dict["thumb_a"],
                                     thumb_b=obj_dict["thumb_b"],
                                     key_a=int(obj_dict["key_a"]),
                                     key_b=int(obj_dict["key_b"]),
                                     store_compare=obj_dict["store_compare"],
                                     compare_threshold=obj_dict["compare_threshold"],
                                     is_dir_b=obj_dict["is_dir_b"],
                                     store_path=obj_dict["store_path"],
                                     size_x=obj_dict["size_x"],
                                     size_y=obj_dict["size_y"],
                                     )

    def to_dict(self):
        """
        Convert object to dict representation
        :return:
        """
        return {
            "img_a": self.img_a,
            "img_b": self.img_b,
            "thumb_a": self.thumb_a,
            "thumb_b": self.thumb_b,
            "key_a": self.key_a,
            "key_b": self.key_b,
            "store_compare": self.store_compare,
            "compare_threshold": self.compare_threshold,
            "is_dir_b": self.is_dir_b,
            "store_path": self.store_path,
            "size_x": self.size_x,
            "size_y": self.size_y,
        }

    def to_json(self):
        """
        Convert object to json string
        :return:
        """
        return json.dumps(self.to_dict())


@dataclass
class CompareImageResults:
    key_a: int
    key_b: int

    error: str
    success: bool

    min_avg_diff: float
    is_dir_b: bool

    @staticmethod
    def from_json(json_string: str):
        """
        Create the CompareImageResults Object from a json dict (jsonified by the to_json method of the object)
        :param json_string: string to convert to object.
        :return:
        """
        obj_dict = json.loads(json_string)
        keys = obj_dict.keys()

        target_keys = ["key_a", "key_b", "error", "success", "min_avg_diff", "is_dir_b"]

        if not all(x in keys for x in target_keys):
            raise ValueError("Provided Json String doesn't contain the necessary keys.")

        return CompareImageResults(key_a=int(obj_dict["key_a"]),
                                   key_b=int(obj_dict["key_b"]),
                                   error=obj_dict["error"],
                                   success=obj_dict["success"],
                                   min_avg_diff=obj_dict["min_avg_diff"],
                                   is_dir_b=obj_dict["is_dir_b"])

    def to_dict(self):
        """
        Convert object to dict representation
        :return:
        """
        return {
            "key_a": self.key_a,
            "key_b": self.key_b,
            "error": self.error,
            "success": self.success,
            "min_avg_diff": self.min_avg_diff,
            "is_dir_b": self.is_dir_b,
        }

    def to_json(self):
        """
        Convert object to json string
        :return:
        """
        return json.dumps(self.to_dict())