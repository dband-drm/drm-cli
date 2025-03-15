import sys
import json
import logging
import glob
import os
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

    @drm_logger.log_decorator(logger) 
    def compare_columns(target_columns, source_columns):
        
        actions = []

        # Get columns names in source & target tables
        target_column_names = {col['name'] for col in target_columns}
        source_column_names = {col['name'] for col in source_columns}

        # Check for updates and additions in columns
        for source_col in source_columns:
            if source_col['name'] in target_column_names:
                # Find the corresponding column in the target to compare
                target_col = next(col for col in target_columns if col['name'] == source_col['name'])
                if source_col != target_col:
                    # If there's a difference, mark as update
                    source_col['action'] = 'upd'
                    actions.append(source_col)
            else:
                # If column is not in the target, it's an addition
                source_col['action'] = 'add'
                actions.append(source_col)

        for target_col in target_columns:
            if target_col['name'] not in source_column_names:
                target_col['action'] = 'del'
                actions.append(target_col)

        return actions

    @drm_logger.log_decorator(logger) 
    def compare_constraints(target_constraints, source_constraints):

        actions = []

        # Get columns names in source & target tables
        target_constraint_names = {constraint['name'] for constraint in target_constraints}
        source_constraint_names = {constraint['name'] for constraint in source_constraints}

        # Check for updates and additions in constraints
        for source_constraint in source_constraints:
            if source_constraint['name'] in target_constraint_names:
                # Find the corresponding constraint in the target to compare
                target_constraint = next(constraint for constraint in target_constraints if constraint['name'] == source_constraint['name'])
                if source_constraint != target_constraint:
                    # If there's a difference, mark as update
                    source_constraint['action'] = 'upd'
                    actions.append(source_constraint)
            else:
                # If constraint is not in the target, it's an addition
                source_constraint['action'] = 'add'
                actions.append(source_constraint)

        for target_constraint in target_constraints:
            if target_constraint['name'] not in source_constraint_names:
                target_constraint['action'] = 'del'
                actions.append(target_constraint)

        return actions

    @drm_logger.log_decorator(logger) 
    def compare_tables(target_table, source_table):
        
        changes_js = {}
        #================
        # Compare columns
        #================
        change = Generic.compare_columns(target_table['columns'], source_table['columns'])
        if (change):
            changes_js['columns'] = change
        #====================
        # Compare constraints
        #====================
        change = Generic.compare_constraints(target_table['constraints'], source_table['constraints'])
        if (change):
            changes_js['constraints'] = change
        
        return changes_js


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

