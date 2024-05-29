import sys
import json
import logging
from modules import files_and_folders, drm_logger

class Generic:

    logger = drm_logger.configure_logging("parser_json_json.Generic")

    @drm_logger.log_decorator(logger) 
    def get_table_columns_list(schema_file_name, table_name):
        """ 
        Return table columns list
        :param table_name: Table name
        :return: List of columns (JSON)
        """
        file = files_and_folders.Files(schema_file_name)
        drm_schema = file.load_file()

        js = json.loads('[]')
        #=================================
        # Get Projects info by Solution ID
        #=================================
        for table in drm_schema['tables']:
            if (table["name"] == table_name):
                for column in table["columns"]:
                    js.append(column["name"])
            
        return json.dumps(js)


class Releases:

    logger = drm_logger.configure_logging("parser_json_json.Releases")

    @drm_logger.log_decorator(logger) 
    def check_release_by_id_and_connection_name(db_file_name, id, connection_name):
        """ 
        Checks if active release & connection name exist in the system
        :param db_file_name: Database file name
        :param id: Release ID
        :param connection_name: Connection name
        :return: release ID & Connection ID (JSON)
        """
        verified_release_id = "null"
        verified_connection_id = "null"
        _connection_id = 0

        file = files_and_folders.Files(db_file_name)
        drm_db = file.load_file()
        for release in drm_db['releases']:
            if ("is_active" in release):
                is_active = release['is_active']
            else:
                is_active = True
            if (is_active and release['id'] == int(id)):
                verified_release_id = release['id']
                if ('solutions' in release):
                    for solution in release['solutions']:
                        if ("is_active" in solution):
                            is_active = solution['is_active']
                        else:
                            is_active = True
                        if(is_active):
                            if ('connections' in solution):
                                for connection in solution['connections']:
                                    _connection_id += 1
                                    if ("is_active" in connection):
                                        is_active = connection['is_active']
                                    else:
                                        is_active = True
                                    if (is_active and connection['name'] == connection_name):
                                        verified_connection_id = _connection_id

        js_text = '{"release_id": ' + str(verified_release_id) + ', "connection_id": ' + str(verified_connection_id) + '}'
        js = json.loads(js_text)
        return json.dumps(js)

    @drm_logger.log_decorator(logger) 
    def get_release_by_id(db_file_name, id, release_obj):
        """ 
        Return release details by release_id
        :param db_file_name: Database file name
        :param id: Release ID
        :param release_obj: Release object
        :return: Release info (JSON)
        """
        file = files_and_folders.Files(db_file_name)
        drm_db = file.load_file()
        for release in drm_db['releases']:
            if (release['id'] == int(id)):
                release_obj.id = release['id']    
                release_obj.name = release['name']    
                if  ("max_retries" in release):   
                    release_obj.max_retries = release['max_retries']
                else:
                    release_obj.max_retries = 0
                if  ("is_active" in release):   
                    release_obj.is_active = release['is_active'] 
                else:
                    release_obj.is_active = True
        js = json.loads(json.dumps(release_obj.__dict__))
        return json.dumps(js)

class Solutions:

    logger = drm_logger.configure_logging("parser_json_json.Solutions")

    @drm_logger.log_decorator(logger) 
    def get_solutions_by_release_id(db_file_name, release_id, solution_obj):
        """ 
        Return solutions list details by release_id
        :param db_file_name: Database file name
        :param release_id: Release ID
        :param solution_obj: Solution object
        :return: Solution info (JSON)
        """
        _solution_id = 0
        js = json.loads('{"solutions":[]}')
        file = files_and_folders.Files(db_file_name)
        drm_db = file.load_file()
        for release in drm_db['releases']:
            if (release['id'] == release_id):
                verified_release_id = release['id']
                if ("solutions" in release):
                    for solution in release['solutions']:
                        _solution_id += 1
                        solution_obj.id = _solution_id    
                        solution_obj.name = solution['name']    
                        solution_obj.release_id = release_id 
                        if  ("ordinal" in solution):
                            solution_obj.ordinal = solution['ordinal'] 
                        else:
                            solution_obj.ordinal = _solution_id
                        solution_obj.solution_type_id = solution['solution_type_id']    
                        solution_obj.path = solution['path']   
                        if  ("is_active" in solution):
                            solution_obj.is_active = solution['is_active'] 
                        else:
                            solution_obj.is_active = True
                        solution_js = json.loads(json.dumps(solution_obj.__dict__))
                        js['solutions'].append(solution_js)
        return json.dumps(js)

