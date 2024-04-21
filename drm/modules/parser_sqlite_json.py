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

class Connections:
    def get_connection_by_solution_id_and_name(solution_id, name, connection_obj):
        """ Return solution connection details by solution_id and name
        :param solution_id: Solution ID
        :param name: Connection name
        :param connection_obj: Connection object
        :return: JSON
        """
        js = json.loads('{"connections":[]}')
        drm_db = Db(DRM_DB_NAME)
        sql_command = "select id, name, solution_id, connection_type_id, connection_string, is_active from connections where solution_id = {sol_id} and name = '{name}';".format(sol_id = solution_id, name = name)
        rows = drm_db.select_query(sql_command)
        for row in rows:
            connection_obj.id = row[0]    
            connection_obj.name = row[1]    
            connection_obj.solution_id = row[2]    
            connection_obj.connection_type_id = row[3]    
            connection_obj.connection_string = row[4]    
            connection_obj.is_active = row[5] 
            connection_js = json.loads(json.dumps(connection_obj.__dict__))
            js['connections'].append(connection_js)
        return json.dumps(js)

class SqlScriptsVariables:
    def get_sql_scripts_variables_by_solution_id(solution_id, sql_script_variable_obj):
        """ Return solution sql_scripts_variables details by solution_id
        :param solution_id: Solution ID
        :param sql_script_variable_obj: Sql_Scripts_Variable object
        :return: JSON
        """
        js = json.loads('{"sql_scripts_variables":[]}')
        drm_db = Db(DRM_DB_NAME)
        sql_command = "select id, name, solution_id, value from sql_scripts_variables where solution_id = {sol_id} order by id;".format(sol_id = solution_id)
        rows = drm_db.select_query(sql_command)
        for row in rows:
            sql_script_variable_obj.id = row[0]    
            sql_script_variable_obj.name = row[1]    
            sql_script_variable_obj.solution_id = row[2]    
            sql_script_variable_obj.value = row[3]    
            sql_script_variable_js = json.loads(json.dumps(sql_script_variable_obj.__dict__))
            js['sql_scripts_variables'].append(sql_script_variable_js)
        return json.dumps(js)

class SqlScripts:
    def get_sql_scripts_by_solution_id(solution_id, sql_script_obj):
        """ Return solution sql_scripts details by solution_id
        :param solution_id: Solution ID
        :param sql_script_obj: Sql_Script object
        :return: JSON
        """
        js = json.loads('{"sql_scripts":[]}')
        drm_db = Db(DRM_DB_NAME)
        sql_command = "select id, name, solution_id, sql_text from sql_scripts where solution_id = {sol_id} order by id;".format(sol_id = solution_id)
        rows = drm_db.select_query(sql_command)
        for row in rows:
            sql_script_obj.id = row[0]    
            sql_script_obj.name = row[1]    
            sql_script_obj.solution_id = row[2]    
            sql_script_obj.sql_text = row[3]    
            sql_script_js = json.loads(json.dumps(sql_script_obj.__dict__))
            js['sql_scripts'].append(sql_script_js)
        return json.dumps(js)

class Projects:
    def get_projects_by_solution_id(solution_id, project_obj):
        """ Return solution projects details by solution_id
        :param solution_id: Solution ID
        :param project_obj: Project object
        :return: JSON
        """
        js = json.loads('{"projects":[]}')
        drm_db = Db(DRM_DB_NAME)
        sql_command = "select projects.id, projects.name, projects.solution_id, projects.ordinal, targets_compare_db, targets_type_id, targets_list, targets_sql_script_id, sql_scripts.sql_text as targets_sql_text, max_degree_in_parallel, timeout_in_min, sleep_time_in_sec, fail_on_error, is_active from projects left join sql_scripts on projects.solution_id = sql_scripts.solution_id and projects.targets_sql_script_id = sql_scripts.id where projects.solution_id = {sol_id} order by projects.ordinal, projects.id;".format(sol_id = solution_id)
        rows = drm_db.select_query(sql_command)
        for row in rows:
            project_obj.id = row[0]    
            project_obj.name = row[1]    
            project_obj.solution_id = row[2]    
            project_obj.ordinal = row[3]    
            project_obj.targets_compare_db = row[4]    
            project_obj.targets_type_id = row[5]    
            project_obj.targets_list = row[6]    
            project_obj.targets_sql_script_id = row[7]    
            project_obj.targets_sql_text = row[8]    
            project_obj.max_degree_in_parallel = row[9]    
            project_obj.timeout_in_min = row[10]    
            project_obj.sleep_time_in_sec = row[11]    
            project_obj.fail_on_error = row[12]    
            project_obj.is_active = row[13]    
            project_js = json.loads(json.dumps(project_obj.__dict__))
            js['projects'].append(project_js)
        return json.dumps(js)

