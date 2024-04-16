import sys
from modules import sqlite

class Db:
    def __init__(self, db_name = ""):   
        """ Constructor
        :param db_name: SQLite databae name
        :return:
        """
        self.db_name = db_name

    def select_query(self, query):    
        """ Run SQL query & return result
        :param query: SQL Query
        :return: result
        """
        conn = sqlite.create_connection(self.db_name)
        rows = sqlite.execute_query(conn, query)
        sqlite.close_connection(conn)
        return rows

class Release:
    def __init__(self, db_name = ""):   
        """ Constructor
        :param db_name: SQLite databae name
        :return:
        """
        self.db_name = db_name

    def get_release_name(self, release_id, enviroment_name):
        """ Return release_name by release_id & environment_name
        :param release_id: Release ID
        :param enviroment_name: Environment name
        :return: Release name
        """
        drm_db = Db(self.db_name)
        sql_command = "select release_name from environments cross join releases where environment_name = '{env_name}' and release_id = {rel_id};".format(env_name = enviroment_name, rel_id = release_id)
        rows = drm_db.select_query(sql_command)
        for row in rows:
            release_name = row[0]    
        return release_name