import logging
import os
import sqlite3
import base64
import json
from typing import Any, Union, List
import datetime
from fast_diff_py.database import Database


"""
Default implementation of the Database.
If the tool is to be used in a different context, a custom implementation of the database class may be provided 
to interface with another database. 
"""


class SQLiteDatabase(Database):
    path: str = None
    con: sqlite3.Connection = None
    cur: sqlite3.Cursor = None
    path: str

    last_update: datetime.datetime = datetime.datetime.now()
    logger: logging.Logger = None

    def __init__(self, path):
        super().__init__()
        self.connect(path)
        self.path = path
        self.prepare_logging()

    # ------------------------------------------------------------------------------------------------------------------
    # DIRECTORY TABLES
    # ------------------------------------------------------------------------------------------------------------------

    def create_directory_tables(self, purge: bool = True):
        """
        Create the directory tables. Default for purge is true, to recompute it in case the program is stopped during
        indexing. ASSUMPTION: Indexing is a very fast operation. TODO Handle Stop mid Indexing.

        :param purge: if True, purge the tables before creating them.
        :return:
        """

        # Drop the tables if purge is set
        if purge:
            self.logger.info("Purging preexisting indexes of directories.")

            if self.test_dir_table_existence():
                self.logger.info("Dropping directory table.")
                self.drop_dir()

        self.debug_execute(
            "CREATE TABLE directory ("
            "key INTEGER PRIMARY KEY AUTOINCREMENT, "
            "path TEXT , "
            "filename TEXT, "
            "error TEXT,"
            "proc_suc INTEGER DEFAULT -1 CHECK ( directory.proc_suc >= -2 AND directory.proc_suc <= 1 ) ,"
            "px INTEGER DEFAULT -1 CHECK (directory.px >= -1), "
            "py INTEGER DEFAULT -1 CHECK (directory.py >= -1),"
            "dir_b INTEGER DEFAULT 0 CHECK (directory.dir_b >= 0 AND directory.dir_b <= 1),"
            "hash_0 INTEGER, "
            "hash_90 INTEGER ,"
            "hash_180 INTEGER , "
            "hash_270 INTEGER ,  "
            "UNIQUE (path, dir_b))"
        )

    @staticmethod
    def all_to_dict_dir(row: Union[tuple, None]):
        """
        Takes the result of a 'SELECT *' from a directory table and turns the tuple into a dict

        :param row: tuple to turn into dict
        :return:
        """
        if row is None:
            return None

        return {"key": row[0],
                "path": row[1],
                "filename": row[2],
                "error": SQLiteDatabase.from_b64(row[3]) if row[3] is not None else None,
                "proc_suc": row[4],
                "px": row[5],
                "py": row[6],
                "dir_a": row[7] == 0,
                "hash_0": row[8],
                "hash_90": row[9],
                "hash_180": row[10],
                "hash_270": row[11],
                }

    @staticmethod
    def wrap_many_dict_dir(rows: List[tuple]):
        """
        Wraps a list of rows in dictionaries.

        :param rows: rows to wrap
        :return:
        """
        result = []
        for row in rows:
            result.append(SQLiteDatabase.all_to_dict_dir(row))
        return result

    def test_dir_table_existence(self):
        """
        Check the table for directory X, exists. DOES NOT VERIFY THE TABLE DEFINITION!

        :return:
        """
        self.cur.execute(f"SELECT * FROM sqlite_master WHERE tbl_name IS 'directory'")
        return self.cur.fetchone() is not None

    def drop_dir(self):
        """
        Drop a table related to the directories.

        :return:
        """
        self.debug_execute(f"DROP TABLE directory")

    def add_file(self, path: str, filename: str, dir_a: bool = True):
        """
        Add a file to the database.

        :param path: path to file, including filename (e.g. /home/user/file.txt)
        :param filename: filename (e.g. file.txt) // For faster searching
        :param dir_a: if True, add to dir_a, else add to dir_b
        :return:
        """

        self.debug_execute(f"INSERT INTO directory (path, filename, dir_b) "
                           f"VALUES ('{path}', '{filename}', {0 if dir_a else 1})")

    def get_dir_count(self, dir_a: Union[bool, None] = None):
        """
        Get the number of files in the directory table.

        :param dir_a: True, count of dir_a, False, count of dir_b, None count of both.
        :return:
        """
        if dir_a is None:
            self.debug_execute(f"SELECT COUNT(key) FROM directory")
            return self.cur.fetchone()[0]

        self.debug_execute(f"SELECT COUNT(key) FROM directory WHERE dir_b = {0 if dir_a else 1}")
        return self.cur.fetchone()[0]

    def update_dir_success(self, key: int, px: int = -1, py: int = -1):
        """
        Set the flag for success of the file with the matching key. Set it in either table_a or table_b.
        Error not updated.

        :param key: file identifier which is to be updated
        :param px: x count of pixels
        :param py: y count of pixels
        :return:
        """
        self.debug_execute(f"UPDATE directory SET proc_suc = 1, px = {px}, py = {py} WHERE key = {key}")

    def update_dir_error(self, key: int, msg: str):
        """
        Set the flag for error of the file with the matching key. Set it in either table_a or table_b
        Error is stored in plane text atm (It might be necessary to store it in b64.

        :param key: file identifier which is to be updated
        :param msg: error message created when attempting to process the file.
        """
        msg_b64 = SQLiteDatabase.to_b64(msg)
        self.debug_execute(f"UPDATE directory SET proc_suc = 0, error='{msg_b64}' WHERE key = {key}")

    def get_next_to_process(self):
        """
        Get an unprocessed entry from the directory table. Returns None per default to signify that there's nothing to
        be computed.

        :return: Next one to compute or None
        """
        self.debug_execute("SELECT * FROM directory WHERE proc_suc = -1")
        return self.all_to_dict_dir(self.cur.fetchone())

    def mark_processing(self, task: dict):
        """
        Precondition, the entry already exists, so it can be updated

        :param task: dictionary generated by the get_next_to_process
        :return:
        """
        self.debug_execute(f"UPDATE directory SET proc_suc = -2 WHERE key = {task['key']}")

    def reset_first_loop_mark(self):
        """
        Reset the mark from mark_processing on all files that are currently in processing. Intended for resume of
        processing.
        :return:
        """
        self.debug_execute("UPDATE directory SET proc_suc = -1 WHERE directory.proc_suc = -2")

    def fetch_many_after_key(self, directory_a: bool = True, starting: int = None, count=100) -> List[dict]:
        """
        Fetch count number of rows from a table a or table b starting at a specific key (WHERE key > starting)

        :param directory_a: True use directory_a table else directory_b
        :param starting: select everything with key greater than that
        :param count: number of entries to return
        :return: List[dict] rows wrapped in dict
        """
        dir_b = 0 if directory_a else 1
        # start at the beginning
        if starting is None:
            self.debug_execute(f"SELECT * FROM directory WHERE dir_b = {dir_b} ORDER BY key ASC")
            return self.wrap_many_dict_dir(rows=self.cur.fetchmany(count))

        # start from specific point
        self.debug_execute(f"SELECT * FROM directory WHERE key > {starting} AND dir_b = {dir_b} ORDER BY key ASC")
        return self.wrap_many_dict_dir(rows=self.cur.fetchmany(count))

    def fetch_row_of_key(self, key: int):
        """
        Fetch exactly the row matching the key and directory.

        :param key: the key of the row
        :return:
        """
        self.debug_execute(f"SELECT * FROM directory WHERE key = {key}")
        return self.all_to_dict_dir(self.cur.fetchone())

    def insert_hash(self, file_hash: str, key: int, rotation: int):
        """
        Insert a hash into the hash table.

        :param file_hash: hash to insert
        :param key: key of the file in the directory table
        :param rotation: rotation of the file
        :return:
        """
        # make sure the rotation matches
        if rotation not in (0, 90, 180, 270):
            raise ValueError(f"Unsupported rotation value {rotation}")

        # update the hash table
        hash_key = self.add_increment_hash(file_hash)

        # update the directory table
        row = f"hash_{rotation}"
        self.debug_execute(f"UPDATE directory SET {row} = {hash_key} WHERE key = {key}")

    def has_all_hashes(self, key: int):
        """
        Check if a file has all hashes populated.

        :param key: key of the file in the directory table
        :return: if a file has all 4 entries.
        """
        self.debug_execute(f"SELECT hash_0, hash_90, hash_180, hash_270 FROM directory WHERE key = {key}")
        row = self.cur.fetchone()

        # check all values are set
        for c in row:
            if c is None:
                return False

        # return true if the for loop was unsuccessful.
        return True

    def has_any_hash(self, key: int):
        """
        Check if a file has any hash already populated.

        :param key: key of the file in the directory table
        :return: if a file has any entry.
        """
        self.debug_execute(f"SELECT hash_0, hash_90, hash_180, hash_270 FROM directory WHERE key = {key}")
        row = self.cur.fetchone()

        # check all values are set
        for c in row:
            if c is not None:
                return True

        # return true if the for loop was unsuccessful.
        return False

    def del_all_hashes(self, key: int):
        """
        Delete all the 4 possible hashes of a given file.

        :param key: key in the directory table
        :return:
        """
        # TODO implement call with transactions to make sure coherancy between hash table count and directory table is
        #  assured

        self.logger.warning("Deleting hashes, this is not matched with the hash table at the moment.")
        self.debug_execute(f"UPDATE directory SET hash_0 = NULL, hash_90 = NULL, hash_180 = NULL, hash_270 = NULL "
                           f"WHERE key = {key}")

    def get_hash_of_key(self, key: int) -> list:
        """
        Get the hashes associated with a certain image.

        :param key: the key of the image in the directory table
        :return: [Hash 0, Hash 90, Hash 180, Hash 270]
        """
        self.debug_execute(f"SELECT hash_0, hash_90, hash_180, hash_270 FROM directory WHERE key = {key}")
        cols = self.cur.fetchone()
        hashes = [None, None, None, None]

        # go through the hashes
        for i in range(4):
            entry = cols[i]

            # get the data from the hash_table
            self.debug_execute(f"SELECT hash FROM hash_table WHERE key = {entry}")
            res = self.cur.fetchone()

            # store the output
            if res is not None:
                hashes[i] = res[0]

        return hashes

    def get_many_preprocessing_errors(self, start_key: int = None, count: int = 1000) -> List[dict]:
        """
        Get rows which contain errors. Wrapp the result in dicts and return them.

        :param start_key: Starting key.
        :param count: Number of Results to be returned at maximum.
        :return:
        """
        # fetching from the beginning
        if start_key is None:
            self.debug_execute(f"SELECT * FROM directory WHERE error IS NOT NULL ORDER BY key ASC")
            return self.cur.fetchmany(count)

        # fetching from starting key.
        self.debug_execute(f"SELECT * FROM directory WHERE error IS NOT NULL AND key > {start_key} "
                           f"ORDER BY key ASC")

        return self.wrap_many_dict_dir(self.cur.fetchmany(count))

    # ------------------------------------------------------------------------------------------------------------------
    # THUMBNAIL FILENAME TABLE
    # ------------------------------------------------------------------------------------------------------------------

    def create_thumb_table(self, purge: bool = False):
        """
        Create tables which contain the names of the thumbnails (to make sure there's no collisions ahead of time)

        :param purge: if True, purge the tables before creating them.
        :return:
        """

        # Drop the tables if purge is set
        if purge:
            self.logger.info("Purging preexisting indexes of directories.")

            if self.test_thumb_table_existence():
                self.logger.info("Dropping directory A table.")
                self.drop_thumb()

        self.debug_execute("CREATE TABLE thumb ( "
                           "key INTEGER PRIMARY KEY, "
                           "filename TEXT , "
                           "dir_b INTEGER DEFAULT 0 CHECK (dir_b >= 0 AND dir_b <= 1),"
                           "UNIQUE (filename, dir_b)  )")

    def test_thumb_table_existence(self):
        """
        Check the table for thumbnails of directory table, exists. DOES NOT VERIFY THE TABLE DEFINITION!

        :return:
        """
        self.cur.execute(f"SELECT * FROM sqlite_master WHERE tbl_name IS 'thumb'")
        return self.cur.fetchone() is not None

    def drop_thumb(self):
        """
        Drop a table related to the thumbnails of the directories.

        :return:
        """
        self.debug_execute(f"DROP TABLE thumb")

    def get_thumb_name(self, key: int):
        """
        Get the thumbnail name associated with the key.

        :param key: key to search the thumbnail path for
        :return:
        """
        self.debug_execute(f"SELECT * FROM thumb WHERE key = {key}")
        return self.cur.fetchone()

    def generate_new_thumb_name(self, key: int, file_name: str, retry_limit: int = 1000, dir_a: bool = True):
        """
        Generate a new free name for a file. If a file name is taken, will retry a limited number of times again.
        The retry_limit is there to prevent a theoretically endless loop. If this was to trigger for you, update the
        attribute in the FastDifPy class or write your own function.

        :param key: key in the directory_X tables
        :param file_name: file name for which to generate the thumbnail name
        :param retry_limit: how many file names are to be tested.
        :param dir_a: if it is to be inserted into thumb_a or thumb_b table.
        :return:
        """
        index = 0
        free = False

        name, ext = os.path.splitext(file_name)
        thumb_name = f"{name}_thumb_{index:03}{ext}"

        while not free:
            if self.thumb_name_exists(thumb_name, dir_a):
                index += 1
                thumb_name = f"{name}_thumb_{index:03}{ext}"
            else:
                break

            if index > retry_limit:
                raise ValueError(f"Filename '{file_name}' is too common, it has been used {retry_limit} times.")

        self.debug_execute(f"INSERT INTO thumb (key, filename, dir_b) "
                           f"VALUES ({key}, '{thumb_name}', {0 if dir_a else 1})")
        return thumb_name

    def thumb_name_exists(self, thumb_name: str, dir_a: bool = True):
        """
        Check if the name exists already, given the name and the directory the file is in.

        :param thumb_name: name to check
        :param dir_a: if it is to be searched in dir a or dir b
        :return:
        """
        self.debug_execute(f"SELECT * FROM thumb WHERE filename IS '{thumb_name}' AND dir_b = {0 if dir_a else 1}")
        return self.cur.fetchone() is not None

    # ------------------------------------------------------------------------------------------------------------------
    # PLOT TABLE
    # ------------------------------------------------------------------------------------------------------------------

    def create_plot_table(self, purge: bool = False):
        """
        Create tables which contain the filenames of the plots (to make sure there's no collisions ahead of time)

        :param purge: if True, purge the tables before creating them.
        :return:
        """

        # Drop the tables if purge is set
        if purge:
            self.logger.info("Purging preexisting indexes of directories.")

            if self.test_plot_table_existence():
                self.logger.info("Dropping directory A table.")
                self.drop_plot()

        self.debug_execute("CREATE TABLE plots ( key INTEGER PRIMARY KEY, key_a INTEGER, key_b INTEGER )")

    def test_plot_table_existence(self):
        """
        Check the table for plots, exists. DOES NOT VERIFY THE TABLE DEFINITION!

        :return:
        """
        self.cur.execute(f"SELECT * FROM sqlite_master WHERE tbl_name IS 'plots'")
        return self.cur.fetchone() is not None

    def drop_plot(self):
        """
        Drop a table related to the plots.

        :return:
        """
        self.debug_execute(f"DROP TABLE plots")

    def get_plot_name(self, key_a: int, key_b: int):
        """
        Get the plot name associated with the two keys.

        :param key_a: the first key provided to the dif table.
        :param key_b: the second key provided in the dif table.
        :return:
        """
        self.debug_execute(f"SELECT * FROM plots WHERE key_a = {key_a} AND key_b = {key_b}")
        return self.cur.fetchone()

    def make_plot_name(self, key_a: int, key_b: int) -> str:
        """
        Generate a new free name for a file. Does not attempt to retry the filename.

        :param key_a: first key provided in the dif table
        :param key_b: second key provided in the dif table
        :return: filename associated with the two keys.
        """
        res = self.get_plot_name(key_a=key_a, key_b=key_b)

        if res is not None:
            return f"{res[0]}.png"

        self.debug_execute(f"INSERT INTO plots (key_a, key_b) VALUES ({key_a}, {key_b})")
        return self.make_plot_name(key_a=key_a, key_b=key_b)

    def get_associated_keys(self, file_name: str) -> Union[tuple, None]:
        """
        Given a file name returns the associated keys in to said plot (if not apparent by the filename I need to put
        in the titles.

        :param file_name: File name to get the two keys from.
        :return: row (tuple) or None
        """
        try:
            db_key = int(os.path.splitext(os.path.basename(file_name))[0])
        except ValueError:
            return None

        self.debug_execute(f"SELECT * FROM plots WHERE key = {db_key}")
        return self.cur.fetchone()

    # ------------------------------------------------------------------------------------------------------------------
    # HASH TABLE
    # ------------------------------------------------------------------------------------------------------------------

    def create_hash_table(self, purge: bool = False):
        """
        Create the hash table and purge preexisting table if desirerd.

        :param purge: if True, purge the table before creating it.
        :return:
        """
        if purge:
            if self.test_hash_table_existence():
                self.drop_hash_table()

        self.debug_execute("CREATE TABLE hash_table ("
                           "key INTEGER PRIMARY KEY AUTOINCREMENT , "
                           "hash TEXT UNIQUE , "
                           "count INTEGER CHECK (count >=0 ))"
                           )

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

    def add_increment_hash(self, file_hash: str):
        """
        Add the hash to database if it doesn't exist otherwise increment it.

        :param file_hash: the hash to be inserted.
        :return: The key of the hash.
        """
        self.debug_execute(f"SELECT * FROM hash_table WHERE hash = '{file_hash}'")

        # no entry in database, add it.
        row = self.cur.fetchone()
        if row is None:
            self.cur.execute(f"INSERT INTO hash_table (hash, count) VALUES ('{file_hash}', 1)")
            self.cur.execute(f"SELECT key FROM hash_table WHERE hash = '{file_hash}'")
            return self.cur.fetchone()[0]

        # increment the key
        key = row[0]
        self.debug_execute(f"UPDATE hash_table SET count = {row[2] + 1} WHERE key = {key}")
        return key

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
                           "dif REAL CHECK (dif_table.dif >= -1) DEFAULT -1,"
                           "error TEXT,"
                           "success INT CHECK (dif_table.success >= 0 AND dif_table.success <= 1),"
                           "UNIQUE (key_a, key_b)) ")

    def test_dif_table_existence(self) -> bool:
        """
        Check if the dif table exists. DOES NOT VERIFY THE TABLE DEFINITION!

        :return: bool, True if the table exists
        """
        self.cur.execute(f"SELECT * FROM sqlite_master WHERE tbl_name IS 'dif_table'")
        return self.cur.fetchone() is not None

    def drop_dif_table(self):
        """
        Drop the dif table.

        :return:
        """
        self.debug_execute(f"DROP TABLE dif_table")

    def insert_dif_success(self, key_a: int, key_b: int, dif: float) -> bool:
        """
        Insert a new row into the database. If the value exists already, return False, else return True

        :param key_a: key of first image in directory_X table
        :param key_b: key of second image in directory_X table
        :param dif: difference between the images.
        :return: bool if the insert was successful or the key pair existed already.
        """
        if self.get_by_pair(key_a=key_a, key_b=key_b) is not None:
            return False

        self.debug_execute(f"INSERT INTO dif_table (key_a, key_b, dif, success) "
                           f"VALUES ({key_a}, {key_b}, {dif}, 1)")
        return True

    def insert_dif_error(self, key_a: int, key_b: int, error: str) -> bool:
        """
        Insert a new row into the database. If the value exists already, return False, else return True

        :param key_a: key of first image in directory_X table
        :param key_b: key of second image in directory_X table
        :param error: error that occurred during processing.
        :return: bool if the insert was successful or the key pair existed already.
        """
        if self.get_by_pair(key_a=key_a, key_b=key_b) is not None:
            return False

        self.debug_execute(f"INSERT INTO dif_table (key_a, key_b, success, error) "
                           f"VALUES ({key_a}, {key_b}, 0, '{error}')")
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
        if row is None:
            return None

        return {
            "key": row[0],
            "key_a": row[1],
            "key_b": row[2],
            "dif": row[3],
            "error": row[4],
            "success": row[5]
        }

    @staticmethod
    def wrap_many_dict_dif(rows: List[tuple]):
        """
        Wraps a list of rows in dictionaries.

        :param rows: rows to wrap
        :return:
        """
        result = []
        for row in rows:
            result.append(SQLiteDatabase.all_to_dict_dif(row))
        return result

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

    def update_pair_row(self, key_a: int, key_b: int, dif: float = None) -> bool:
        """
        Updates a pair with the new data. if the data is not specified, the preexisting data is used.
        Return true if the update was successful. Return False if the row didn't exist.

        :param key_a: key of first image in directory_X table
        :param key_b: key of second image in directory_X table
        :param dif: difference measurement
        :return: if update was successful
        """

        # get the previous row.
        prev_row = self.get_by_pair(key_a=key_a, key_b=key_b)

        if prev_row is None:
            return False

        if dif is None:
            dif = prev_row["dif"]

        self.debug_execute(f"UPDATE dif_table SET dif = {dif} WHERE key_a = {key_a} AND "
                           f"key_b = {key_b}")

        return True

    def get_all_matching_pairs(self, threshold: float):
        """
        Fetches all pairs in the dif table matching the threshold and which terminated successfully.

        :param threshold: in avg diff.
        :return:
        """
        self.debug_execute(f"SELECT * FROM dif_table WHERE dif >= 0 AND dif < {threshold}")
        return self.cur.fetchall()

    def get_many_pairs(self, threshold: float, start_key: int = None, count: int = 1000):
        """
        Fetch duplicate pairs from the database. If a start is provided, selecting anything going further from there.

        :param count: number of pairs to fetch.
        :param threshold: below what the dif value needs to be.
        :param start_key: larger than that the diff needs to be.
        :return: tuples from
        """
        # fetching from the beginning
        if start_key is None:
            self.debug_execute(f"SELECT * FROM dif_table WHERE dif >= 0 AND dif < {threshold} ORDER BY key ASC")
            return self.wrap_many_dict_dif(self.cur.fetchmany(count))

        # fetching from starting key.
        self.debug_execute(f"SELECT * FROM dif_table WHERE dif >= 0 AND dif < {threshold} AND key > {start_key} "
                           f"ORDER BY key ASC")
        return self.wrap_many_dict_dif(self.cur.fetchmany(count))

    def get_many_comparison_errors(self, start_key: int = None, count: int = 1000) -> List[dict]:
        """
        Fetch up to count of errors in the dif table. Returns the key in the dif_table, two keys in the directory
        table, the file paths to the compared files and the error message.

        :param start_key: key in the dif_table to start from.
        :param count:
        :return:
        """

        # fetch from the beginning
        if start_key is None:
            self.debug_execute(f"SELECT dif_table.key, dif_table.key_a, dif_table.key_b,  a.path, b.path, "
                               f"dif_table.error "
                               f"FROM dif_table "
                               f"JOIN directory a on dif_table.key_a = a.key "
                               f"JOIN directory b on dif_table.key_b = b.key "
                               f"WHERE dif_table.error IS NOT NULL ORDER BY dif_table.key ASC")

            return self.wrap_many_errors_dif(self.cur.fetchmany(count))

        # fetching from starting key.
        self.debug_execute(f"SELECT dif_table.key, dif_table.key_a, dif_table.key_b,  a.path, b.path, "
                           f"dif_table.error "
                           f"FROM dif_table "
                           f"JOIN directory a on dif_table.key_a = a.key "
                           f"JOIN directory b on dif_table.key_b = b.key "
                           f"WHERE dif_table.error IS NOT NULL ORDER BY dif_table.key ASC")

        return self.wrap_many_errors_dif(self.cur.fetchmany(count))

    @staticmethod
    def error_to_dict(row: tuple = None) -> Union[dict, None]:
        """
        Wrapp the result of an error row which was previously created by using two joins on the keys.
        It only contains the paths, keys in the dir table, key in the dif_table and the error string

        :param row: row as tuple to wrap
        :return: the row tuple wrapped with a dict for better readability
        """
        if row is None:
            return None

        return {
            "dif_key": row[0],
            "dir_key_a": row[1],
            "dir_key_b": row[2],
            "a_path": row[3],
            "b_path": row[4],
            "error": SQLiteDatabase.from_b64(row[5]),
        }

    @staticmethod
    def wrap_many_errors_dif(rows: List[tuple]) -> List[dict]:
        """
        Wrap error rows in a dict.

        :param rows: list of tuples that should be wrapped.
        :return: list of wrapped rows in dict.
        """
        results = []

        for row in rows:
            results.append(SQLiteDatabase.error_to_dict(row))

        return results

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
            self.logger.exception(f"Exception {e} with statement:\n{statement}")
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

    def disconnect(self):
        """
        Disconnect from the Database
        :return:
        """
        self.con.commit()
        self.con.close()

    @property
    def has_b(self):
        """
        Executes an SQL statement to detect if there are any entries in directory b.

        :return: bool
        """
        self.debug_execute("SELECT * FROM directory WHERE dir_b > 0")
        return self.cur.fetchone() is not None

    @staticmethod
    def to_b64(to_encode: Any):
        """
        Convert an object to a b64 string

        :param to_encode: object to encode
        :return: base64 string
        """
        json_str = json.dumps(to_encode)
        bytes_string = json_str.encode("utf-8")
        return base64.standard_b64encode(bytes_string).decode("utf-8")

    @staticmethod
    def from_b64(b64_string: str):
        """
        Convert a b64 string to a python object

        :param b64_string: a b64 encoded python object
        :return: a python object
        """
        bytes_string = base64.standard_b64decode(b64_string.encode("utf-8"))
        json_string = bytes_string.decode("utf-8")
        return json.loads(json_string)

    def commit(self):
        """
        Commit any not stored changes now to the filesystem.

        :return:
        """
        self.con.commit()

    def free(self):
        """
        Remove the database file from.

        :return:
        """
        os.remove(self.path)

    def prepare_logging(self):
        """
        Get a logger, set the level and set the propagation.
        """
        self.logger = logging.getLogger("fast_diff_py.sql_database")
        self.logger.propagate = True
        self.logger.level = logging.DEBUG

    @staticmethod
    def thread_safe():
        """
        Returns weather the implementation of the database is thread safe (for improved performance)
        :return:
        """
        return False

    def create_config_dump(self):
        return {"type": "sqlite", "path": self.path}