class Connections:

    logger = drm_logger.configure_logging("parser_json_json.Connections")

    @drm_logger.log_decorator(logger) 
    def get_connection_by_solution_id_and_name(db_file_name, release_id, solution_id, name, connection_obj):
        """ 
        Return solution connection details by solution_id and name
        :param db_file_name: Database file name
        :param release_id: Release ID
        :param solution_id: Solution ID
        :param name: Connection name
        :param connection_obj: Connection object
        :return: Connection details (JSON)
        """
        _solution_id = 0
        _connection_id = 0
        js = json.loads('{"connections":[]}')
        file = files_and_folders.Files(db_file_name)
        drm_db = file.load_file()
        for release in drm_db['releases']:
            if (release['id'] == int(release_id)):
                verified_release_id = release['id']
                if ("solutions" in release):
                    for solution in release['solutions']:
                        _solution_id += 1
                        if (int(solution_id) == _solution_id):
                            if ("connections" in solution):
                                for connection in solution['connections']:
                                    _connection_id += 1
                                    if(connection['name'] == name):
                                        connection_obj.id = _connection_id    
                                        connection_obj.name = connection['name']    
                                        connection_obj.solution_id = solution_id    
                                        connection_obj.connection_type_id = connection['connection_type_id']    
                                        connection_obj.connection_string = connection['connection_string']
                                        if ("is_active" in connection):   
                                            connection_obj.is_active = connection['is_active'] 
                                        else:
                                            connection_obj.is_active = True
                                        connection_js = json.loads(json.dumps(connection_obj.__dict__))
                                        js['connections'].append(connection_js)
        return json.dumps(js)

class SqlScriptsVariables:

    logger = drm_logger.configure_logging("parser_json_json.SqlScriptsVariables")

    @drm_logger.log_decorator(logger) 
    def get_sql_scripts_variables_by_solution_id(db_file_name, release_id, solution_id, sql_script_variable_obj):
        """ 
        Return solution sql_scripts_variables details by solution_id
        :param db_file_name: Database file name
        :param release_id: Release ID
        :param solution_id: Solution ID
        :param sql_script_variable_obj: Sql_Scripts_Variable object
        :return: SQL Scripts variables & values (JSON)
        """
        _solution_id = 0
        _sql_script_variable_id = 0
        js = json.loads('{"sql_scripts_variables":[]}')
        file = files_and_folders.Files(db_file_name)
        drm_db = file.load_file()
        for release in drm_db['releases']:
            if (release['id'] == int(release_id)):
                verified_release_id = release['id']
                if ("solutions" in release):
                    for solution in release['solutions']:
                        _solution_id += 1
                        if (int(solution_id) == _solution_id):
                            if ("sql_scripts_variables" in solution):
                                for sql_script_variable in solution['sql_scripts_variables']:
                                    _sql_script_variable_id += 1
                                    sql_script_variable_obj.id = _sql_script_variable_id    
                                    sql_script_variable_obj.name = sql_script_variable['name']    
                                    sql_script_variable_obj.solution_id = solution_id    
                                    sql_script_variable_obj.value = sql_script_variable['value']    
                                    sql_script_variable_js = json.loads(json.dumps(sql_script_variable_obj.__dict__))
                                    js['sql_scripts_variables'].append(sql_script_variable_js)
        return json.dumps(js)

