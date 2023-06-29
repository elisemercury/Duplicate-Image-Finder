import mariadb
from fast_diff_py.sql_database import SQLBase, IntegrityError
from fast_diff_py.datatransfer import CompareImageResults
import datetime
from typing import Union, List
import os
import logging


class MariaDBDatabase(SQLBase):
    user: str
    host: str
    port: int
    database: str

    password: str = None
    table_suffix: str = None

    kw: dict = None

    con: Union[mariadb.Connection, None] = None
    cur: Union[mariadb.Cursor, None] = None
    logger: logging.Logger

    def __init__(self, user: str, host: str, port: int, database: str, password: str = None, table_suffix: str = None,
                 purge: bool = False, **kwargs):

        # Create super call just in case
        super().__init__()

        self.prepare_logging()

        # Store the input
        self.user = user
        self.host = host
        self.port = port
        self.database = database
        self.password = password
        self.table_suffix = table_suffix

        self.kw = kwargs
        if len(kwargs) == 0:
            self.kw = {}

        self.connect()

        if len(table_suffix) > 20:
            raise ValueError("table suffix is too long. Max length is 20")

        self.table_suffix = table_suffix
        if table_suffix is None:
            self.table_suffix = f"{hash(datetime.datetime.now())}"

        self.create_tables(purge=purge)

    def create_tables(self, purge: bool = False):
        """
        First tests if the tables exist and then creates them.
        :param purge:
        :return:
        """
        # Removing all tables
        if purge:
            self.logger.info("Purging preexisting tables.")

            if self.test_thumb_table_existence():
                self.logger.info("Dropping preexisting thumbnail table.")
                self.drop_thumb()
            if self.test_plot_table_existence():
                self.logger.info("Dropping preexisting plot table.")
                self.drop_plot()
            if self.test_diff_table_existence():
                self.logger.info("Dropping preexisting error table.")
                self.drop_dif_table()
            if self.test_dir_table_existence():
                self.logger.info("Dropping preexisting directory table.")
                self.drop_dir()
            if self.test_hash_table_existence():
                self.logger.info("Dropping preexisting hash table.")
                self.drop_hash_table()

        # creating the tables.
        if not self.test_hash_table_existence():
            self.logger.info("Creating hash table.")
            self.__create_hash_table()
        if not self.test_dir_table_existence():
            self.logger.info("Creating directory table.")
            self.__create_directory_tables()
        if not self.test_diff_table_existence():
            self.logger.info("Creating error table.")
            self.__create_diff_table()
        if not self.test_plot_table_existence():
            self.logger.info("Creating plot table.")
            self.__create_plot_table()
        if not self.test_thumb_table_existence():
            self.logger.info("Creating thumbnail table.")
            self.__create_thumb_table()

    # ------------------------------------------------------------------------------------------------------------------
    # DIRECTORY TABLES
    # ------------------------------------------------------------------------------------------------------------------

    def __create_directory_tables(self):
        """
        Simply create the directory table.
        :return:
        """

        # DATA DESCRIPTION:
        # prod_suc:
        # * -1 not processed
        # * -2 currently processing
        # *  0 error occurred while processing
        # *  1 processing success
        self.debug_execute(
            f"CREATE TABLE {self.directory_table} ("
            f"`key` INT UNSIGNED AUTO_INCREMENT,"
            f"path TEXT,"
            f"filename TEXT,"
            f"error TEXT,"
            f"proc_suc TINYINT DEFAULT -1 CHECK (proc_suc >= -2 AND proc_suc <= 1),"
            f"px INT DEFAULT -1 CHECK (px >= -1),"
            f"py INT DEFAULT -1 CHECK (py >= -1),"
            f"dir_b TINYINT DEFAULT 0 CHECK (dir_b >= 0 AND dir_b <= 1),"
            f"hash_0 INT UNSIGNED DEFAULT NULL,"
            f"hash_90 INT UNSIGNED DEFAULT NULL,"
            f"hash_180 INT UNSIGNED DEFAULT NULL,"
            f"hash_270 INT UNSIGNED DEFAULT NULL,"
            f"PRIMARY KEY (`key`),"
            f"UNIQUE (path, dir_b),"
            f"CONSTRAINT hash0 FOREIGN KEY (hash_0) "
            f"                 REFERENCES {self.hash_table} (`key`) "
            f"                 ON DELETE RESTRICT "
            f"                 ON UPDATE RESTRICT, "
            f"CONSTRAINT hash90 FOREIGN KEY (hash_90) "
            f"                 REFERENCES {self.hash_table} (`key`) "
            f"                 ON DELETE RESTRICT "
            f"                 ON UPDATE RESTRICT, "
            f"CONSTRAINT hash180 FOREIGN KEY (hash_180) "
            f"                 REFERENCES {self.hash_table} (`key`) "
            f"                 ON DELETE RESTRICT "
            f"                 ON UPDATE RESTRICT, "
            f"CONSTRAINT hash270 FOREIGN KEY (hash_270) "
            f"                 REFERENCES {self.hash_table} (`key`) "
            f"                 ON DELETE RESTRICT "
            f"                 ON UPDATE RESTRICT "
            f");"
        )

    def test_dir_table_existence(self):
        """
        Check the table for directory X, exists. DOES NOT VERIFY THE TABLE DEFINITION!

        :return:
        """
        self.debug_execute(f"SHOW TABLES LIKE '{self.directory_table}';")
        return self.cur.fetchone() is not None

    def drop_dir(self):
        """
        Drop a table related to the directories.

        :return:
        """
        # Global update statement is intended since table constraint wouldn't allow deletion otherwise.
        self.debug_execute(f"DROP TABLE {self.directory_table}")

    def add_file(self, path: str, filename: str, dir_a: bool = True):
        """
        Add a file to the database.

        :param path: path to file, including filename (e.g. /home/user/file.txt)
        :param filename: filename (e.g. file.txt) // For faster searching
        :param dir_a: if True, add to dir_a, else add to dir_b
        :return:
        """

        self.debug_execute(f"INSERT INTO {self.directory_table} (path, filename, dir_b) "
                           f"VALUES ('{path}', '{filename}', {0 if dir_a else 1})")

    def get_dir_count(self, dir_a: Union[bool, None] = None):
        """
        Get the number of files in the directory table.

        :param dir_a: True, count of dir_a, False, count of dir_b, None count of both.
        :return:
        """
        if dir_a is None:
            self.debug_execute(f"SELECT COUNT(`key`) FROM {self.directory_table}")
            return self.cur.fetchone()[0]

        self.debug_execute(f"SELECT COUNT(`key`) FROM {self.directory_table} WHERE dir_b = {0 if dir_a else 1}")
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
        self.debug_execute(f"UPDATE {self.directory_table} SET proc_suc = 1, px = {px}, py = {py} WHERE `key` = {key}")

    def update_dir_error(self, key: int, msg: str):
        """
        Set the flag for error of the file with the matching key. Set it in either table_a or table_b
        Error is stored in plane text atm (It might be necessary to store it in b64.

        :param key: file identifier which is to be updated
        :param msg: error message created when attempting to process the file.
        """
        msg_b64 = self.to_b64(msg)
        self.debug_execute(f"UPDATE {self.directory_table} SET proc_suc = 0, error='{msg_b64}' WHERE `key` = {key}")

    def get_next_to_process(self):
        """
        Get an unprocessed entry from the directory table. Returns None per default to signify that there's nothing to
        be computed.

        :return: Next one to compute or None
        """
        self.debug_execute(f"SELECT * FROM {self.directory_table} WHERE proc_suc = -1")
        return self.all_to_dict_dir(self.cur.fetchone())

    def mark_processing(self, task: dict):
        """
        Precondition, the entry already exists, so it can be updated

        :param task: dictionary generated by the get_next_to_process
        :return:
        """
        self.debug_execute(f"UPDATE {self.directory_table} SET proc_suc = -2 WHERE `key` = {task['key']}")

    def reset_first_loop_mark(self):
        """
        Reset the mark from mark_processing on all files that are currently in processing. Intended for resume of
        processing.
        :return:
        """
        self.debug_execute(f"UPDATE {self.directory_table} SET proc_suc = -1 WHERE proc_suc = -2")

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
            self.debug_execute(f"SELECT * FROM {self.directory_table} WHERE dir_b = {dir_b} ORDER BY `key` ASC")
            return self.wrap_many_dict_dir(rows=self.cur.fetchmany(count))

        # start from specific point
        self.debug_execute(f"SELECT * FROM {self.directory_table} WHERE `key` > {starting} AND dir_b = {dir_b} "
                           f"ORDER BY `key` ASC")
        return self.wrap_many_dict_dir(rows=self.cur.fetchmany(count))

    def fetch_row_of_key(self, key: int):
        """
        Fetch exactly the row matching the key and directory.

        :param key: the key of the row
        :return:
        """
        self.debug_execute(f"SELECT * FROM {self.directory_table} WHERE `key` = {key}")
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
        self.debug_execute(f"UPDATE {self.directory_table} SET {row} = {hash_key} WHERE `key` = {key}")

    def has_all_hashes(self, key: int):
        """
        Check if a file has all hashes populated.

        :param key: key of the file in the directory table
        :return: if a file has all 4 entries.
        """
        self.debug_execute(f"SELECT hash_0, hash_90, hash_180, hash_270 "
                           f"FROM {self.directory_table} WHERE `key` = {key}")
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
        self.debug_execute(f"SELECT hash_0, hash_90, hash_180, hash_270 "
                           f"FROM {self.directory_table} WHERE `key` = {key}")
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
        hashes = self.get_hash_of_key(key=key)
        for hs in hashes:
            if hs is None:
                continue

            self.__decrement_hash(hs)

        self.debug_execute(f"UPDATE {self.directory_table} "
                           f"SET hash_0 = NULL, hash_90 = NULL, hash_180 = NULL, hash_270 = NULL "
                           f"WHERE `key` = {key}")

    def __decrement_hash(self, key: int):
        """
        Decrement the count of a hash in the hash table.

        :param key: key of hash to decrement.
        :return:
        """
        self.debug_execute(f"SELECT count FROM {self.hash_table} WHERE `key` = {key}")
        row = self.cur.fetchone()

        if row is None:
            raise ValueError(f"No hash found. key {key}")

        count = row[0]
        self.debug_execute(f"UPDATE {self.hash_table} SET count = {count - 1} WHERE `key` = {key}")


    def get_hash_of_key(self, key: int) -> list:
        """
        Get the hashes associated with a certain image.

        :param key: the key of the image in the directory table
        :return: [Hash 0, Hash 90, Hash 180, Hash 270]
        """
        self.debug_execute(f"SELECT hash_0, hash_90, hash_180, hash_270 FROM {self.directory_table} "
                           f"WHERE `key` = {key}")

        cols = self.cur.fetchone()
        hashes = [None, None, None, None]

        # go through the hashes
        for i in range(4):
            entry = cols[i]

            # get the data from the hash_table
            self.debug_execute(f"SELECT hash FROM {self.hash_table} WHERE `key` = {entry}")
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
            self.debug_execute(f"SELECT * FROM {self.directory_table} WHERE error IS NOT NULL ORDER BY `key` ASC")
            return self.cur.fetchmany(count)

        # fetching from starting key.
        self.debug_execute(f"SELECT * FROM {self.directory_table} WHERE error IS NOT NULL AND `key` > {start_key} "
                           f"ORDER BY key ASC")

        return self.wrap_many_dict_dir(self.cur.fetchmany(count))

    # ------------------------------------------------------------------------------------------------------------------
    # THUMBNAIL FILENAME TABLE
    # ------------------------------------------------------------------------------------------------------------------

    def __create_thumb_table(self):
        """
        Simply create the thumbnail table.
        :return:
        """
        self.debug_execute(f"CREATE TABLE {self.thumbnail_table} ( "
                           f"`key` INT UNSIGNED, "
                           f"filename TEXT , "
                           f"dir_b TINYINT DEFAULT 0 CHECK (dir_b >= 0 AND dir_b <= 1),"
                           f"UNIQUE (filename, dir_b),"
                           f"PRIMARY KEY (`key`),"
                           f"FOREIGN KEY (`key`) REFERENCES {self.directory_table} "
                           f"ON DELETE RESTRICT ON UPDATE RESTRICT )")

    def test_thumb_table_existence(self):
        """
        Check the table for thumbnails of directory table, exists. DOES NOT VERIFY THE TABLE DEFINITION!

        :return:
        """
        self.debug_execute(f"SHOW TABLES LIKE '{self.thumbnail_table}';")
        return self.cur.fetchone() is not None

    def test_thumb_existence(self):
        """
        Check the table for thumbnails of directory table, exists. DOES NOT VERIFY THE TABLE DEFINITION!

        :return:
        """
        self.debug_execute(f"SELECT COUNT(`key`) FROM {self.thumbnail_table}")
        row = self.cur.fetchone()
        return row[0] > 0

    def drop_thumb(self):
        """
        Drop a table related to the thumbnails of the directories.

        :return:
        """
        self.debug_execute(f"DROP TABLE {self.thumbnail_table}")

    def get_thumb_name(self, key: int):
        """
        Get the thumbnail name associated with the key.

        :param key: key to search the thumbnail path for
        :return:
        """
        self.debug_execute(f"SELECT * FROM {self.thumbnail_table} WHERE `key` = {key}")
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

        self.debug_execute(f"INSERT INTO {self.thumbnail_table} (`key`, filename, dir_b) "
                           f"VALUES ({key}, '{thumb_name}', {0 if dir_a else 1})")
        return thumb_name

    def thumb_name_exists(self, thumb_name: str, dir_a: bool = True):
        """
        Check if the name exists already, given the name and the directory the file is in.

        :param thumb_name: name to check
        :param dir_a: if it is to be searched in dir a or dir b
        :return:
        """
        self.debug_execute(f"SELECT * FROM {self.thumbnail_table} "
                           f"WHERE filename = '{thumb_name}' "
                           f"AND dir_b = {0 if dir_a else 1}")
        return self.cur.fetchone() is not None

    # ------------------------------------------------------------------------------------------------------------------
    # PLOT TABLE
    # ------------------------------------------------------------------------------------------------------------------

    def __create_plot_table(self):
        """
        Create tables which contain the filenames of the plots (to make sure there's no collisions ahead of time)
        :return:
        """
        self.debug_execute(f"CREATE TABLE {self.plot_table} ( "
                           f"`key` INT UNSIGNED , "
                           f"key_a INT UNSIGNED, "
                           f"key_b INT UNSIGNED,"
                           f"PRIMARY KEY (`key`),"
                           f"CONSTRAINT id_a FOREIGN KEY (key_a)"
                           f"   REFERENCES {self.directory_table} (`key`)"
                           f"   ON DELETE RESTRICT "
                           f"   ON UPDATE RESTRICT,"
                           f"CONSTRAINT id_b FOREIGN KEY (key_b)"
                           f"   REFERENCES {self.directory_table} (`key`) "
                           f"   ON DELETE RESTRICT "
                           f"   ON UPDATE RESTRICT )")

    def test_plot_table_existence(self):
        """
        Check the table for plots, exists. DOES NOT VERIFY THE TABLE DEFINITION!

        :return:
        """
        self.debug_execute(f"SHOW TABLES LIKE '{self.plot_table}';")
        return self.cur.fetchone() is not None

    def drop_plot(self):
        """
        Drop a table related to the plots.

        :return:
        """
        self.debug_execute(f"DROP TABLE {self.plot_table}")

    def get_plot_name(self, key_a: int, key_b: int):
        """
        Get the plot name associated with the two keys.

        :param key_a: the first key provided to the dif table.
        :param key_b: the second key provided in the dif table.
        :return:
        """
        self.debug_execute(f"SELECT * FROM {self.plot_table} WHERE key_a = {key_a} AND key_b = {key_b}")
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

        self.debug_execute(f"INSERT INTO {self.plot_table} (key_a, key_b) VALUES ({key_a}, {key_b})")
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

        self.debug_execute(f"SELECT * FROM {self.plot_table} WHERE `key` = {db_key}")
        return self.cur.fetchone()

    # ------------------------------------------------------------------------------------------------------------------
    # HASH TABLE
    # ------------------------------------------------------------------------------------------------------------------

    def __create_hash_table(self):
        """
        Simply create the hash table.
        :return:
        """
        self.debug_execute(f"CREATE TABLE {self.hash_table} ("
                           f"`key` INT UNSIGNED AUTO_INCREMENT, "
                           f"hash TEXT UNIQUE , "
                           f"count INT CHECK (count >=0 ),"
                           f"PRIMARY KEY (`key`))"
                           )

    def test_hash_table_existence(self):
        """
        Check if the hash table exists. DOES NOT VERIFY THE TABLE DEFINITION!

        :return:
        """
        self.debug_execute(f"SHOW TABLES LIKE '{self.hash_table}';")
        return self.cur.fetchone() is not None

    def drop_hash_table(self):
        """
        Drop the hash table.

        :return:
        """
        self.debug_execute(f"DROP TABLE {self.hash_table}")

    def add_increment_hash(self, file_hash: str) -> int:
        """
        Add the hash to database if it doesn't exist otherwise increment it.

        :param file_hash: the hash to be inserted.
        :return: The key of the hash.
        """
        self.debug_execute(f"SELECT * FROM {self.hash_table} WHERE hash = '{file_hash}'")

        # no entry in database, add it.
        row = self.cur.fetchone()
        if row is None:
            self.debug_execute(f"INSERT INTO {self.hash_table} (hash, count) VALUES ('{file_hash}', 1)")
            self.debug_execute(f"SELECT `key` FROM {self.hash_table} WHERE hash = '{file_hash}'")
            return self.cur.fetchone()[0]

        # increment the key
        key = row[0]
        self.debug_execute(f"UPDATE {self.hash_table} SET count = {row[2] + 1} WHERE `key` = {key}")
        return key

    # ------------------------------------------------------------------------------------------------------------------
    # ERROR TABLE
    # ------------------------------------------------------------------------------------------------------------------

    def __create_diff_table(self):
        """
        Simply create the diff table.
        :return:
        """
        self.debug_execute(f"CREATE TABLE {self.diff_table} ("
                           f"`key` INT UNSIGNED AUTO_INCREMENT, "
                           f"key_a INT UNSIGNED NOT NULL , "
                           f"key_b INT UNSIGNED NOT NULL ,"
                           f"dif DOUBLE DEFAULT -1.0 CHECK (dif >= -1.0) ,"
                           f"error TEXT,"
                           f"success TINYINT CHECK (success >= 0 AND success <= 1),"
                           f"UNIQUE (key_a, key_b),"
                           f"PRIMARY KEY (`key`),"
                           f"CONSTRAINT identifier_a FOREIGN KEY (key_a)"
                           f"   REFERENCES {self.directory_table} (`key`)"
                           f"   ON UPDATE RESTRICT "
                           f"   ON DELETE RESTRICT, "
                           f"CONSTRAINT identifier_b FOREIGN KEY (key_b)"
                           f"   REFERENCES {self.directory_table} (`key`)"
                           f"   ON DELETE RESTRICT "
                           f"   ON UPDATE RESTRICT "
                           f") ")

    def test_diff_table_existence(self) -> bool:
        """
        Check if the dif table exists. DOES NOT VERIFY THE TABLE DEFINITION!

        :return: bool, True if the table exists
        """
        self.debug_execute(f"SHOW TABLES LIKE '{self.diff_table}';")
        return self.cur.fetchone() is not None

    def drop_dif_table(self):
        """
        Drop the dif table.

        :return:
        """
        self.debug_execute(f"DROP TABLE {self.diff_table}")

    def insert_diff_success(self, key_a: int, key_b: int, dif: float) -> bool:
        """
        Insert a new row into the database. If the value exists already, return False, else return True

        :param key_a: key of first image in directory_X table
        :param key_b: key of second image in directory_X table
        :param dif: difference between the images.
        :return: bool if the insert was successful or the key pair existed already.
        """
        if self.get_by_pair(key_a=key_a, key_b=key_b) is not None:
            return False

        self.debug_execute(f"INSERT INTO {self.diff_table} (key_a, key_b, dif, success) "
                           f"VALUES ({key_a}, {key_b}, {dif}, 1)")
        return True

    def insert_many_diff_success(self, tasks: List[CompareImageResults]):
        """
        Insert a list into table with single statement. Statement need to be successes
        :param tasks: list of elements to insert
        :return: None
        """

        statement = f"INSERT INTO {self.diff_table} (key_a, key_b, dif, success) VALUES "
        if len(tasks) == 0:
            return

        statement += f"({tasks[0].key_a}, {tasks[0].key_b}, {tasks[0].min_avg_diff}, 1)"

        for entry in tasks[1:]:
            statement += f", ({entry.key_a}, {entry.key_b}, {entry.min_avg_diff}, 1)"

        # Try builk insert otherwise perform slower insert.
        try:
            self.debug_execute(statement)
        except Exception as e:
            self.logger.exception(e)
            for task in tasks:
                self.insert_diff_success(key_a=task.key_a, key_b=task.key_b, dif=task.min_avg_diff)

    def insert_many_diff_errors(self, tasks: List[CompareImageResults]):
        """
        Insert a list into table with single statement. Statement need to be errors
        :param tasks: list of elements to insert
        :return: None
        """
        statement = f"INSERT INTO {self.diff_table} (key_a, key_b, success, error) VALUES "
        if len(tasks) == 0:
            return

        statement += f"({tasks[0].key_a}, {tasks[0].key_b}, 0, '{tasks[0].error}')"

        for entry in tasks[1:]:
            statement += f", ({entry.key_a}, {entry.key_b}, 0, {entry.error})"

        try:
            self.debug_execute(statement)
        except Exception as e:
            self.logger.exception(e)
            for task in tasks:
                self.insert_diff_error(key_a=task.key_a, key_b=task.key_b, error=task.error)

    def insert_diff_error(self, key_a: int, key_b: int, error: str) -> bool:
        """
        Insert a new row into the database. If the value exists already, return False, else return True

        :param key_a: key of first image in directory_X table
        :param key_b: key of second image in directory_X table
        :param error: error that occurred during processing.
        :return: bool if the insert was successful or the key pair existed already.
        """
        if self.get_by_pair(key_a=key_a, key_b=key_b) is not None:
            return False

        self.debug_execute(f"INSERT INTO {self.diff_table} (key_a, key_b, success, error) "
                           f"VALUES ({key_a}, {key_b}, 0, '{error}')")
        return True

    def get_by_pair(self, key_a: int, key_b: int) -> Union[dict, None]:
        """
        Get the row matching the pair of keys. Return the row wrapped in a dict or None if it doesn't exist.

        :param key_a: key of first image in directory_X table
        :param key_b: key of second image in directory_X table
        :return: None, nothing exists, dict of matching row
        """
        self.debug_execute(f"SELECT * FROM {self.diff_table} WHERE key_a = {key_a} AND key_b = {key_b}")
        res = self.cur.fetchone()

        if res is None:
            return None

        return self.all_to_dict_dif(res)

    def get_by_table_key(self, key: int):
        """
        Get a row by the table key. Return the row wrapped in a dict tor None if it doesn't exist.

        :param key: unique key in the dif table.
        :return: None, nothing exists, dict of matching row.
        """
        self.debug_execute(f"SELECT * FROM {self.diff_table} WHERE `key` = {key}")
        res = self.cur.fetchone()

        if res is None:
            return None

        return self.all_to_dict_dif(res)

    def update_pair_row(self, key_a: int, key_b: int, diff: float = None) -> bool:
        """
        Updates a pair with the new data. if the data is not specified, the preexisting data is used.
        Return true if the update was successful. Return False if the row didn't exist.

        :param key_a: key of first image in directory_X table
        :param key_b: key of second image in directory_X table
        :param diff: difference measurement
        :return: if update was successful
        """

        # get the previous row.
        prev_row = self.get_by_pair(key_a=key_a, key_b=key_b)

        if prev_row is None:
            return False

        if diff is None:
            diff = prev_row["dif"]

        self.debug_execute(f"UPDATE {self.diff_table} SET dif = {diff} WHERE key_a = {key_a} AND "
                           f"key_b = {key_b}")

        return True

    def get_all_matching_pairs(self, threshold: float):
        """
        Fetches all pairs in the dif table matching the threshold and which terminated successfully.

        :param threshold: in avg diff.
        :return:
        """
        self.debug_execute(f"SELECT * FROM {self.diff_table} WHERE dif >= 0 AND dif < {threshold}")
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
            self.debug_execute(f"SELECT * FROM {self.diff_table} WHERE dif >= 0 AND dif < {threshold} "
                               f"ORDER BY `key` ASC")
            return self.wrap_many_dict_dif(self.cur.fetchmany(count))

        # fetching from starting key.
        self.debug_execute(f"SELECT * FROM {self.diff_table} WHERE dif >= 0 AND dif < {threshold} "
                           f"AND `key` > {start_key} "
                           f"ORDER BY `key` ASC")
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
            self.debug_execute(f"SELECT {self.diff_table}.key, {self.diff_table}.key_a, {self.diff_table}.key_b,  "
                               f"a.path, b.path, {self.diff_table}.error "
                               f"FROM {self.diff_table} "
                               f"JOIN directory a on {self.diff_table}.key_a = a.`key` "
                               f"JOIN directory b on {self.diff_table}.key_b = b.`key` "
                               f"WHERE {self.diff_table}.error IS NOT NULL ORDER BY {self.diff_table}.`key` ASC")

            return self.wrap_many_errors_dif(self.cur.fetchmany(count))

        # fetching from starting key.
        self.debug_execute(f"SELECT {self.diff_table}.key, {self.diff_table}.key_a, {self.diff_table}.key_b,  "
                           f"a.path, b.path, {self.diff_table}.error "
                           f"FROM {self.diff_table} "
                           f"JOIN directory a on {self.diff_table}.key_a = a.`key` "
                           f"JOIN directory b on {self.diff_table}.key_b = b.`key` "
                           f"WHERE {self.diff_table}.error IS NOT NULL ORDER BY {self.diff_table}.`key` ASC")

        return self.wrap_many_errors_dif(self.cur.fetchmany(count))

    # ------------------------------------------------------------------------------------------------------------------
    # COMMON FUNCTIONS
    # ------------------------------------------------------------------------------------------------------------------

    def debug_execute(self, statement: str):
        """
        Wrapper to print the infringing statement in case of an error.

        :param statement: statement to execute
        :return:
        """
        try:
            self.cur.execute(statement)
        except Exception as e:
            self.logger.exception(f"Exception {e} with statement:\n{statement}")
            raise e

    def connect(self):
        """
        Create Connection to Database.
        :return:
        """
        self.con = mariadb.connect(
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.database,
            **self.kw
        )
        self.cur = self.con.cursor()

    def disconnect(self):
        """
        Disconnect from the Database
        :return:
        """
        self.con.commit()
        self.con.close()
        self.con = None
        self.cur = None

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
        if self.cur is None and self.con is None:
            return

        self.drop_dif_table()
        self.drop_dir() # child since it has a foreign key reference to hash table
        self.drop_hash_table()
        self.drop_thumb() # child since it has a foreign key reference to plot table
        self.drop_plot()

    def prepare_logging(self):
        """
        Get a logger, set the level and set the propagation.
        """
        self.logger = logging.getLogger("fast_diff_py.mariadb_database")
        self.logger.propagate = True
        self.logger.level = logging.DEBUG

    @property
    def thread_safe(self):
        """
        Returns weather the implementation of the database is thread safe (for improved performance)
        :return:
        """
        return True

    def create_config_dump(self):
        return {"type": "mariadb",
                "user": self.user,
                "host": self.host,
                "port": self.port,
                "database": self.database,
                "password": self.password,
                "table_suffix": self.table_suffix,
                "kwargs": self.kw}

    @property
    def directory_table(self):
        return f"directory_{self.table_suffix}"

    @property
    def hash_table(self):
        return f"hash_{self.table_suffix}"

    @property
    def thumbnail_table(self):
        return f"thumb_{self.table_suffix}"

    @property
    def plot_table(self):
        return f"plots_{self.table_suffix}"

    @property
    def diff_table(self):
        return f"diff_{self.table_suffix}"


class BenchmarkMariaDBDatabase(MariaDBDatabase):
    query_time = 0

    def debug_execute(self, statement: str):
        try:
            start = datetime.datetime.now()
            self.cur.execute(statement)
            stop = datetime.datetime.now()
            self.query_time += (stop - start).total_seconds()
        except Exception as e:
            self.logger.exception(f"Exception {e} with statement:\n{statement}")
            raise e