import os
import uuid
import json
import zipfile
import logging
import subprocess
import shutil
import concurrent.futures
from typing import Callable, List, Dict, Any
from queue import Queue
from pathlib import Path
from shutil import which
from datetime import datetime
from modules import drm_logger, files_and_folders, crypto, parser_sqlite_json
from modules import parser_json_json, sqlite, parser_json_sqlite, mssql

current_working_directory = Path(__file__).parent.parent.resolve()

#===========
# Constrants
#===========
DEPLOY_CONFIG_FILE_NAME = "drm_deploy.config"
DRM_SCHEM_JSON_FILE_NAME = "drm_db_schema.json"
BUILD_FILE_NAME = "drm_deploy.json"
PACK_FILE_NAME = "deploy.drmpac"
DRYRUN_MODE = "DryRun"
DEPLOY_MODE = "Deploy"
DEPLOY_DIR = "deployments"
DEPLOYMENT_PENDING_STATUS = "Pending"
DEPLOYMENT_IN_PROGRESS_STATUS = "In progress"
DEPLOYMENT_SUCCESS_STATUS = "Finished successfully"
DEPLOYMENT_CANCELED_STATUS = "Canceled"
DEPLOYMENT_FAILED_STATUS = "Failed"

class MsSql:

    logger = drm_logger.configure_logging("deploy.MsSql")

    @drm_logger.log_decorator(logger) 
    def __init__(self, deploy_config): 

        def get_location (self, app_name):
            if which(app_name) != None:
                return app_name
            app = "{app_name}.exe".format(app_name = app_name)
            if which(app) != None:
                return app
            # Not known --> search
            f = files_and_folders.Files(app_name)
            file_name = f.find_file_in_dir("/")
            if (file_name == None):
                f = files_and_folders.Files("{app_name}.exe".format(app_name = app_name))
                file_name = f.find_file_in_dir("/")
            if (file_name == None):
                raise ('{file_name} utility not found!!!'.format(file_name = file_name))
            else:
                return (file_name.replace("\\", "/"))


        js = deploy_config.full_config
        missing_object = False

        #============================
        # Identify SqlPackage utility
        #============================
        app_name = "sqlpackage"
        if hasattr(deploy_config, 'sqlpackage_path'):
            # Get utility location from configuration
            self.upgrade_tool_file_name = deploy_config.sqlpackage_path
        else:
            # Utility not configured --> serach
            missing_object = True
            self.logger.info("{app_name} utility path was not supplied in drm_deploy.config, searching (This may take a while)...".format(app_name = app_name))
            self.upgrade_tool_file_name = get_location (self, app_name)                    
            self.logger.info("{app_name} utility found & configured in drm_deploy.config for next deployments!!!".format(app_name = app_name))
            locations_js = json.loads('{"sqlpackage_path": "' + self.upgrade_tool_file_name + '"}')
            js['locations'].append(locations_js)

        app_name = "sqlcmd"
        if hasattr(deploy_config, 'sqlcmd_path'):
            # Get utility location from configuration
            self.run_script_tool_file_name = deploy_config.sqlcmd_path
        else:
            # Utility not configured --> serach
            missing_object = True
            self.logger.info("{app_name} utility path was not supplied in drm_deploy.config, searching (This may take a while)...".format(app_name = app_name))
            self.run_script_tool_file_name = get_location (self, app_name)                    
            self.logger.info("{app_name} utility found & configured in drm_deploy.config for next deployments!!!".format(app_name = app_name))
            locations_js = json.loads('{"sqlcmd_path": "' + self.run_script_tool_file_name + '"}')
            js['locations'].append(locations_js)

        if(missing_object):
            json_obj = json.dumps(js, indent=4)
            drm_config_file = os.path.join(current_working_directory, DEPLOY_CONFIG_FILE_NAME)
            file = files_and_folders.Files(drm_config_file)
            file.write_file(json_obj)

                

    @drm_logger.log_decorator(logger) 
    def get_list_of_targets(self, targets_type_id, targets_list, connection_string, targets_sql_text, targets_compare_db):
        """ 
        Returns a list of target databases to deploy into
        :param targets_type_id: targets type id (list or query)
        :param targets_list: targets json list
        :param targets_sql_text: SQL query which returns a list of targets
        :prams targets_compare_db: target compare database name
        :return: List of target databases (json)
        """ 
        try:
            def custom_sort_key(s):
                # Define a high priority for "a" to make it come last
                return (1, s) if s == targets_compare_db else (0, s)
            
            #==========
            # JSON list
            #==========
            if targets_type_id == 1:
                return sorted(json.loads(targets_list), key=custom_sort_key)
            #==========
            # SQL query
            #==========
            elif targets_type_id == 2:
                target_db_obj = mssql.MsSql(self.run_script_tool_file_name, connection_string)
                result = target_db_obj.execute_query(targets_sql_text)
                names = [entry["name"] for entry in json.loads(result)]
                return sorted(names, key=custom_sort_key)
        except Exception as e:            
            raise Exception (f"failed to get list of targets: {e}")
               

    @drm_logger.log_decorator(logger) 
    def get_source_file(self, solution_path, project_name):
        """ 
        returns the source file path 
        :param solution_path: solution path
        :param project_name: project_name
        :return: source file full path (String)
        """ 
        return os.path.join (solution_path, project_name, "bin", "Debug", project_name + ".dacpac")
               

    @drm_logger.log_decorator(logger) 
    def get_fixed_connection_string(self, connection_string, project_targets_compare_db):
        """ 
        returns the fixed connection string using compare DB
        :param connection_string: connection string from the solution
        :param project_targets_compare_db: database name to connect into
        :return: fixed conneciton string (String)
        """ 
        return connection_string + "Database={project_targets_compare_db};".format(project_targets_compare_db = project_targets_compare_db)
               
    @drm_logger.log_decorator(logger) 
    def generate_upgrade_script(self, deploy_file_base_name, solution_id, project_id, project_name, project_targets_compare_db, source_file, connection_string, deployment_properties):
        """ 
        returns the fixed connection string using compare DB
        :param deploy_file_base_name: file base name (prefix)
        :param solution_id: solution ID
        :param project_id: project ID
        :param project_name: project name
        :param project_targets_compare_db: target database name to compare with
        :param source_file: source file name (dacpac)
        :param connection_string: connection string
        :param deployment_properties: array of deployment properties
        :return: update script name (String)
        """ 
        # Define upgrade script file
        upgrade_script = os.path.join (current_working_directory, "bin", deploy_file_base_name + "_S" + str(solution_id) + "-P" + str(project_id) + "-" + project_name + "-" + project_targets_compare_db + ".sql")
        self.logger.info('Generating upgrade script "{upgrade_script}"...'.format(upgrade_script = upgrade_script))
        
        #================================
        # Builld subprocessarguments list
        #================================
        args_list = []
        # Utility
        args_list.append(self.upgrade_tool_file_name)
        # Generate script
        args_list.append("/Action:script")
        # Dacpac source file
        args_list.append("/SourceFile:" + source_file)
        # Target connection string
        args_list.append("/TargetConnectionString:" + connection_string)
        # Output log file
        args_list.append("/OutputPath:" + upgrade_script)
        # Deployment properties
        if (deployment_properties == None):
            deployment_properties = '[]'
        js_deployment_properties = json.loads(deployment_properties)
        for property in js_deployment_properties:
            args_list.append("/p:" + property)

        #=============================
        # Generate upgrade script file
        #=============================
        result = subprocess.run(args_list, capture_output=True)
        # Check if process exit with a failure
        if result.stderr:
            raise Exception (result.stderr)
        self.logger.info("Upgrade script generated successfully!!!")

        return upgrade_script
               
    @drm_logger.log_decorator(logger) 
    def run_upgrade_script(self, deploy_file_base_name, solution_id, project_id, project_name, target_name, upgrade_script, connection_string, sql_script_variables_list, project_fail_on_error):
        """ 
        returns the fixed connection string using compare DB
        :param semaphore: amount of parallel processes
        :param deploy_file_base_name: file base name (prefix)
        :param solution_id: solution ID
        :param project_id: project ID
        :param project_name: project name
        :param target_name: target database name
        :param upgrade_script: upgrade script name
        :param connection_string: connection string
        :param sql_script_variables_list: array of pairs of script variables (name, value)
        :param project_fail_on_error: fail the deploymet if at least one failed
        :return: update script name (String)
        """ 
        upgrade_log_file = os.path.join (current_working_directory, "log", deploy_file_base_name + "_S" + str(solution_id) + "-P" + str(project_id) + "-" + project_name + "-" + target_name + ".log")
        self.logger.info('Running upgrade script against "{target_name}" (log file: "{upgrade_log_file}")...'.format(target_name = target_name, upgrade_log_file = upgrade_log_file))
        
        db_obj = mssql.MsSql(self.run_script_tool_file_name, connection_string, target_name, sql_script_variables_list, upgrade_log_file)
        try:
            result = db_obj.run_script(upgrade_script)
            self.logger.info(f'Upgrade "{target_name}" finished successfully!!!')
            return result
        except Exception as e:
            if (project_fail_on_error):
                raise Exception(f'{e}')
            else:
                self.logger.warning(f'{e}')