class SqlScripts:

    logger = drm_logger.configure_logging("parser_json_json.SqlScripts")

    @drm_logger.log_decorator(logger) 
    def get_sql_scripts_by_solution_id(db_file_name, release_id, solution_id, sql_script_obj):
        """ 
        Return solution sql_scripts details by solution_id
        :param db_file_name: Database file name
        :param release_id: Release ID
        :param solution_id: Solution ID
        :param sql_script_obj: Sql_Script object
        :return: Get databases from queriy scripts (JSON)
        """
        _solution_id = 0
        _sql_script_id = 0
        js = json.loads('{"sql_scripts":[]}')
        file = files_and_folders.Files(db_file_name)
        drm_db = file.load_file()
        for release in drm_db['releases']:
            if (release['id'] == int(release_id)):
                verified_release_id = release['id']
                if ("solutions" in release):
                    for solution in release['solutions']:
                        _solution_id += 1
                        if (int(solution_id) == _solution_id):
                            if ("projects" in solution):
                                for project in solution['projects']:
                                    if ("targets_sql_text" in project):
                                        _sql_script_id += 1
                                        sql_script_obj.id = _sql_script_id   
                                        sql_script_obj.name = _sql_script_id    
                                        sql_script_obj.solution_id = solution_id    
                                        sql_script_obj.sql_text = project['targets_sql_text']    
                                        sql_script_js = json.loads(json.dumps(sql_script_obj.__dict__))
                                        js['sql_scripts'].append(sql_script_js)
        return json.dumps(js)

class Projects:

    logger = drm_logger.configure_logging("parser_json_json.Projects")

    @drm_logger.log_decorator(logger) 
    def get_projects_by_solution_id(db_file_name, release_id, solution_id, project_obj):
        """ 
        Return solution projects details by solution_id
        :param db_file_name: Database file name
        :param release_id: Release ID
        :param solution_id: Solution ID
        :param project_obj: Project object
        :return: Projects info (JSON)
        """
        _solution_id = 0
        _sql_script_id = 0
        _project_id = 0
        js = json.loads('{"projects":[]}')
        file = files_and_folders.Files(db_file_name)
        drm_db = file.load_file()
        for release in drm_db['releases']:
            if (release['id'] == int(release_id)):
                verified_release_id = release['id']
                if ("solutions" in release):
                    for solution in release['solutions']:
                        _solution_id += 1
                        if (int(solution_id) == _solution_id):
                            if ("projects" in solution):
                                for project in solution['projects']:
                                    _project_id += 1
                                    project_obj.id = _project_id    
                                    project_obj.name = project['name']     
                                    project_obj.solution_id = solution_id
                                    if ("ordinal" in project):    
                                        project_obj.ordinal = project['ordinal'] 
                                    else:
                                        project_obj.ordinal = _project_id
                                    project_obj.targets_compare_db = project['targets_compare_db']     
                                    project_obj.targets_type_id = project['targets_type_id']     
                                    if ("targets_list" in project):    
                                        project_obj.targets_list = project['targets_list'] 
                                    else:
                                        project_obj.targets_list = None
                                    if ("targets_sql_text" in project):
                                        _sql_script_id += 1
                                        project_obj.targets_sql_script_id = _sql_script_id    
                                        project_obj.targets_sql_text = project['targets_sql_text']    
                                    else:
                                        project_obj.targets_sql_script_id = None
                                        project_obj.targets_sql_text = None
                                    if ("max_degree_in_parallel" in project):   
                                        project_obj.max_degree_in_parallel = project['max_degree_in_parallel']
                                    else:
                                         project_obj.max_degree_in_parallel = None   
                                    if ("timeout_in_min" in project):   
                                        project_obj.timeout_in_min = project['timeout_in_min']
                                    else:
                                         project_obj.timeout_in_min = None   
                                    if ("sleep_time_in_sec" in project):   
                                        project_obj.sleep_time_in_sec = project['sleep_time_in_sec']
                                    else:
                                         project_obj.sleep_time_in_sec = None   
                                    if ("deployment_properties" in project):   
                                        project_obj.deployment_properties = project['deployment_properties']
                                    else:
                                         project_obj.deployment_properties = []  
                                    if ("fail_on_error" in project):   
                                        project_obj.fail_on_error = project['fail_on_error']
                                    else:
                                         project_obj.fail_on_error = True   
                                    if ("is_active" in project):   
                                        project_obj.is_active = project['is_active']
                                    else:
                                         project_obj.is_active = True   
                                    project_js = json.loads(json.dumps(project_obj.__dict__))
                                    js['projects'].append(project_js)
        return json.dumps(js)

