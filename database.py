from psycopg2 import pool


class Database:
    __connection_pool = None
    # __prevents the user from accessing the connection_pool from a different class of the code

    @classmethod
    def initialise(cls, **kwargs):
        # connection pool creates a number of connections that we can reuse
        cls.__connection_pool = pool.SimpleConnectionPool(1, 10, **kwargs)

    @classmethod
    def get_connection(cls):
        return cls.__connection_pool.getconn()

    @classmethod
    def return_connection(cls, connection):
        Database.__connection_pool.putconn(connection)

    @classmethod
    def close_all_connections(cls):
        Database.__connection_pool.closeall()


class CursorFromConnectionFromPool:
    # obtaining a cursor from the ConnectionFromPool class
    def __init__(self):
        self.connection = None
        self.cursor = None

    """this method tells the class to getconn()
    at the start of the with clause the enter method gets called """
    def __enter__(self):
        self.connection = Database.get_connection()
        self.cursor = self.connection.cursor()
        return self.cursor

    # at the end of the with clause the exit method gets called
    def __exit__(self, exc_type, exception_value, exc_tb):
        if exception_value is not None:  # e.g. type error, value error, attribute error
            self.connection.rollback()
        else:
            self.cursor.close()
            self.connection.commit()
        Database.return_connection(self.connection)
