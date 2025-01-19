import sqlite3
import logging
from sqlite3 import Error
from modules import drm_logger

logger = drm_logger.configure_logging("sqlite")

@drm_logger.log_decorator(logger) 
def create_connection(db_file):
    """ 
    create a database connection to the SQLite database specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn

@drm_logger.log_decorator(logger) 
def close_connection(conn):
    """ 
    close a database connection
    :param conn: the Connection object
    :return:
    """
    conn.close

@drm_logger.log_decorator(logger) 
def execute_query(conn, query):
    """
    Query & return results
    :param conn: the Connection object
    :param query: SQL query to run
    :return: Query restils (Dataset)
    """
    cur = conn.cursor()
    cur.execute(query)

    rows = cur.fetchall()

    return rows

@drm_logger.log_decorator(logger) 
def execute_command(conn, command):
    """
    Execute SQL command (DDL/DML)
    :param conn: The Connection object
    :param command: SQL Command (DML/DDL) to run
    :return:
    """
    cur = conn.cursor()
    cur.execute(command)
    conn.commit()