class Deploy:

    logger = drm_logger.configure_logging("deploy.Deploy")

    @drm_logger.log_decorator(logger) 
    def __init__(self, deploy_config, encryption_key = False, execution_mode = DRYRUN_MODE): 
        self.deploy_config = deploy_config

        build_dir = os.path.join(current_working_directory, self.deploy_config.build_folder_name)
        pack_file_name = os.path.join(build_dir, PACK_FILE_NAME)
        
        #===============================================
        # Extract deploy plan from drmpac for validation
        #===============================================
        with zipfile.ZipFile(pack_file_name, 'r') as zip_ref:
            with zip_ref.open(BUILD_FILE_NAME) as json_file:
                self.release = json.load(json_file)
                zip_ref.close()

        self.encryption_key = encryption_key
        self.execution_mode = execution_mode
        self.schema_file_name = os.path.join(current_working_directory, deploy_config.db_folder_name, DRM_SCHEM_JSON_FILE_NAME)
        self.schema_parser = parser_json_json

        #=====================================
        # Get DB & parser by installation type       
        #=====================================
        # SQLite to JSON
        if (deploy_config.installation_type == "sqlite"):
            self.parser = parser_sqlite_json
            self.db_parser = parser_json_sqlite.ParserJsonSqlite()
            self.db_file_name = os.path.join(current_working_directory, deploy_config.db_folder_name, deploy_config.db_file_name + "." + deploy_config.sqlite_file_ext)
        # JSON to JSON
        else:
            self.parser = parser_json_json
            self.db_file_name = os.path.join(current_working_directory, deploy_config.db_folder_name, deploy_config.db_file_name + "." + deploy_config.data_file_ext)


    @drm_logger.log_decorator(logger) 
    def copy_deploy_to_sqlite(self,deployment_js):
        """ 
        Copy deploy results into Sqlite
        :return:
        """ 
		#================
		# Create Database
		#================
        conn = sqlite.create_connection(self.db_file_name)

        #==================
        # Insert deployment
        #==================
        table_name = "deployments"
        columns = []
        values = []
        deployments_columns_list = self.schema_parser.Generic.get_table_columns_list(self.schema_file_name, table_name)
        for deployment_column_name in json.loads(deployments_columns_list):
            if (deployment_js[deployment_column_name] != None):
                columns.append(deployment_column_name)
                values.append(deployment_js[deployment_column_name])
                if (deployment_column_name) == "id":
                    deployment_id = deployment_js[deployment_column_name]
        if len(columns) != 0:
            sql_command = self.db_parser.insert_row(table_name, columns, values)
            sqlite.execute_command(conn, sql_command)

            #========================
            # Insert deployment_tries
            #========================
            table_name = "deployments_tries"
            if table_name in deployment_js:
                deployments_tries_columns_list = self.schema_parser.Generic.get_table_columns_list(self.schema_file_name, table_name)
                for deployment_try_js in deployment_js[table_name]:
                    columns = []
                    values = []
                    for deployment_try_column_name in json.loads(deployments_tries_columns_list):
                        if(deployment_try_column_name == "deployment_id"):
                            columns.append(deployment_try_column_name)
                            values.append(deployment_id)
                        else:
                            if (deployment_try_js[deployment_try_column_name] != None):
                                columns.append(deployment_try_column_name)
                                values.append(deployment_try_js[deployment_try_column_name])
                                if (deployment_try_column_name == "id"):
                                    deployment_try_id = deployment_try_js[deployment_try_column_name]
                    if len(columns) != 0:
                        sql_command = self.db_parser.insert_row(table_name, columns, values)
                        sqlite.execute_command(conn, sql_command)

                        #============================
                        # Insert deployment_solutions
                        #============================
                        table_name = "deployments_solutions"
                        if table_name in deployment_try_js:
                            deployments_solutions_columns_list = self.schema_parser.Generic.get_table_columns_list(self.schema_file_name, table_name)
                            for deployment_solution_js in deployment_try_js[table_name]:
                                columns = []
                                values = []
                                for deployment_solution_column_name in json.loads(deployments_solutions_columns_list):
                                    if(deployment_solution_column_name == "deployment_try_id"):
                                        columns.append(deployment_solution_column_name)
                                        values.append(deployment_try_id)
                                    else:
                                        if (deployment_solution_js[deployment_solution_column_name] != None):
                                            columns.append(deployment_solution_column_name)
                                            values.append(deployment_solution_js[deployment_solution_column_name])
                                            if (deployment_solution_column_name == "id"):
                                                deployment_solution_id = deployment_solution_js[deployment_solution_column_name]
                                if len(columns) != 0:
                                    sql_command = self.db_parser.insert_row(table_name, columns, values)
                                    sqlite.execute_command(conn, sql_command)

                                    #===========================
                                    # Insert deployment_projects
                                    #===========================
                                    table_name = "deployments_projects"
                                    if table_name in deployment_solution_js:
                                        deployments_projects_columns_list = self.schema_parser.Generic.get_table_columns_list(self.schema_file_name, table_name)
                                        for deployment_project_js in deployment_solution_js[table_name]:
                                            columns = []
                                            values = []
                                            insert_record = True
                                            for deployment_project_column_name in json.loads(deployments_projects_columns_list):
                                                if(deployment_project_column_name == "deployment_solution_id"):
                                                    columns.append(deployment_project_column_name)
                                                    values.append(deployment_solution_id)
                                                else:
                                                    if (deployment_project_js[deployment_project_column_name] != None):
                                                        columns.append(deployment_project_column_name)
                                                        values.append(deployment_project_js[deployment_project_column_name])
                                                if (deployment_project_column_name == "start_time" and deployment_project_js[deployment_project_column_name] == None):
                                                    insert_record = False
                                            if len(columns) != 0 and insert_record:
                                                sql_command = self.db_parser.insert_row(table_name, columns, values)
                                                sqlite.execute_command(conn, sql_command)


    @drm_logger.log_decorator(logger) 
    def deploy_release(self):
        """ 
        Deploy release
        :return:
        """ 
        try:
            deployment_id = uuid.uuid4()
            deploy_file_base_name = "{execution_mode}_{deployment_id}".format(execution_mode = self.execution_mode, deployment_id = deployment_id)
            try_num = 0
            deployment_started = False
            
            #=================
            # Get release info  
            #=================
            js_release = self.release
            release_id = js_release['id']
            release_name = js_release['name']
            if "max_retries" in js_release:
                release_max_retries = js_release['max_retries']
            else:
                release_max_retries = 0

            deploy_file_base_name = "{execution_mode}_{deployment_id}_R{release_id}".format(execution_mode = self.execution_mode, deployment_id = deployment_id, release_id = release_id)
            deploy_log_file_name = "{deploy_file_base_name}.json".format(deploy_file_base_name = deploy_file_base_name)
            deploy_dir = os.path.join(current_working_directory, DEPLOY_DIR)
            if (self.deploy_config.installation_type == "json") and not(os.path.exists(deploy_dir)):
                os.mkdir(deploy_dir)
            build_dir = os.path.join(current_working_directory, self.deploy_config.build_folder_name)
            deployment_file = files_and_folders.Files(os.path.join(build_dir, deploy_log_file_name))

            deployment_js = {}
            deployments_columns_list = self.schema_parser.Generic.get_table_columns_list(self.schema_file_name, "deployments")
            for deployment_column_name in json.loads(deployments_columns_list):
                if (deployment_column_name == "id"):
                    deployment_js[deployment_column_name] = str(deployment_id)
                elif (deployment_column_name == "release_id"):
                    deployment_js[deployment_column_name] = release_id
                    deployment_js["release_name"] = release_name
                elif (deployment_column_name == "user_id"):
                    deployment_js[deployment_column_name] = 1
                elif (deployment_column_name == "deployment_type_id"):
                    if (self.execution_mode == DEPLOY_MODE):
                        deployment_js[deployment_column_name] = 2
                    else:
                        deployment_js[deployment_column_name] = 1
                    deployment_js["deployment_type_name"] = self.execution_mode
                elif (deployment_column_name == "start_time"):
                    deployment_js[deployment_column_name] = datetime.now().isoformat()
                elif (deployment_column_name == "end_time"):
                    deployment_js[deployment_column_name] = None
                elif (deployment_column_name == "deployment_status_id"):
                    deployment_js[deployment_column_name] = 1
                    deployment_js["deployment_status_name"] = DEPLOYMENT_IN_PROGRESS_STATUS
                elif (deployment_column_name == "error_message"):
                    deployment_js[deployment_column_name] = None
            deployment_js["max_retries"] = release_max_retries
            deployment_js["deployments_tries"] = []
            deployment_file.write_file(json.dumps(deployment_js, indent=7))
            
            try_num += 1
            deployment_js = deployment_file.load_file()
            deployment_try_js = {}
            deployments_tries_columns_list = self.schema_parser.Generic.get_table_columns_list(self.schema_file_name, "deployments_tries")
            for deployment_try_column_name in json.loads(deployments_tries_columns_list):
                if (deployment_try_column_name == "id"):
                    deployment_try_js[deployment_try_column_name] = str(uuid.uuid4())
                elif (deployment_try_column_name == "try_num"):
                    deployment_try_js[deployment_try_column_name] = try_num
                elif (deployment_try_column_name == "start_time"):
                    deployment_try_js[deployment_try_column_name] = datetime.now().isoformat()
                elif (deployment_try_column_name == "end_time"):
                    deployment_try_js[deployment_try_column_name] = None
                elif (deployment_try_column_name == "error_message"):
                    deployment_try_js[deployment_try_column_name] = None
                elif (deployment_try_column_name == "deployment_status_id"):
                    deployment_try_js[deployment_try_column_name] = 1
                    deployment_try_js["deployment_status_name"] = DEPLOYMENT_IN_PROGRESS_STATUS

            deployment_try_js["deployments_solutions"] = []        
            #=====================
            # Get active solutions  
            #=====================
            for js_solution in js_release['solutions']:
                if "is_active" in js_solution:
                    solution_is_active = js_solution['is_active']
                else:
                    solution_is_active = 1
                
                if (solution_is_active):
                    #==================
                    # Get solution info
                    #==================
                    solution_id = js_solution['id']
                    solution_name = js_solution['name']
                    solution_type_id = js_solution['solution_type_id']
                    solution_path = js_solution['path']

                    deployment_solution_js = {}
                    deployments_solutions_columns_list = self.schema_parser.Generic.get_table_columns_list(self.schema_file_name, "deployments_solutions")
                    for deployment_solution_column_name in json.loads(deployments_solutions_columns_list):
                        if (deployment_solution_column_name == "id"):
                            deployment_solution_js[deployment_solution_column_name] = str(uuid.uuid4())
                        elif (deployment_solution_column_name == "solution_id"):
                            deployment_solution_js[deployment_solution_column_name] = solution_id
                            deployment_solution_js["solution_name"] = solution_name
                        elif (deployment_solution_column_name == "start_time"):
                            deployment_solution_js[deployment_solution_column_name] = datetime.now().isoformat()
                        elif (deployment_solution_column_name == "end_time"):
                            deployment_solution_js[deployment_solution_column_name] = None
                        elif (deployment_solution_column_name == "error_message"):
                            deployment_solution_js[deployment_solution_column_name] = None
                    

                    if (solution_type_id == 1): #mssql
                        solution_obj = MsSql(self.deploy_config)

                    #====================
                    # Get connection info
                    #====================
                    for js_connection in js_solution['connections']:
                        connection_id = js_connection['id']
                        connection_name = js_connection['name']
                        connection_type_id = js_connection['connection_type_id']
                        connection_string = js_connection['connection_string']
                        if self.deploy_config.db_secured:
                            crpt = crypto.Crypto(self.encryption_key)
                            connection_string = crpt.decrypt_string(connection_string)

                    #=========================
                    # Get SQL script variables
                    #=========================
                    sql_script_variables_list = []
                    if "sql_scripts_variables" in js_solution:
                        for js_sql_script_variable in js_solution['sql_scripts_variables']:
                            sql_script_variables_list.append((js_sql_script_variable['name'], js_sql_script_variable['value']))

                    deployment_solution_js["deployments_projects"] = []
                    #====================
                    # Get active projects
                    #====================
                    for js_project in js_solution['projects']:
                        if "is_active" in js_project:
                            project_is_active = js_project['is_active']
                        else:
                            project_is_active = 1

                        if (project_is_active):
                            #=================
                            # Get project info
                            #=================
                            deployment_started = False
                            project_id = js_project['id']
                            project_name = js_project['name']
                            project_targets_compare_db = js_project['targets_compare_db']
                            project_targets_type_id = js_project['targets_type_id']
                            project_targets_list = js_project['targets_list']
                            project_targets_sql_script_id = js_project['targets_sql_script_id']
                            project_targets_sql_text = js_project['targets_sql_text']
                            project_max_degree_in_parallel = js_project['max_degree_in_parallel']
                            project_timeout_in_min = js_project['timeout_in_min']
                            project_sleep_time_in_sec = js_project['sleep_time_in_sec']
                            project_deployment_properties = js_project['deployment_properties']
                            project_fail_on_error = js_project['fail_on_error']

                            deployments_projects_columns_list = self.schema_parser.Generic.get_table_columns_list(self.schema_file_name, "deployments_projects")

                            #========================
                            # Generate upgrade script
                            #========================
                            source_file = solution_obj.get_source_file(solution_path, project_name)
                            target_connection_string = solution_obj.get_fixed_connection_string(connection_string, project_targets_compare_db)                                              
                            if (self.execution_mode == DRYRUN_MODE):
                                deployment_project_js = {}
                                for deployment_project_column_name in json.loads(deployments_projects_columns_list):
                                    if (deployment_project_column_name == "id"):
                                        deployment_project_js[deployment_project_column_name] = str(uuid.uuid4())
                                    elif (deployment_project_column_name == "project_id"):
                                        deployment_project_js[deployment_project_column_name] = project_id
                                        deployment_project_js["project_name"] = project_name
                                    elif (deployment_project_column_name == "target_database_name"):
                                        deployment_project_js[deployment_project_column_name] = project_targets_compare_db
                                    elif (deployment_project_column_name == "start_time"):
                                        deployment_project_js[deployment_project_column_name] = datetime.now().isoformat()
                                    elif (deployment_project_column_name == "end_time"):
                                        deployment_project_js[deployment_project_column_name] = None
                                    elif (deployment_project_column_name == "error_message"):
                                        deployment_project_js[deployment_project_column_name] = None
                            
                            upgrade_script = solution_obj.generate_upgrade_script(deploy_file_base_name, solution_id, project_id, project_name, project_targets_compare_db, source_file, target_connection_string, project_deployment_properties)
                            
                            if (self.execution_mode == DRYRUN_MODE):
                                deployment_project_js["end_time"] = datetime.now().isoformat()
                                deployment_solution_js["deployments_projects"].append(deployment_project_js)

                            #================================
                            # Deploy mode (Not a DryRun mode)
                            #================================
                            if (self.execution_mode == DEPLOY_MODE):
                                if project_max_degree_in_parallel == None:
                                    project_max_degree_in_parallel = 1
                                tasks = []
                                # Get list targets
                                targets_list_js = solution_obj.get_list_of_targets(project_targets_type_id, project_targets_list, target_connection_string, project_targets_sql_text, project_targets_compare_db)
                                for target_db in targets_list_js:  
                                    tasks.append({"target_db": target_db})
                                
                                task_statuses = {task["target_db"]: {"status_id": "0", "status_name": DEPLOYMENT_PENDING_STATUS, "start_time": None, "end_time": None, "error_message": None} for task in tasks}
                                task_queue = Queue()
                                for task in tasks:
                                    task_queue.put(task)

                                failed = False

                                def task_wrapper(task: Dict[str, Any]) -> None:
                                    target_db = task["target_db"]
                                    try:
                                        deployment_started = True
                                        task_statuses[target_db]["start_time"] = datetime.now().isoformat()
                                        result = solution_obj.run_upgrade_script(deploy_file_base_name, solution_id, project_id, project_name, target_db, upgrade_script, target_connection_string, sql_script_variables_list, project_fail_on_error)
                                        task_statuses[target_db]["status_id"] = 2
                                        task_statuses[target_db]["status_name"] = DEPLOYMENT_SUCCESS_STATUS
                                    except Exception as e:
                                        task_statuses[target_db]["status_id"] = 4
                                        task_statuses[target_db]["status_name"] = DEPLOYMENT_FAILED_STATUS
                                        task_statuses[target_db]["error_message"] = f"{str(e)}"
                                        nonlocal failed
                                        failed = True
                                    finally:
                                        task_statuses[target_db]["end_time"] = datetime.now().isoformat()

                                with concurrent.futures.ThreadPoolExecutor(max_workers=project_max_degree_in_parallel) as executor:
                                    futures = []
                                    for _ in range(project_max_degree_in_parallel):
                                        if not task_queue.empty():
                                            task = task_queue.get()
                                            futures.append(executor.submit(task_wrapper, task))

                                    while futures:
                                        done, _ = concurrent.futures.wait(futures, return_when=concurrent.futures.FIRST_COMPLETED)
                                        for future in done:
                                            futures.remove(future)
                                            future.result()  # Re-raise exceptions if any

                                        if failed and project_fail_on_error:
                                            break

                                        if not task_queue.empty() and not (failed and project_fail_on_error):
                                            task = task_queue.get()
                                            futures.append(executor.submit(task_wrapper, task))

                                # Mark remaining tasks as not started if there was a failure and project_fail_on_error is True
                                if project_fail_on_error and failed:
                                    while not task_queue.empty():
                                        task = task_queue.get()
                                        task_statuses[task["target_db"]]["status_id"] = 0
                                        task_statuses[task["target_db"]]["status_name"] = DEPLOYMENT_PENDING_STATUS
                                    raise Exception ('One or more projects deployment failed.')

                                for task in task_statuses:
                                    deployment_project_js = {}
                                    for deployment_project_column_name in json.loads(deployments_projects_columns_list):
                                        if (deployment_project_column_name == "id"):
                                            deployment_project_js[deployment_project_column_name] = str(uuid.uuid4())
                                        elif (deployment_project_column_name == "project_id"):
                                            deployment_project_js[deployment_project_column_name] = project_id
                                            deployment_project_js["project_name"] = project_name
                                        elif (deployment_project_column_name == "target_database_name"):
                                            deployment_project_js[deployment_project_column_name] = task
                                        elif (deployment_project_column_name == "start_time"):
                                            deployment_project_js[deployment_project_column_name] = task_statuses[task]['start_time']
                                        elif (deployment_project_column_name == "end_time"):
                                            deployment_project_js[deployment_project_column_name] = task_statuses[task]['end_time']
                                        elif (deployment_project_column_name == "error_message"):
                                            deployment_project_js[deployment_project_column_name] = task_statuses[task]['error_message']
                                    deployment_solution_js["deployments_projects"].append(deployment_project_js)


                    deployment_solution_js["end_time"] = datetime.now().isoformat()
            
            deployment_try_js["deployments_solutions"].append(deployment_solution_js)
            deployment_try_js["deployment_status_id"] = 2
            deployment_try_js["deployment_status_name"] = DEPLOYMENT_SUCCESS_STATUS
            deployment_try_js["end_time"] = datetime.now().isoformat()



            deployment_js["deployments_tries"].append(deployment_try_js)
            deployment_js["deployment_status_id"] = 2
            deployment_js["deployment_status_name"] = DEPLOYMENT_SUCCESS_STATUS
            deployment_js["end_time"] = datetime.now().isoformat()
            deployment_file.write_file(json.dumps(deployment_js, indent=7))
    
            if (self.deploy_config.installation_type == "sqlite"):
                self.copy_deploy_to_sqlite(deployment_js)
            else:
                deployment_file_build_name = os.path.join(build_dir, deploy_log_file_name)
                deployment_file_deply_name = os.path.join(deploy_dir, deploy_log_file_name)                
                shutil.copy(deployment_file_build_name, deployment_file_deply_name)

        except Exception as e:            
            if (deployment_started):
                for task in task_statuses:
                    deployment_project_js = {}
                    for deployment_project_column_name in json.loads(deployments_projects_columns_list):
                        if (deployment_project_column_name == "id"):
                            deployment_project_js[deployment_project_column_name] = str(uuid.uuid4())
                        elif (deployment_project_column_name == "project_id"):
                            deployment_project_js[deployment_project_column_name] = project_id
                            deployment_project_js["project_name"] = project_name
                        elif (deployment_project_column_name == "target_database_name"):
                            deployment_project_js[deployment_project_column_name] = task
                        elif (deployment_project_column_name == "start_time"):
                            deployment_project_js[deployment_project_column_name] = task_statuses[task]['start_time']
                        elif (deployment_project_column_name == "end_time"):
                            deployment_project_js[deployment_project_column_name] = task_statuses[task]['end_time']
                        elif (deployment_project_column_name == "error_message"):
                            deployment_project_js[deployment_project_column_name] = task_statuses[task]['error_message']
                    deployment_solution_js["deployments_projects"].append(deployment_project_js)

                deployment_solution_js["error_message"] = f"{e}"
                deployment_solution_js["end_time"] = datetime.now().isoformat()           
                deployment_try_js["deployments_solutions"].append(deployment_solution_js)
                deployment_try_js["deployment_status_id"] = 4
                deployment_try_js["deployment_status_name"] = DEPLOYMENT_FAILED_STATUS
                deployment_try_js["error_message"] = f"{e}"
                deployment_try_js["end_time"] = datetime.now().isoformat()
                deployment_js["deployments_tries"].append(deployment_try_js)
                deployment_js["deployment_status_id"] = 4
                deployment_js["deployment_status_name"] = DEPLOYMENT_FAILED_STATUS
                deployment_js["error_message"] = f"{e}"
                deployment_js["end_time"] = datetime.now().isoformat()
                deployment_file.write_file(json.dumps(deployment_js, indent=7))
                if (self.deploy_config.installation_type == "sqlite"):
                    self.copy_deploy_to_sqlite(deployment_js)
                    raise Exception (f'{e}, see detains in DRM database, Deployment ID {deployment_id}')
                else:
                    deployment_file_build_name = os.path.join(build_dir, deploy_log_file_name)
                    deployment_file_deply_name = os.path.join(deploy_dir, deploy_log_file_name)                
                    shutil.copy(deployment_file_build_name, deployment_file_deply_name)
                    raise Exception (f'{e}, see detains in "{deployment_file_deply_name}"')
            else:
                raise Exception (f'{e}')
        