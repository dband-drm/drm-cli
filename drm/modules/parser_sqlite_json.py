import sys
import json
from modules import sqlite

DRM_DB_NAME = "./db/drm.db"

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


class Releases:
    def get_release_by_id(id, release_obj):
        """ Return release details by release_id
        :param release_id: Release ID
        :param release_obj: Release object
        :return: JSON
        """
        drm_db = Db(DRM_DB_NAME)
        sql_command = "select id, name, max_retries, is_active from releases where id = {rel_id};".format(rel_id = id)
        rows = drm_db.select_query(sql_command)
        for row in rows:
            release_obj.id = row[0]    
            release_obj.name = row[1]    
            release_obj.max_retries = row[2]    
            release_obj.is_active = row[3] 
        js = json.loads(json.dumps(release_obj.__dict__))
        return json.dumps(js)

class Solutions:
    def get_solutions_by_release_id(release_id, solution_obj):
        """ Return solutions list details by release_id
        :param release_id: Release ID
        :param solution_obj: Solution object
        :return: JSON
        """
        js = json.loads('{"solutions":[]}')
        drm_db = Db(DRM_DB_NAME)
        sql_command = "select id, name, release_id, ordinal, solution_type_id, path, is_active from solutions where release_id = {rel_id} order by ordinal;".format(rel_id = release_id)
        rows = drm_db.select_query(sql_command)
        for row in rows:
            solution_obj.id = row[0]    
            solution_obj.name = row[1]    
            solution_obj.release_id = row[2]    
            solution_obj.ordinal = row[3]    
            solution_obj.solution_type_id = row[4]    
            solution_obj.path = row[5]    
            solution_obj.is_active = row[6] 
            solution_js = json.loads(json.dumps(solution_obj.__dict__))
            js['solutions'].append(solution_js)
        return json.dumps(js)

