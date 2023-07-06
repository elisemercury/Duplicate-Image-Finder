import json
import os
import datetime
import warnings
from typing import Union, List


def test_existing_config() -> bool:
    """
    Tests the default config path if it exists.
    :return: True if there's a config.
    """
    return os.path.exists(os.path.join(os.path.dirname(__file__), "task.json"))


class FastDiffPyConfig:
    cfg_path: str
    update_timeout: int = 30
    retain_config: bool = False

    __task_dict: dict
    __last_update: datetime.datetime = datetime.datetime.now()

    # ------------------------------------------------------------------------------------------------------------------
    # Class Config Storage
    # ------------------------------------------------------------------------------------------------------------------

    def __init__(self, task_path: str = None, task_purge: bool = False, cfg: dict = None):
        """
        Create config object

        :param task_path: path to where config is stored.
        :param task_purge: If a config exists at the specified path, the config will be removed if it exists
        :param cfg: an initial state of the config - used for config created in child processes.
        """
        # set the config_path
        if task_path is None:
            self.cfg_path = os.path.join(os.path.dirname(__file__), "task.json")

        self._task_dict = {
            "thumbnail_size_x": 64,
            "thumbnail_size_y": 64,
            "p_root_dir_a": None,
            "p_root_dir_b": None,
            "similarity_threshold": 200.0,
            "ignore_names": [],
            "ignore_paths": [],
            "enough_images_to_compare": [],
            "max_queue_size": 200,
            "first_loop":{
                "compute_thumbnails": True,
                "compute_hash": False,
                "shift_amount": 4,
                "cpu_proc": None,
                "inserted_counter": 0,
                "use_workers": True,
            },
            "second_loop": {
                "matching_hash": False,
                "has_thumb": False,
                "matching_aspect": False,
                "make_diff_plots": False,
                "plot_output_dir": None,
                "cpu_proc": None,
                "gpu_proc": 0,
                "queue_status": None ,
                "loop_base_a": True ,
                "use_workers": True,
                "use_special_b_algo": True
            },
            "database":{
                "type": "sqlite",
                "path": ""
            },
            "supported_file_types" : [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".gif", ".webp"],
            "less_optimized": False,
            "retry_limit": 1000,
            "verbose": False,
            "state": None,
            "retain_db": True,
        }

        if os.path.exists(self.cfg_path):
            if task_purge:
                os.remove(self.cfg_path)
            else:
                if cfg is not None:
                    self.__task_dict = cfg
                else:
                    self.load_config()

    def load_config(self):
        """
        Load config from file
        :return:
        """
        with open(self.cfg_path, "r") as file:
            self.__task_dict = json.load(file)

    def write_to_file(self):
        """
        Write config to file.
        :return:
        """
        with open(self.cfg_path, "w") as file:
            json.dump(self.__task_dict, file)

    @property
    def _task_dict(self):
        if (datetime.datetime.now() - self.__last_update).total_seconds() > self.update_timeout and self.retain_config:
            self.write_to_file()
            self.__last_update = datetime.datetime.now()

        return self.__task_dict

    @_task_dict.setter
    def _task_dict(self, value):
        self.__task_dict = value
        if (datetime.datetime.now() - self.__last_update).total_seconds() > self.update_timeout and self.retain_config:
            self.write_to_file()
            self.__last_update = datetime.datetime.now()

    def export_task_dict(self):
        """
        Function used to extract config for child processes.
        :return:
        """
        return self.__task_dict

    @property
    def thumbnail_size_x(self) -> int:
        return self._task_dict["thumbnail_size_x"]

    @thumbnail_size_x.setter
    def thumbnail_size_x(self, value: int):
        if value < 0:
            raise ValueError("Thumbnail size must be positive")

        if value > 1000:
            warnings.warn("Thumbnail size is very large. Higher Accuracy will slow down the process and "
                          "increase storage usage.")
        self._task_dict["thumbnail_size_x"] = value

    @property
    def thumbnail_size_y(self) -> int:
        return self._task_dict["thumbnail_size_y"]

    @thumbnail_size_y.setter
    def thumbnail_size_y(self, value: int):
        if value < 0:
            raise ValueError("Thumbnail size must be positive")

        if value > 1000:
            warnings.warn("Thumbnail size is very large. Higher Accuracy will slow down the process and "
                          "increase storage usage.")
        self._task_dict["thumbnail_size_y"] = value

    @property
    def p_root_dir_a(self) -> str:
        return self._task_dict["p_root_dir_a"]

    @p_root_dir_a.setter
    def p_root_dir_a(self, value: str):
        if os.path.exists(value):
            self._task_dict["p_root_dir_a"] = value
        else:
            raise FileNotFoundError("Directory A not found.")

    @property
    def p_root_dir_b(self) -> str:
        return self._task_dict["p_root_dir_b"]

    @p_root_dir_b.setter
    def p_root_dir_b(self, value: str):
        if value is None:
            self._task_dict["p_root_dir_b"] = value

        elif os.path.exists(value):
            self._task_dict["p_root_dir_b"] = value
        else:
            raise FileNotFoundError("The root dir b is not None yet it doesn't exist")

    @property
    def thumb_dir_a(self) -> str:
        return os.path.join(self._task_dict["p_root_dir_a"], ".temp_thumbnails")

    @property
    def thumb_dir_b(self) -> str:
        return os.path.join(self._task_dict["p_root_dir_b"], ".temp_thumbnails")

    @property
    def has_dir_b(self) -> bool:
        return self._task_dict["p_root_dir_b"] is not None

    @property
    def similarity_threshold(self) -> float:
        return self._task_dict["similarity_threshold"]

    @similarity_threshold.setter
    def similarity_threshold(self, value: float):
        if type(value) is not float or value < 0:
            raise ValueError("similarity threshold needs to be float and greater than 0.")
        self._task_dict["similarity_threshold"] = value

    @property
    def ignore_names(self) -> List[str]:
        return self._task_dict["ignore_names"]

    @ignore_names.setter
    def ignore_names(self, value: List[str]):
        self._task_dict["ignore_names"] = value

    @property
    def ignore_paths(self) -> List[str]:
        return self._task_dict["ignore_paths"]

    @ignore_paths.setter
    def ignore_paths(self, value: List[str]):
        self._task_dict["ignore_paths"] = value

    @property
    def enough_images_to_compare(self) -> bool:
        return self._task_dict["enough_images_to_compare"]

    @enough_images_to_compare.setter
    def enough_images_to_compare(self, value: bool):
        self._task_dict["enough_images_to_compare"] = value

    @property
    def sl_matching_hash(self) -> bool:
        return self._task_dict["second_loop"]["matching_hash"]

    @sl_matching_hash.setter
    def sl_matching_hash(self, value: bool):
        self._task_dict["second_loop"]["matching_hash"] = value

    @property
    def sl_has_thumb(self) -> bool:
        return self._task_dict["second_loop"]["has_thumb"]

    @sl_has_thumb.setter
    def sl_has_thumb(self, value: bool):
        self._task_dict["second_loop"]["has_thumb"] = value

    @property
    def sl_matching_aspect(self) -> bool:
        return self._task_dict["second_loop"]["matching_aspect"]

    @sl_matching_aspect.setter
    def sl_matching_aspect(self, value: bool):
        self._task_dict["second_loop"]["matching_aspect"] = value

    @property
    def sl_make_diff_plots(self) -> bool:
        return self._task_dict["second_loop"]["make_diff_plots"]

    @sl_make_diff_plots.setter
    def sl_make_diff_plots(self, value: bool):
        self._task_dict["second_loop"]["make_diff_plots"] = value

    @property
    def sl_plot_output_dir(self) -> str:
        return self._task_dict["second_loop"]["plot_output_dir"]

    @sl_plot_output_dir.setter
    def sl_plot_output_dir(self, value: str):
        self._task_dict["second_loop"]["plot_output_dir"] = value

    @property
    def sl_gpu_proc(self) -> int:
        return self._task_dict["second_loop"]["gpu_proc"]

    @sl_gpu_proc.setter
    def sl_gpu_proc(self, value: int):
        self._task_dict["second_loop"]["gpu_proc"] = value

    @property
    def sl_cpu_proc(self) -> Union[int, None]:
        return self._task_dict["second_loop"]["cpu_proc"]

    @sl_cpu_proc.setter
    def sl_cpu_proc(self, value: Union[int, None]):
        self._task_dict["second_loop"]["cpu_proc"] = value

    @property
    def sl_queue_status(self) -> Union[List[dict], dict, None]:
        return self._task_dict["second_loop"]["queue_status"]

    @sl_queue_status.setter
    def sl_queue_status(self, value: Union[List[dict], dict, None]):
        self._task_dict["second_loop"]["queue_status"] = value

    @property
    def sl_base_a(self) -> bool:
        return self._task_dict["second_loop"]["loop_base_a"]

    @sl_base_a.setter
    def sl_base_a(self, value: bool):
        self._task_dict["second_loop"]["loop_base_a"] = value

    @property
    def sl_use_workers(self) -> bool:
        return self._task_dict["second_loop"]["use_workers"]

    @sl_use_workers.setter
    def sl_use_workers(self, value: bool):
        self._task_dict["second_loop"]["use_workers"] = value

    @property
    def sl_use_special_b_algo(self) -> bool:
        return self._task_dict["second_loop"]["use_special_b_algo"]

    @sl_use_special_b_algo.setter
    def sl_use_special_b_algo(self, value: bool):
        self._task_dict["second_loop"]["use_special_b_algo"] = value

    @property
    def supported_file_types(self) -> List[str]:
        return self._task_dict["supported_file_types"]

    @supported_file_types.setter
    def supported_file_types(self, value: List[str]):
        self._task_dict["supported_file_types"] = value

    @property
    def less_optimized(self) -> bool:
        return self._task_dict["less_optimized"]

    @less_optimized.setter
    def less_optimized(self, value: bool):
        self._task_dict["less_optimized"] = value

    @property
    def retry_limit(self) -> int:
        return self._task_dict["retry_limit"]

    @retry_limit.setter
    def retry_limit(self, value: int):
        self._task_dict["retry_limit"] = value

    @property
    def verbose(self) -> bool:
        return self._task_dict["verbose"]

    @verbose.setter
    def verbose(self, value: bool):
        self._task_dict["verbose"] = value

    @property
    def state(self) -> str:
        return self._task_dict["state"]

    @state.setter
    def state(self, value: str):
        self._task_dict["state"] = value

    @property
    def fl_compute_thumbnails(self) -> bool:
        return self._task_dict["first_loop"]["compute_thumbnails"]

    @fl_compute_thumbnails.setter
    def fl_compute_thumbnails(self, value: bool):
        self._task_dict["first_loop"]["compute_thumbnails"] = value

    @property
    def fl_compute_hash(self) -> bool:
        return self._task_dict["first_loop"]["compute_hash"]

    @fl_compute_hash.setter
    def fl_compute_hash(self, value: bool):
        self._task_dict["first_loop"]["compute_hash"] = value

    @property
    def fl_shift_amount(self) -> int:
        return self._task_dict["first_loop"]["shift_amount"]

    @fl_shift_amount.setter
    def fl_shift_amount(self, value: int):
        self._task_dict["first_loop"]["shift_amount"] = value

    @property
    def fl_cpu_proc(self) -> int:
        return self._task_dict["first_loop"]["cpu_proc"]

    @fl_cpu_proc.setter
    def fl_cpu_proc(self, value: int):
        self._task_dict["first_loop"]["cpu_proc"] = value

    @property
    def fl_inserted_counter(self) -> int:
        return self._task_dict["first_loop"]["inserted_counter"]

    @fl_inserted_counter.setter
    def fl_inserted_counter(self, value: int):
        self._task_dict["first_loop"]["inserted_counter"] = value

    @property
    def fl_use_workers(self) -> bool:
        return self._task_dict["first_loop"]["use_workers"]

    @fl_use_workers.setter
    def fl_use_workers(self, value: bool):
        self._task_dict["first_loop"]["use_workers"] = value

    @property
    def database(self) -> dict:
        return self._task_dict["database"]

    @database.setter
    def database(self, value: dict):
        self._task_dict["database"] = value

    @property
    def retain_db(self) -> bool:
        return self._task_dict["retain_db"]

    @retain_db.setter
    def retain_db(self, value: bool):
        self._task_dict["retain_db"] = value

    @property
    def max_queue_size(self) -> int:
        return self._task_dict["max_queue_size"]

    @max_queue_size.setter
    def max_queue_size(self, value: int):
        self._task_dict["max_queue_size"] = value