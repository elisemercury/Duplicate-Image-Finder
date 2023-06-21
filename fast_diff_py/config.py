import json
import os
import datetime


class FastDiffPyConfig:
    cfg_path: str
    update_timeout: int = 30
    __cfg_dict: dict
    __last_update: datetime.datetime
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

