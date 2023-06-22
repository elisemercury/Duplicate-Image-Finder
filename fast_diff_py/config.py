import json
import os
import datetime
from typing import Union, List
import warnings


class FastDiffPyConfig:
    cfg_path: str
    update_timeout: int = 30

    __cfg_dict: dict
    __last_update: datetime.datetime

    # Config from Class
    __p_root_dir_a: str
    __p_root_dir_b: Union[str, None]

    __thumb_dir_a: str
    __thumb_dir_b: Union[str, None]

    __thumbnail_size_x = 64
    __thumbnail_size_y = 64

    __similarity_threshold = 200

    __has_dir_b: bool = False

    __ignore_names: List[str]
    __ignore_paths: List[str]

    __enough_images_to_compare: bool = False

    # argument storage
    __sl_matching_hash: bool = False
    __sl_has_thumb: bool = False
    __sl_matching_aspect: bool = False
    __sl_make_diff_plots: bool = False
    __sl_plot_output_dir: str = None

    __supported_file_types = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".gif", ".webp"}

    # default config
    __less_optimized: bool = False
    __retry_limit: int = 1000

    __verbose: bool = False

    def __init__(self, path: str = None, purge: bool = False):
        # set the config_path
        if path is None:
            self.cfg_path = os.path.join(os.path.dirname(__file__), "config.json")

        self.__cfg_dict = {}

        if os.path.exists(self.cfg_path):
            if purge:
                os.remove(self.cfg_path)
            else:
                self.load_config()

    def load_config(self):
        """
        Load config from file
        :return:
        """
        with open(self.cfg_path, "r") as file:
            self.__cfg_dict = json.load(file)

    def write_to_file(self):
        """
        Write config to file.
        :return:
        """
        with open(self.cfg_path, "w") as file:
            json.dump(self.cfg_dict, file)

    @property
    def cfg_dict(self):
        if (datetime.datetime.now() - self.__last_update).total_seconds() > self.update_timeout:
            self.write_to_file()
            self.__last_update = datetime.datetime.now()

        return self.__cfg_dict

    @cfg_dict.setter
    def cfg_dict(self, value):
        self.__cfg_dict = value
        if (datetime.datetime.now() - self.__last_update).total_seconds() > self.update_timeout:
            self.write_to_file()
            self.__last_update = datetime.datetime.now()

    @property
    def thumbnail_size_x(self):
        return self.__thumbnail_size_x

    @thumbnail_size_x.setter
    def thumbnail_size_x(self, value):
        if value < 0:
            raise ValueError("Thumbnail size must be positive")

        if value > 1000:
            warnings.warn("Thumbnail size is very large. Higher Accuracy will slow down the process and "
                          "increase storage usage.")
        self.__thumbnail_size_x = value
        self.__cfg_dict["thumbnail_size_x"] = value
        self.write_to_file()

    @property
    def thumbnail_size_y(self):
        return self.__thumbnail_size_y

    @thumbnail_size_y.setter
    def thumbnail_size_y(self, value):
        if value < 0:
            raise ValueError("Thumbnail size must be positive")

        if value > 1000:
            warnings.warn("Thumbnail size is very large. Higher Accuracy will slow down the process and "
                          "increase storage usage.")
        self.__thumbnail_size_y = value
        self.__cfg_dict["thumbnail_size_y"] = value
        self.write_to_file()

    @property
    def p_root_dir_a(self):
        return self.__p_root_dir_a

    @p_root_dir_a.setter
    def p_root_dir_a(self, value):
        if os.path.exists(value):
            self.__p_root_dir_a = value
            self.__thumb_dir_a = os.path.join(self.__p_root_dir_a, ".temp_thumbnails")
            self.__cfg_dict["p_root_dir_a"] = value
            self.write_to_file()

    @property
    def p_root_dir_b(self):
        return self.__p_root_dir_b

    @p_root_dir_b.setter
    def p_root_dir_b(self, value):
        if value is None:
            self.__p_root_dir_b = None
            self.__thumb_dir_b = None
            self.__has_dir_b = False
            self.__cfg_dict["p_root_dir_b"] = value
            self.write_to_file()

        elif os.path.exists(value):
            self.__p_root_dir_b = value
            self.__thumb_dir_b = os.path.join(self.__p_root_dir_b, ".temp_thumbnails")
            self.__has_dir_b = True
            self.__cfg_dict["p_root_dir_b"] = value
            self.write_to_file()
        else:
            raise ValueError("The root dir b is not None yet it doesn't exist")

    @property
    def thumb_dir_a(self):
        return self.__thumb_dir_a

    @property
    def thumb_dir_b(self):
        return self.__thumb_dir_b

    @property
    def has_dir_b(self):
        return self.__has_dir_b

    @property
    def similarity_threshold(self):
        return self.__similarity_threshold

    @similarity_threshold.setter
    def similarity_threshold(self, value):
        if type(value) is not float or value < 0:
            raise ValueError("similarity threshold needs to be float and greater than 0.")
        self.__similarity_threshold = value
        self.__cfg_dict["similarity_threshold"] = value
        self.write_to_file()

    @property
    def ignore_names(self):
        return self.__ignore_names

    @ignore_names.setter
    def ignore_names(self, value):
        self.__ignore_names = value
        self.__cfg_dict["ignore_names"] = value
        self.write_to_file()

    @property
    def ignore_paths(self):
        return self.__ignore_paths

    @ignore_paths.setter
    def ignore_paths(self, value):
        self.__ignore_paths = value
        self.__cfg_dict["ignore_paths"] = value
        self.write_to_file()

    @property
    def enough_images_to_compare(self):
        return self.__enough_images_to_compare

    @enough_images_to_compare.setter
    def enough_images_to_compare(self, value):
        self.__enough_images_to_compare = value
        self.__cfg_dict["enough_images_to_compare"] = value
        self.write_to_file()

    @property
    def sl_matching_hash(self):
        return self.__sl_matching_hash

    @sl_matching_hash.setter
    def sl_matching_hash(self, value):
        self.__sl_matching_hash = value
        self.__cfg_dict["sl_matching_hash"] = value
        self.write_to_file()

    @property
    def sl_has_thumb(self):
        return self.__sl_has_thumb

    @sl_has_thumb.setter
    def sl_has_thumb(self, value):
        self.__sl_has_thumb = value
        self.__cfg_dict["sl_has_thumb"] = value
        self.write_to_file()

    @property
    def sl_matching_aspect(self):
        return self.__sl_matching_aspect

    @sl_matching_aspect.setter
    def sl_matching_aspect(self, value):
        self.__sl_matching_aspect = value
        self.__cfg_dict["sl_matching_aspect"] = value
        self.write_to_file()

    @property
    def sl_make_diff_plots(self):
        return self.__sl_make_diff_plots

    @sl_make_diff_plots.setter
    def sl_make_diff_plots(self, value):
        self.sl_make_diff_plots = value
        self.__cfg_dict["sl_make_diff_plots"] = value
        self.write_to_file()

    @property
    def sl_plot_output_dir(self):
        return self.__sl_plot_output_dir

    @sl_plot_output_dir.setter
    def sl_plot_output_dir(self, value):
        self.__sl_plot_output_dir = value
        self.__cfg_dict["sl_plot_output_dir"] = value
        self.write_to_file()

    @property
    def supported_file_types(self):
        return self.__supported_file_types

    @supported_file_types.setter
    def supported_file_types(self, value):
        self.__supported_file_types = value
        self.__cfg_dict["supported_file_types"] = value
        self.write_to_file()

    @property
    def less_optimized(self):
        return self.__less_optimized

    @less_optimized.setter
    def less_optimized(self, value):
        self.__less_optimized = value
        self.__cfg_dict["less_optimized"] = value
        self.write_to_file()

    @property
    def retry_limit(self):
        return self.__retry_limit

    @retry_limit.setter
    def retry_limit(self, value):
        self.__retry_limit = value
        self.__cfg_dict["retry_limit"] = value
        self.write_to_file()

    @property
    def verbose(self):
        return self.__verbose

    @verbose.setter
    def verbose(self, value):
        self.__verbose = value
        self.__cfg_dict["verbose"] = value
        self.write_to_file()

