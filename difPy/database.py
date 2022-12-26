import sqlite3
import base64
import json
from typing import Any, Union

"""
Default implementation of the Database.
If the tool is to be used in a different context, a custom implementation of the database class may be provided 
to interface with another database. 
"""


class Database:
    path: str = None
    con: sqlite3.Connection = None
    cur: sqlite3.Cursor = None

    def __init__(self, path):
        self.connect(path)

    def create_config(self, config: dict, type_name: str) -> bool:
        """
        Create the config table and insert a config dictionary.
        :param config: config dict
        :param type_name: name under which config is stored
        :return: bool -> insert successfull or not (key already exists)
        """
        if not self.test_config_table_existence():
            self.debug_execute("CREATE TABLE config (key INTEGER PRIMARY KEY AUTOINCREMENT, "
                               "name TEXT UNIQUE , value TEXT)")

        config_string = self.to_b64(config)

        self.debug_execute(f"SELECT * FROM config WHERE name IS '{type_name}'")

        if self.cur.fetchone() is None:
            return False

        self.debug_execute(f"INSERT INTO config (name, value) VALUES ('{type_name}', '{config_string}')")
        self.con.commit()
        return True

    def get_config(self, type_name: str) -> Union[dict, None]:
        """
        Get the config dictionary from the database.
        :param type_name: name under which config is stored
        :return: config dict or None if not found
        """
        self.debug_execute(f"SELECT value FROM config WHERE name IS '{type_name}'")

        value = self.cur.fetchone()[0]
        if value is None:
            return None

        return self.from_b64(value)

    def delete_config(self, type_name: str):
        """
        Delete the config from the database.
        :param type_name: name under which config is stored
        :return:
        """
        self.debug_execute(f"DELETE FROM config WHERE name IS '{type_name}'")
        self.con.commit()

    def update_config(self, config: dict, type_name: str):
        """
        Update the config to the database.
        :param config: config dict
        :param type_name: name under which config is stored
        :return:
        """
        config_string = self.to_b64(config)
        self.debug_execute(f"UPDATE config SET value = '{config_string}' WHERE name IS '{type_name}'")
        self.con.commit()

    def debug_execute(self, statement: str):
        """
        Wrapper to print the infringing statement in case of an error.
        :param statement: statement to execute
        :return:
        """
        try:
            self.cur.execute(statement)
        except Exception as e:
            print(f"Exception {e} with statement:\n{statement}")
            raise e

    def connect(self, path):
        """
        Create Connection to Database.
        :param path: path to database
        :return:
        """
        self.con = sqlite3.connect(path)
        self.cur = self.con.cursor()

    @staticmethod
    def to_b64(to_encode: Any):
        """
        Convert an object to a b64 string

        :param to_encode: object to encode
        :return: base64 string
        """
        json_str = json.dumps(to_encode)
        bytes_string = json_str.encode("utf-8")
        return base64.standard_b64encode(bytes_string)

    @staticmethod
    def from_b64(b64_string: str):
        """
        Convert a b64 string to a python object

        :param b64_string: b64 encoded python object
        :return: python object
        """
        bytes_string = base64.standard_b64decode(b64_string)
        json_string = bytes_string.decode("utf-8")
        return json.loads(json_string)

    def test_config_table_existence(self):
        """
        Check the master table if the config table exists. DOES NOT VERIFY THE TABLE DEFINITION!
        :return:
        """
        self.cur.execute("SELECT * FROM sqlite_master WHERE tbl_name IS 'config'")
        return self.cur.fetchone() is None
