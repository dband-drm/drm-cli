import sqlite3
from sqlite3 import Error

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn

def close_connection(conn):
    """ close a database connection
    :param conn: the Connection object
    :return:
    """
    conn.close

def execute_query(conn, query):
    """
    Query & return results
    :param conn: the Connection object
    :param query: SQL query to run
    :return: Dataset
    """
    cur = conn.cursor()
    cur.execute(query)

    rows = cur.fetchall()

    return rows

def execute_command(conn, command):
    """
    Execute SQL command (DDL/DML)
    :param conn: The Connection object
    :param command: SQL Command (DML/DDL) to run
    """
    cur = conn.cursor()
    cur.execute(command)
    conn.commit()

