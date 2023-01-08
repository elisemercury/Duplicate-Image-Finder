import os
import sqlite3
import base64
import json
from typing import Any, Union, List
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

    # ------------------------------------------------------------------------------------------------------------------
    # CONFIG TABLE
    # ------------------------------------------------------------------------------------------------------------------

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

    def config_table_exists(self):
        """
        Check the master table if the config table exists. DOES NOT VERIFY THE TABLE DEFINITION!
        :return:
        """
        self.cur.execute("SELECT * FROM sqlite_master WHERE tbl_name IS 'config'")
        return self.cur.fetchone() is not None

    # ------------------------------------------------------------------------------------------------------------------
    # DIRECTORY TABLES
    # ------------------------------------------------------------------------------------------------------------------

    def create_directory_tables(self, secondary_folder: bool = False, purge: bool = True):
        """
        Create the directory tables. Default for purge is true, to recompute it in case the program is stopped during 
        indexing. ASSUMPTION: Indexing is a very fast operation. TODO Handle Stop mid Indexing.

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

        self.debug_execute(
            "CREATE TABLE directory_a ("
            "key INTEGER PRIMARY KEY AUTOINCREMENT, "
            "path TEXT , "
            "filename TEXT, "
            "error TEXT DEFAULT '<EMPTY>',"
            "proc_suc INTEGER DEFAULT -1 CHECK ( directory_a.proc_suc >= -1 AND directory_a.proc_suc <= 1 ) ,"
            "px INTEGER DEFAULT -1 CHECK (directory_a.px >= -1), "
            "py INTEGER DEFAULT -1 CHECK (directory_a.py >= -1))"
        )

        if secondary_folder:
            self.has_b = True
            self.debug_execute(
                "CREATE TABLE directory_b ("
                "key INTEGER PRIMARY KEY AUTOINCREMENT, "
                "path TEXT , "
                "filename TEXT, "
                "error TEXT DEFAULT '<EMPTY>',"
                "proc_suc INTEGER DEFAULT -1 CHECK ( directory_b.proc_suc >= -1 AND directory_b.proc_suc <= 1 ) ,"
                "px INTEGER DEFAULT -1 CHECK (directory_b.px >= -1), "
                "py INTEGER DEFAULT -1 CHECK (directory_b.py >= -1))"
            )

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
                "px": row[5],
                "py": row[6],
                "dir_a": dir_a
                }

    @staticmethod
    def wrap_many_dict_dir(rows: List[tuple], dir_a: bool = True):
        result = []
        for row in rows:
            result.append(Database.all_to_dict_dir(row, dir_a=dir_a))
        return result

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

    def update_dir_success(self, key: int, dir_a: bool = True, px: int = -1, py: int = -1):
        """
        Set the flag for success of the file with the matching key. Set it in either table_a or table_b.
        Error not updated.
        :param key: file identifier which is to be updated
        :param dir_a: TRUE <=> update directory_a, ELSE update directory_b
        :param px: x count of pixels
        :param py: y count of pixels
        :return:
        """
        tbl_name = "directory_a" if dir_a else "directory_b"
        self.debug_execute(f"UPDATE {tbl_name} SET proc_suc = 1, px = {px}, py = {py} WHERE key = {key}")

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

    def fetch_many_after_key(self, directory_a: bool = True, starting: int = None, count=100) -> List[dict]:
        """
        Fetch count number of rows from a table a or table b starting at a specific key (WHERE key > starting)

        :param directory_a: True use directory_a table else directory_b
        :param starting: select everything with key greater than that
        :param count: number of entries to return
        :return: List[dict] rows wrapped in dict
        """
        tbl_name = "directory_a" if directory_a else "directory_b"

        # start at the beginning
        if starting is None:
            self.debug_execute(f"SELECT * FROM {tbl_name} ORDER BY key ASC")
            return Database.wrap_many_dict_dir(rows=self.cur.fetchmany(count), dir_a=directory_a)

        # start from specific point
        self.debug_execute(f"SELECT * FROM {tbl_name} WHERE key > {starting} ORDER BY key ASC")
        return self.cur.fetchmany(count)

    # ------------------------------------------------------------------------------------------------------------------
    # THUMBNAIL FILENAME TABLE
    # ------------------------------------------------------------------------------------------------------------------

    def create_thumb_table(self, secondary_folder: bool = False, purge: bool = False):
        """
        Create tables which contain the names of the thumbnails ( to make sure there's no collisions ahead of time)

        :param secondary_folder: if True, create a table for the secondary folder as well.
        :param purge: if True, purge the tables before creating them.
        :return:
        """

        # Drop the tables if purge is set
        if purge:
            print("Purging preexisting indexes of directories.")

            if self.test_thumb_table_existence(True):
                print("Dropping directory A table.")
                self.drop_thumb(True)

            if self.test_thumb_table_existence(False):
                print("Dropping directory B table.")
                self.drop_thumb(False)

        self.debug_execute("CREATE TABLE thumb_a ( key INTEGER PRIMARY KEY, filename TEXT UNIQUE )")

        if secondary_folder:
            self.debug_execute("CREATE TABLE thumb_b ( key INTEGER PRIMARY KEY, filename TEXT UNIQUE )")

    def test_thumb_table_existence(self, dir_a: bool = True):
        """
        Check the table for thumbnails of directory X, exists. DOES NOT VERIFY THE TABLE DEFINITION!
        :param dir_a: True if dir_a, False if dir_b
        :return:
        """
        tbl_name = "thumb_a" if dir_a else "thumb_b"
        self.cur.execute(f"SELECT * FROM sqlite_master WHERE tbl_name IS '{tbl_name}'")
        return self.cur.fetchone() is not None

    def drop_thumb(self, dir_a: bool = True):
        """
        Drop a table related to the thumbnails of a directory.
        :param dir_a: if True, drop thumb A table, else drop thumb b table.
        :return:
        """
        tbl_name = "thumb_a" if dir_a else "thumb_b"
        self.debug_execute(f"DROP TABLE {tbl_name}")

    def get_thumb_name(self, key: int, dir_a: bool):
        """
        Get the thumbnail name associated with the key.
        :param key: key to search the thumbnail path for
        :param dir_a: if the key is to be searched in the directory_a or directory_b table.
        :return:
        """
        tbl_name = "thumb_a" if dir_a else "thumb_b"
        self.debug_execute(f"SELECT * FROM {tbl_name} WHERE key = {key}")
        return self.cur.fetchone()

    def generate_new_thumb_name(self, key: int, file_name: str, retry_limit: int = 1000, dir_a: bool = True):
        """
        Generate a new free name for a file. If a file name is taken, will retry a limited number of times again.

        :param key: key in the directory_X tables
        :param file_name: file name for which to generate the thumbnail name
        :param retry_limit: how many file names are to be tested.
        :param dir_a: if it is to be inserted into thumb_a or thumb_b table.
        :return:
        """
        index = 0
        tbl_name = "thumb_a" if dir_a else "thumb_b"
        free = False

        name, ext = os.path.splitext(file_name)
        thumb_name = f"{name}_thumb_{index:03}{ext}"

        while not free:
            if self.thumb_name_exists(thumb_name, dir_a):
                index += 1
                thumb_name = f"{name}_thumb_{index:03}{ext}"
            else:
                free = True

            if index > retry_limit:
                raise ValueError(f"Filename '{file_name}' is too common, it has been used {retry_limit} times.")

        self.debug_execute(f"INSERT INTO {tbl_name} (key, filename) VALUES ({key}, '{thumb_name}')")
        return thumb_name

    def thumb_name_exists(self, thumb_name: str, dir_a: bool = True):
        """
        Check if the name exists already, given the name and the directory the file is in.

        :param thumb_name: name to check
        :param dir_a: if it is to be searched in dir a or dir b
        :return:
        """
        tbl_name = "thumb_a" if dir_a else "thumb_b"
        self.debug_execute(f"SELECT * FROM {tbl_name} WHERE filename IS '{thumb_name}'")
        return self.cur.fetchone() is not None

    # ------------------------------------------------------------------------------------------------------------------
    # HASH TABLE
    # ------------------------------------------------------------------------------------------------------------------

    def create_hash_table(self, purge: bool = False) :
        """
        Create the config table and insert a config dictionary.
        :param purge: if True, purge the table before creating it.
        :return:
        """
        if purge:
            if self.test_hash_table_existence():
                self.drop_hash_table()

        self.debug_execute("CREATE TABLE hash_table ("
                           "key INTEGER PRIMARY KEY AUTOINCREMENT , "
                           "hash TEXT , "
                           "dir_a INTEGER CHECK ( hash_table.dir_a >= 0 AND hash_table.dir_a <= 1 ), "
                           "dir_key INTEGER ,"
                           "rotation INTEGER) ")

    def test_hash_table_existence(self):
        """
        Check if the hash table exists. DOES NOT VERIFY THE TABLE DEFINITION!
        :return:
        """
        self.cur.execute(f"SELECT * FROM sqlite_master WHERE tbl_name IS 'hash_table'")
        return self.cur.fetchone() is not None

    def drop_hash_table(self):
        """
        Drop the hash table.
        :return:
        """
        self.debug_execute(f"DROP TABLE hash_table")

    def insert_hash(self, fhash: str, dir_a: bool, dir_key: int, rotation: int):
        """
        Insert a hash into the hash table.
        :param fhash: hash to insert
        :param dir_a: if the file is in dir_a or dir_b
        :param dir_key: key of the file in the directory table
        :param rotation: rotation of the file
        :return:
        """
        dir_a_num = 1 if dir_a else 0
        self.debug_execute(f"INSERT INTO hash_table (hash, dir_a, dir_key, rotation) VALUES ('{fhash}', {dir_a_num},"
                           f" {dir_key}, {rotation})")

    def has_all_hashes(self, dir_a: bool, dir_key: int):
        """
        Check if a file has a hash.
        :param dir_a: if the file is in dir_a or dir_b
        :param dir_key: key of the file in the directory table
        :return: if a file has all 4 entries.
        """
        dir_a_num = 1 if dir_a else 0
        self.debug_execute(f"SELECT * FROM hash_table WHERE dir_a = {dir_a_num} AND dir_key = {dir_key}")
        return len(self.cur.fetchall()) == 4

    def has_any_hash(self, dir_a: bool, dir_key: int):
        """
        Check if a file has a hash.
        :param dir_a: if the file is in dir_a or dir_b
        :param dir_key: key of the file in the directory table
        :return: if a file has any entry.
        """
        dir_a_num = 1 if dir_a else 0
        self.debug_execute(f"SELECT * FROM hash_table WHERE dir_a = {dir_a_num} AND dir_key = {dir_key}")
        return self.cur.fetchone() is not None

    def del_all_hashes(self, dir_a: bool, dir_key: int):
        """
        Delete any of the 4 possible hashes of a given file.
        :param dir_a:
        :param dir_key:
        :return:
        """
        dir_a_num = 1 if dir_a else 0
        self.debug_execute(f"DELETE FROM hash_table WHERE dir_a = {dir_a_num} AND dir_key = {dir_key}")
        return self.cur.fetchone() is not None

    def update_hash(self, file_hash: str, dir_a: bool, dir_key: int, rotation: int):
        """
        Update a hash in the hash table. (Not sure why I'd need the function but there it is)
        :param file_hash: hash to update
        :param dir_a: if the file is in dir_a or dir_b
        :param dir_key: key of the file in the directory table
        :param rotation: rotation of the file
        :return:
        """
        dir_a_num = 1 if dir_a else 0
        self.debug_execute(f"UPDATE hash_table SET hash = '{file_hash}' "
                           f"WHERE dir_a = {dir_a_num} AND dir_key = {dir_key} AND rotation = {rotation}")

    # ------------------------------------------------------------------------------------------------------------------
    # ERROR TABLE
    # ------------------------------------------------------------------------------------------------------------------

    def create_dif_table(self, purge: bool = False):
        """
        Create the dif table. If purge is true, drop a preexisting dif table.

        :param purge: if True, purge the table before creating it.
        :return:
        """
        if purge:
            if self.test_dif_table_existence():
                self.drop_dif_table()

        self.debug_execute("CREATE TABLE dif_table ("
                           "key INTEGER PRIMARY KEY AUTOINCREMENT , "
                           "key_a INTEGER NOT NULL , "
                           "key_b INTEGER NOT NULL ,"
                           "dif REAL CHECK (dif_table.dif > 0) DEFAULT 100,"
                           "b_dir_b INTEGER CHECK (dif_table.b_dir_b >= 0 AND dif_table.b_dir_b <= 1) DEFAULT 0,"
                           "error TEXT,"
                           "success INT CHECK (dif_table.success >= 0 AND dif_table.success <= 1)) ")

    def test_dif_table_existence(self):
        """
        Check if the dif table exists. DOES NOT VERIFY THE TABLE DEFINITION!
        :return:
        """
        self.cur.execute(f"SELECT * FROM sqlite_master WHERE tbl_name IS 'dif_table'")
        return self.cur.fetchone() is not None

    def drop_dif_table(self):
        """
        Drop the dif table.
        :return:
        """
        self.debug_execute(f"DROP TABLE dif_table")

    def insert_dif_success(self, key_a: int, key_b: int, dif: float, b_dir_b: bool = False) -> bool:
        """
        Insert a new row into the database. If the value exists already, return False, else return True

        :param key_a: key of first image in directory_X table
        :param key_b: key of second image in directory_X table
        :param dif: difference between the images.
        :param b_dir_b: if the second image came from dir_b
        :return: bool if the insert was successful or the key pair existed already.
        """
        if self.get_by_pair(key_a=key_a, key_b=key_b) is not None:
            return False

        self.debug_execute(f"INSERT INTO dif_table (key_a, key_b, dif, b_dir_b, success) "
                           f"VALUES ({key_a}, {key_b}, {dif}, {1 if b_dir_b else 0, 1}, 1)")
        return True

    def insert_dif_error(self, key_a: int, key_b: int, error: str, b_dir_b: bool = False) -> bool:
        """
        Insert a new row into the database. If the value exists already, return False, else return True

        :param key_a: key of first image in directory_X table
        :param key_b: key of second image in directory_X table
        :param error: error that occurred during processing.
        :param b_dir_b: if the second image came from dir_b
        :return: bool if the insert was successful or the key pair existed already.
        """
        if self.get_by_pair(key_a=key_a, key_b=key_b) is not None:
            return False

        self.debug_execute(f"INSERT INTO dif_table (key_a, key_b, b_dir_b, success, error) "
                           f"VALUES ({key_a}, {key_b}, {1 if b_dir_b else 0, 1}, 0, '{error}')")
        return True

    def get_by_pair(self, key_a: int, key_b: int):
        """
        Get the row matching the pair of keys. Return the row wrapped in a dict or None if it doesn't exist.

        :param key_a: key of first image in directory_X table
        :param key_b: key of second image in directory_X table
        :return: None, nothing exists, dict of matching row
        """
        self.debug_execute(f"SELECT * FROM dif_table WHERE key_a = {key_a} AND key_b = {key_b}")
        res = self.cur.fetchone()

        if res is None:
            return None

        return self.all_to_dict_dif(res)

    @staticmethod
    def all_to_dict_dif(row: tuple):
        return {
            "key": row[0],
            "key_a": row[1],
            "key_b": row[2],
            "dif": row[3],
            "b_dir_b": row[4],
            "error": row[5],
            "success": row[6]
        }

    def get_by_table_key(self, key: int):
        """
        Get a row by the table key. Return the row wrapped in a dict tor None if it doesn't exist.

        :param key: unique key in the dif table.
        :return: None, nothing exists, dict of matching row.
        """
        self.debug_execute(f"SELECT * FROM dif_table WHERE key = {key}")
        res = self.cur.fetchone()

        if res is None:
            return None

        return self.all_to_dict_dif(res)

    def update_pair_row(self, key_a: int, key_b: int, dif: float = None, b_dir_b: bool = None) -> bool:
        """
        Updates a pair with the new data. if the data is not specified, the preexisting data is used.
        Return true if the update was successful. Return False if the row didn't exist.

        :param key_a: key of first image in directory_X table
        :param key_b: key of second image in directory_X table
        :param dif: difference measurement
        :param b_dir_b: if the second image is from dir b or not.
        :return: if update was successful
        """

        if b_dir_b is None and dif is None:
            print("WARNING: Update function called without anything to oupdate.")
            return True

        # get the previous row.
        prev_row = self.get_by_pair(key_a=key_a, key_b=key_b)

        if prev_row is None:
            return False

        if b_dir_b is None:
            b_dir_b = prev_row["b_dir_b"]

        if dif is None:
            dif = prev_row["dif"]

        self.debug_execute(f"UPDATE dif_table SET b_dir_b = {b_dir_b}, dif = {dif} WHERE key_a = {key_a} AND "
                           f"key_b = {key_b}")

        return True

    # ------------------------------------------------------------------------------------------------------------------
    # COMMON FUNCTIONS
    # ------------------------------------------------------------------------------------------------------------------

    def debug_execute(self, statement: str, commit_now: bool = False):
        """
        Wrapper to print the infringing statement in case of an error.

        :param statement: statement to execute
        :param commit_now: If after execution a commit should be executed.
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

        :param b64_string: a b64 encoded python object
        :return: a python object
        """
        bytes_string = base64.standard_b64decode(b64_string)
        json_string = bytes_string.decode("utf-8")
        return json.loads(json_string)
