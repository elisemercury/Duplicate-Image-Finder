import mariadb
from fast_diff_py.database import Database
import datetime


class MariaDBDatabase(Database):
    user: str
    host: str
    port: int
    database: str

    password: str = None
    table_name: str = None

    kw: dict = None

    def __init__(self, user: str, host: str, port: int, database: str, password: str = None, table_name: str = None,
                 **kwargs):

            # Create super call just in case
            super().__init__()

            # Store the input
            self.user = user
            self.host = host
            self.port = port
            self.database = database
            self.password = password
            self.table_name = table_name

            self.kw = kwargs
            if len(kwargs) == 0:
                self.kw = {}

            # connect to database
            mariadb.connect(
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
                database=self.database,
                **kwargs
            )

            self.table_name = table_name
            if table_name is None:
                self.table_name = f"diff_tbl_{hash(datetime.datetime.now())}"