class Deployments:

    logger = drm_logger.configure_logging("parser_json_json.Deployments")

    DEPLOYMENT_PENDING_STATUS = "Pending"
    DEPLOYMENT_IN_PROGRESS_STATUS = "In progress"
    DEPLOYMENT_SUCCESS_STATUS = "Finished successfully"
    DEPLOYMENT_CANCELED_STATUS = "Canceled"
    DEPLOYMENT_FAILED_STATUS = "Failed"
    DEPLOYMENT_ALREADY_DEPLOYED_STATUS = "Already deployed"

    @drm_logger.log_decorator(logger) 
    def __init__(self, release_id, connection, execution_mode, deploy_dir, db_file_name = None): 
        """ 
        :param release_id: Release ID
        :param connection: Connection name
        :param execution_mode: Execution mode
        :param deploy_dir: Directory of all deployments files
        :param db_file_name: DRM database file name (Not in use)
        :return:
        """
        file_pattern = f"{execution_mode}_*_C{connection}_R{release_id}.json"
        search_pattern = os.path.join(deploy_dir, file_pattern)
        list_of_files = glob.glob(search_pattern)
        
        if not list_of_files:
            self.latest_deployment_file = None
    
        else:
            # Sort files by creation time (most recent first)
            list_of_files.sort(key=lambda x: os.path.getctime(x), reverse=True)
    
            # Return the most recent file
            self.latest_deployment_file = list_of_files[0]

    @drm_logger.log_decorator(logger) 
    def get_last_deployment_restuls(self, solution_id, project_id, targets_list_js): 
        """ 
        Return last deployment results for each target database
        :param targets_list_js: List of target databases
        :return: Last failed deployment ID (Integer) & List of target databases followed by deployment status (JSON)
        """
        task_statuses = {}
        last_deployment_id = None
        deployment_status_id = None
        
        if (self.latest_deployment_file != None):
            #=============================
            # Check last deployment status
            #=============================
            file = files_and_folders.Files(self.latest_deployment_file)
            deployment_js = file.load_file()
            if ('deployment_status_id' in deployment_js):
                deployment_status_id = deployment_js['deployment_status_id']
            
            #========================================================================================
            # If last deployment did not fully succeeded --> get last status for each target database
            #========================================================================================
            if (deployment_status_id != 2):
                
                last_deployment_id = deployment_js['id']
                
                # Search against all tries
                for deployment_try_js in deployment_js['deployments_tries']:
                    
                    # Search against all solutions of try
                    for deployment_solution_js in deployment_try_js['deployments_solutions']:
                        
                        # If solution match --> get results
                        if (deployment_solution_js['solution_id'] == solution_id):
                            
                            # Search against all projects of the solution
                            for deployment_project_js in deployment_solution_js['deployments_projects']:
                                
                                # If project match --> get results
                                if (deployment_project_js['project_id'] == project_id):
                                    
                                    # Get target databases results
                                    for target_db in targets_list_js:
                                        if(deployment_project_js['target_database_name'] == target_db):
                                            task_statuses[target_db] = {"status_id": deployment_project_js['deployment_status_id'], "status_name": deployment_project_js['deployment_status_name'], "start_time": deployment_project_js['start_time'], "end_time": deployment_project_js['end_time'], "error_message": None}
            
                # mark all other rest pending target databases
                for target_db in targets_list_js:
                    if target_db not in task_statuses:
                        task_statuses[target_db] = {"status_id": 0, "status_name": Deployments.DEPLOYMENT_PENDING_STATUS, "start_time": None, "end_time": None, "error_message": None}
                        
        return last_deployment_id, task_statuses
class ChangePassword:
    
    logger = drm_logger.configure_logging("parser_json_json.ChangePassword")

    @drm_logger.log_decorator(logger) 
    def __init__(self, db_file_name = "",encryption_key = "",new_encryption_key = ""):   
        """ 
        Constructor
        :param db_file_name:  databae name
        :param encryption_key: encryption_key
        :param new_encryption_key: new_encryption_key
        :return:
        """
        self.db_file_name = db_file_name
        self.encryption_key = encryption_key
        self.new_encryption_key = new_encryption_key

    @drm_logger.log_decorator(logger)     
    def execute_command(self):
        """ 
        Run ChangePassword command 
        :return: result
        """
        db_file_name = self.db_file_name

        file = files_and_folders.Files(db_file_name)
        drm_db_json = file.load_file()
        self.update_connection_strings(drm_db_json)
        json_obj = json.dumps(drm_db_json, indent=4)
        file.write_file(json_obj)


    def update_connection_strings(self,data):
        """ 
        Update_connection_strings
        :return:
        """ 
        from modules import crypto

        crpt = crypto.Crypto(self.encryption_key)
        crpt_new = crypto.Crypto(self.new_encryption_key)

        if isinstance(data, dict):
            for key, value in data.items():
                if key == "connections":#"connection_string":
                 conn = value
                 for item in conn:
                    for key, value in item.items():
                        if key == "connection_string":
                            
                            #verify encyption key
                            if (self.encryption_key != None and self.new_encryption_key != None):
                                value_ = crpt_new.encrypt_string( crpt.decrypt_string(value))
                            elif (self.encryption_key == None and self.new_encryption_key != None):
                                value_ = crpt_new.encrypt_string( value)
                            elif (self.new_encryption_key == None and self.encryption_key != None):
                                value_ = crpt.decrypt_string(value)
                            else:
                                raise Exception('Failed ChangePassword, No Encyption keys supplied')
                            item[key] = value_
                       # data[key] = crpt_new.encrypt_string( crpt.decrypt_string(value))
            else:
                self.update_connection_strings(value)
        elif isinstance(data, list):
            for item in data:
                self.update_connection_strings(item)
