import os
import sqlite3
import base64
import json
from typing import Any, Union
import datetime

"""
Default implementation of the Database.
If the tool is to be used in a different context, a custom implementation of the database class may be provided 
to interface with another database. 
"""


class Database:
    path: str = None
    con: sqlite3.Connection = None
    cur: sqlite3.Cursor = None

    a_done: bool
    b_done: bool
    has_b: Union[bool, None]

    last_update: datetime.datetime = None

    def __init__(self, path):
        self.connect(path)
        self.a_done = False
        self.b_done = False
        self.has_b = None

    def create_config(self, config: dict, type_name: str) -> bool:
        """
        Create the config table and insert a config dictionary.
        :param config: config dict
        :param type_name: name under which config is stored
        :return: bool -> insert successful or not (key already exists)
        """
        if not self.config_table_exists():
            self.debug_execute("CREATE TABLE config (key INTEGER PRIMARY KEY AUTOINCREMENT, "
                               "name TEXT UNIQUE , value TEXT)")

        config_string = self.to_b64(config)

        self.debug_execute(f"SELECT * FROM config WHERE name IS '{type_name}'")

        if self.cur.fetchone() is None:
            return False

        self.debug_execute(f"INSERT INTO config (name, value) VALUES ('{type_name}', '{config_string}')")
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

    def update_config(self, config: dict, type_name: str):
        """
        Update the config to the database.
        :param config: config dict
        :param type_name: name under which config is stored
        :return:
        """
        config_string = self.to_b64(config)
        self.debug_execute(f"UPDATE config SET value = '{config_string}' WHERE name IS '{type_name}'")

    def debug_execute(self, statement: str, commit_now: bool = False):
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

        # automatically commit.
        if (datetime.datetime.now() - self.last_update).total_seconds() > 60 or commit_now or self.last_update is None:
            self.con.commit()
            self.last_update = datetime.datetime.now()

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

    def config_table_exists(self):
        """
        Check the master table if the config table exists. DOES NOT VERIFY THE TABLE DEFINITION!
        :return:
        """
        self.cur.execute("SELECT * FROM sqlite_master WHERE tbl_name IS 'config'")
        return self.cur.fetchone() is not None

    def create_directory_tables(self, secondary_folder: bool = False, purge: bool = True):
        """
        Create the directory tables. Default for purge is true, to recompute it in case the program is stopped during 
        indexing. ASSUMPTION: Indexing is a very fast operation. TODO Handle Stop mit Indexing.

        :param secondary_folder: if True, create a table for the secondary folder as well.
        :param purge: if True, purge the tables before creating them.
        :return:
        """

        # Drop the tables if purge is set
        if purge:
            print("Purging preexisting indexes of directories.")

            if self.test_dir_table_existence(True):
                print("Dropping directory A table.")
                self.drop_dir(True)

            if self.test_dir_table_existence(False):
                print("Dropping directory B table.")
                self.drop_dir(False)

        self.debug_execute("CREATE TABLE directory_a (key INTEGER PRIMARY KEY AUTOINCREMENT, "
                           "path TEXT , "
                           "filename TEXT, "
                           "error TEXT DEFAULT '<EMPTY>',"
                           "proc_suc INTEGER DEFAULT -1 CHECK "
                           "( directory_a.proc_suc >= -1 AND directory_a.proc_suc <= 1 ))")

        if secondary_folder:
            self.has_b = True
            self.debug_execute("CREATE TABLE directory_b (key INTEGER PRIMARY KEY AUTOINCREMENT, "
                               "path TEXT , "
                               "filename TEXT ,"
                               "error TEXT DEFAULT '<EMPTY>',"
                               "proc_suc INTEGER DEFAULT -1 CHECK "
                               "( directory_b.proc_suc >= -1 AND directory_b.proc_suc <= 1 ))")

    @staticmethod
    def all_to_dict_dir(row: Union[tuple, None], dir_a: bool = True):
        """
        Takes the result of a 'SELECT *' from a directory table and turns the tuple into a dict
        :param row: tuple to turn into dict
        :param dir_a: if the file was in directory a or directory b
        :return:
        """
        if row is None:
            return None

        return {"key": row[0],
                "path": row[1],
                "filename": row[2],
                "error": row[3],
                "proc_suc": row[4],
                "dir_a": dir_a
                }

    def test_dir_table_existence(self, dir_a: bool = True):
        """
        Check the table for directory X, exists. DOES NOT VERIFY THE TABLE DEFINITION!
        :param dir_a: True if dir_a, False if dir_b
        :return:
        """
        tbl_name = "directory_a" if dir_a else "directory_b"
        self.cur.execute(f"SELECT * FROM sqlite_master WHERE tbl_name IS '{tbl_name}'")
        return self.cur.fetchone() is not None

    def drop_dir(self, dir_a: bool = True):
        """
        Drop a table related to the directories.
        :param dir_a: if True, drop dir A table, else drop dir b table.
        :return:
        """
        tbl_name = "directory_a" if dir_a else "directory_b"
        self.debug_execute(f"DROP TABLE {tbl_name}")

    def add_file(self, path: str, filename: str, dir_a: bool = True):
        """
        Add a file to the database.
        :param path: path to file, including filename (e.g. /home/user/file.txt)
        :param filename: filename (e.g. file.txt) // For faster searching
        :param dir_a: if True, add to dir_a, else add to dir_b
        :return:
        """

        tbl_name = "directory_a" if dir_a else "directory_b"
        self.debug_execute(f"INSERT INTO {tbl_name} (path, filename) VALUES ('{path}', '{filename}')")

    def get_dir_count(self, dir_a: bool = True):
        """
        Get the number of files in the directory.
        :param dir_a: if True, get count of dir_a, else get count of dir_b
        :return:
        """
        tbl_name = "directory_a" if dir_a else "directory_b"
        self.debug_execute(f"SELECT COUNT(key) FROM {tbl_name}")
        return self.cur.fetchone()[0]

    def update_dir_success(self, key: int, dir_a: bool = True):
        """
        Set the flag for success of the file with the matching key. Set it in either table_a or table_b.
        Error not updated.
        :param key: file identifier which is to be updated
        :param dir_a: TRUE <=> update directory_a, ELSE update directory_b
        :return:
        """
        tbl_name = "directory_a" if dir_a else "directory_b"
        self.debug_execute(f"UPDATE {tbl_name} SET proc_suc = 1 WHERE key = {key}")

    def update_dir_error(self, key: int, msg: str, dir_a: bool = True):
        """
        Set the flag for error of the file with the matching key. Set it in either table_a or table_b
        Error is stored in plane text atm (It might be necessary to store it in b64.
        :param key: file identifier which is to be updated
        :param dir_a: TRUE <=> update directory_a, ELSE update directory_b
        :param msg: error message created when attempting to process the file.
        """
        tbl_name = "directory_a" if dir_a else "directory_b"
        self.debug_execute(f"UPDATE {tbl_name} SET proc_suc = 0, error='{msg}' WHERE key = {key}")

    def get_next_to_process(self):
        """
        Get an unprocessed entry from (one) of the directory table (s). Returns None per default to signify that
        there's nothing to be computed.
        :return: Next one to compute or None
        """
        if not self.a_done:
            self.debug_execute("SELECT * FROM directory_a WHERE proc_suc = -1")
            res = self.cur.fetchone()

            if res is None:
                self.a_done = True

            return self.all_to_dict_dir(res, dir_a=True)

        # if the has_b attribute is not computed, set it here.
        if self.has_b is None:
            self.has_b = self.test_dir_table_existence(dir_a=False)

            # Only needs to be eval. here since if it doesn't exist, we don't need to query the db. if it exists,
            # there's no need to recheck the has condition every time.
            if not self.has_b:
                self.b_done = True
                return None

        # query b table
        if not self.b_done:
            self.debug_execute("SELECT * FROM directory_b WHERE proc_suc = -1")
            res = self.cur.fetchone()

            if res is None:
                self.b_done = True

            return self.all_to_dict_dir(res, dir_a=False)

        # return None is the fall through and the default
        return None

