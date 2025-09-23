import os
import sys
import uuid
import json
import zipfile
import logging
import subprocess
import shutil
import concurrent.futures
import re
from typing import Callable, List, Dict, Any
from queue import Queue
from pathlib import Path
from shutil import which
from datetime import datetime
from modules import drm_logger, files_and_folders, crypto, parser_sqlite_json
from modules import parser_json_json, sqlite, parser_json_sqlite, liquibase, flyway, sqlpackage

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
ALIGN_MODE = "Align"
DEPLOY_DIR = "deployments"
DEPLOYMENT_PENDING_STATUS = "Pending"
DEPLOYMENT_IN_PROGRESS_STATUS = "In progress"
DEPLOYMENT_SUCCESS_STATUS = "Finished successfully"
DEPLOYMENT_CANCELED_STATUS = "Canceled"
DEPLOYMENT_FAILED_STATUS = "Failed"
DEPLOYMENT_ALREADY_DEPLOYED_STATUS = "Already deployed"

class Deploy:

    logger = drm_logger.configure_logging("deploy.Deploy")

    @drm_logger.log_decorator(logger) 
    def __init__(self, deploy_config, encryption_key = False, execution_mode = DRYRUN_MODE, connection = None): 
        self.deploy_config = deploy_config

        self.connection = connection

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

        self.default_data_path = None
        self.default_log_path = None 
        
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
                    table_name = "deployments_tries"
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
                                table_name = "deployments_solutions"
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
                                            table_name = "deployments_projects"
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
    def generate_deployment_json(self, release_id, release_name, release_max_retries, deployment_id):
        """ 
        Generates deployment json
        :param release_id: Release ID
        :param release_name: Release name
        :param release_max_retries: Max number of retries
        :param deployment_id: Deployment ID
        :return: json
        """
        deployment_js = {}
        deployments_columns_list = self.schema_parser.Generic.get_table_columns_list(self.schema_file_name, "deployments")
        for deployment_column_name in json.loads(deployments_columns_list):
            if (deployment_column_name == "id"):
                deployment_js[deployment_column_name] = str(deployment_id)
            elif (deployment_column_name == "release_id"):
                deployment_js[deployment_column_name] = release_id
                deployment_js["release_name"] = release_name
            elif (deployment_column_name == "connection_id"):
                deployment_js[deployment_column_name] = None
                deployment_js["connection_name"] = None
            elif (deployment_column_name == "user_id"):
                deployment_js[deployment_column_name] = 1
            elif (deployment_column_name == "deployment_type_id"):
                if (self.execution_mode in (DEPLOY_MODE, ALIGN_MODE)):
                    deployment_js[deployment_column_name] = 2
                else:
                    deployment_js[deployment_column_name] = 1
                deployment_js["deployment_type_name"] = self.execution_mode
            elif (deployment_column_name == "start_time"):
                deployment_js[deployment_column_name] = datetime.now().isoformat()
            elif (deployment_column_name == "end_time"):
                deployment_js[deployment_column_name] = None
            elif (deployment_column_name == "error_message"):
                deployment_js[deployment_column_name] = None
            elif (deployment_column_name == "deployment_status_id"):
                deployment_js[deployment_column_name] = 1
                deployment_js["deployment_status_name"] = DEPLOYMENT_IN_PROGRESS_STATUS
        deployment_js["max_retries"] = release_max_retries
        deployment_js["deployments_tries"] = []
        
        return (deployment_js)

    @drm_logger.log_decorator(logger) 
    def generate_try_json(self, try_num):
        """ 
        Generates try json
        :param try_num: Try number
        :return: json
        """
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

        return (deployment_try_js)

    @drm_logger.log_decorator(logger) 
    def generate_solution_json(self, solution_id, solution_name):
        """ 
        Generates solution json
        :param solution_id: Solution ID
        :param solution_name: Solution name
        :return: json
        """
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
            elif (deployment_solution_column_name == "deployment_status_id"):
                deployment_solution_js[deployment_solution_column_name] = 1
                deployment_solution_js["deployment_status_name"] = DEPLOYMENT_IN_PROGRESS_STATUS
        
        deployment_solution_js["deployments_projects"] = []
        
        return (deployment_solution_js)

    @drm_logger.log_decorator(logger) 
    def get_last_deployment_statuses(self, release_id, solution_id, project_id, targets_list_js, deploy_dir, db_file_name):
        """ 
        Get last deployment statuses results
        :param release_id: Release ID
        :param solution_id: Solution ID
        :param project_id: Project ID
        :param targets_list_js: List of target databases
        :param deploy_dir: Deployments directory
        :return: json
        """
        task_statuses = {}
        last_deployment_id = None
        
        deployment_obj = self.parser.Deployments(release_id, self.connection, self.execution_mode, deploy_dir, db_file_name)
        last_deployment_id, task_statuses = deployment_obj.get_last_deployment_restuls (solution_id, project_id, targets_list_js)
        
        if (last_deployment_id != None):
            self.logger.info(f'Continue last failed deployment ID "{last_deployment_id}"')

        return task_statuses

    @drm_logger.log_decorator(logger) 
    def generate_project_json(self, project_id, project_name):
        """ 
        Generates project json
        :param project_id: Project ID
        :param project_name: Project name
        :return: json
        """
        deployments_projects_columns_list = self.schema_parser.Generic.get_table_columns_list(self.schema_file_name, "deployments_projects")
        deployment_project_js = {}
        for deployment_project_column_name in json.loads(deployments_projects_columns_list):
            if (deployment_project_column_name == "id"):
                deployment_project_js[deployment_project_column_name] = str(uuid.uuid4())
            elif (deployment_project_column_name == "project_id"):
                deployment_project_js[deployment_project_column_name] = project_id
                deployment_project_js["project_name"] = project_name
            elif (deployment_project_column_name == "target_database_name"):
                deployment_project_js[deployment_project_column_name] = None
            elif (deployment_project_column_name == "start_time"):
                deployment_project_js[deployment_project_column_name] = None
            elif (deployment_project_column_name == "end_time"):
                deployment_project_js[deployment_project_column_name] = None
            elif (deployment_project_column_name == "error_message"):
                deployment_project_js[deployment_project_column_name] = None
            elif (deployment_project_column_name == "deployment_status_id"):
                deployment_project_js[deployment_project_column_name] = 1
                deployment_project_js["deployment_status_name"] = DEPLOYMENT_IN_PROGRESS_STATUS
        
        return (deployment_project_js)

    @drm_logger.log_decorator(logger) 
    def update_update_scrip(self,upgrade_script,prepost_scripts,connection_type_id):
        
        """ 
        Update script with pre post scripts by Connection Type ID
        :param upgrade_script:      Upgrade Script
        :param prepost_scripts:     Pprepost Scripts
        :param connection_type_id:  Connection Type ID
        :return: none
        """ 

        #=============================
        # Modify upgrade script with pre-post script file
        #=============================
        if(prepost_scripts):
            file = files_and_folders.Files(upgrade_script)
            for  prepost_script_obj in  prepost_scripts:
                prepost_script_active = prepost_script_obj['is_active']
                prepost_script_type_id = prepost_script_obj['script_type_id']
                prepost_script_path = prepost_script_obj['path']
                if(prepost_script_active == 1):
                    prepost_script_file = files_and_folders.Files(prepost_script_path)                
                    error_exit_prefix = {
                        1: ":ON ERROR EXIT\n",   # MSSQL
                        2: "WHENEVER SQLERROR EXIT FAILURE;\n",  # Oracle (sqlpus)
                        3: "\\set ON_ERROR_STOP on\n",  # PostgreSQL (psql)
                        4: " \n",  # MySql
                        5: " \n"  # Google BigQuery
                    }

                    match connection_type_id:

                        case 1 | 2 | 3 | 4 | 5:
                            prefix = error_exit_prefix.get(connection_type_id, "")
                            if prepost_script_type_id == 0:
                                text = prefix + prepost_script_file.read_file()
                            else:
                                text = prepost_script_file.read_file()
                        case _:
                            text = prepost_script_file.read_file()

                    match prepost_script_type_id:
                        case 0:
                            file.add_first_line_to_file(text)
                        case 1:
                            file.append_file(text)
                        case 2:
                            file.add_first_line_to_file(text)
                            file.append_file(text)

    @drm_logger.log_decorator(logger) 
    def deploy_release(self):
        """ 
        Deploy release
        :return:
        """ 
        deployment_started = False

        deployment_id = uuid.uuid4()
        deploy_file_base_name = "{execution_mode}_{deployment_id}".format(execution_mode = self.execution_mode, deployment_id = deployment_id)
        try_num = 0
        deployment_succeeded = False
        
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

        deploy_file_base_name = "{execution_mode}_{deployment_id}_C{connection}_R{release_id}".format(execution_mode = self.execution_mode, deployment_id = deployment_id, release_id = release_id, connection = self.connection)
        deploy_log_file_name = "{deploy_file_base_name}.json".format(deploy_file_base_name = deploy_file_base_name)
        deploy_dir = os.path.join(current_working_directory, DEPLOY_DIR)
        if (self.deploy_config.installation_type == "json") and not(os.path.exists(deploy_dir)):
            os.mkdir(deploy_dir)
        build_dir = os.path.join(current_working_directory, self.deploy_config.build_folder_name)
        deployment_file = files_and_folders.Files(os.path.join(build_dir, deploy_log_file_name))

        #=========================
        # Generate Deployment JSON
        #=========================
        deployment_js = Deploy.generate_deployment_json(self, release_id, release_name, release_max_retries, deployment_id)
        deployment_file.write_file(json.dumps(deployment_js, indent=7))
        deployment_js = deployment_file.load_file()
            
        try:

            task_statuses = {}
            
            deployment_former_try_js = {}

            while try_num <= release_max_retries and not(deployment_succeeded):
                try:                    
                    try_num += 1
                    #==================
                    # Generate Try JSON
                    #==================
                    deployment_try_js = Deploy.generate_try_json(self, try_num)
                    if (deployment_former_try_js == {}):
                        deployment_former_try_js = deployment_try_js

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
                            solution_file_name = js_solution['file_name']

                            #====================
                            # Get connection info
                            #====================
                            for js_connection in js_solution['connections']:
                                connection_id = js_connection['id']
                                connection_name = js_connection['name']
                                connection_type_id = js_connection['connection_type_id']
                                connection_string = js_connection['connection_string']
                                if (deployment_js["connection_id"] == None):
                                    deployment_js["connection_id"] = connection_id
                                if (deployment_js["connection_name"] == None):
                                    deployment_js["connection_name"] = connection_name
                                if self.deploy_config.db_secured:
                                    crpt = crypto.Crypto(self.encryption_key)
                                    connection_string = crpt.decrypt_string(connection_string)

                            #=======================
                            # Generate Solution JSON
                            #=======================
                            deployment_solution_js = Deploy.generate_solution_json(self, solution_id, solution_name)                            

                            match solution_type_id:
                                case 1:#sqlpackage
                                    solution_obj = sqlpackage.SqlPackage(self.deploy_config, connection_type_id)
                                case 2:#liquibase
                                    solution_obj = liquibase.Liquibase(self.deploy_config, connection_type_id)
                                case 3:#flyway
                                    solution_obj = flyway.Flyway(self.deploy_config, connection_type_id)

                            #=========================
                            # Get SQL script variables
                            #=========================
                            sql_script_variables_list = []
                            if "sql_scripts_variables" in js_solution:
                                for js_sql_script_variable in js_solution['sql_scripts_variables']:
                                    sql_script_variables_list.append((js_sql_script_variable['name'], js_sql_script_variable['value']))

                            #====================
                            # Get active projects
                            #====================
                            for js_project in js_solution['projects']:
                                if "is_active" in js_project:
                                    project_is_active = js_project['is_active']
                                else:
                                    project_is_active = 1

                                if (project_is_active):
                                    task_statuses = {}
                                    #=================
                                    # Get project info
                                    #=================
                                    project_id = js_project['id']
                                    project_name = js_project['name']
                                    project_targets_compare_db = js_project['targets_compare_db']
                                    project_targets_type_id = js_project['targets_type_id']
                                    project_targets_list = js_project['targets_list']
                                    project_targets_sql_script_id = js_project['targets_sql_script_id']
                                    project_targets_sql_text = js_project['targets_sql_text']
                                    project_targets_priority = js_project['targets_priority']
                                    project_targets_exclude = js_project['targets_exclude']
                                    project_max_degree_in_parallel = js_project['max_degree_in_parallel']
                                    project_timeout_in_min = js_project['timeout_in_min']
                                    project_sleep_time_in_sec = js_project['sleep_time_in_sec']
                                    project_deployment_properties = js_project['deployment_properties']
                                    project_fail_on_error = js_project['fail_on_error']

                                    prepost_scripts = js_project['pre_post_deployment_projects_scripts']

                                    source_file = solution_obj.get_source_file(solution_path, solution_file_name, project_name)                                    

                                    #============
                                    # DryRun mode
                                    #============
                                    if (self.execution_mode == DRYRUN_MODE):
                                        
                                        #========================
                                        # Generate upgrade script
                                        #========================
                                        target_connection_string = solution_obj.get_fixed_connection_string(connection_string, project_targets_compare_db)                                              
                                        upgrade_script = solution_obj.generate_upgrade_script(deploy_file_base_name, solution_id, project_id, project_name, project_targets_compare_db, source_file, target_connection_string, project_deployment_properties,solution_path)
    
                                        #======================
                                        # PRE POST SCRIPTS
                                        #======================
                                        self.update_update_scrip(upgrade_script,prepost_scripts,connection_type_id)
                                       

                                        #======================
                                        # Generate Project JSON
                                        #======================
                                        deployment_project_js = Deploy.generate_project_json(self, project_id, project_name)

                                        deployment_project_js["target_database_name"] = project_targets_compare_db
                                        deployment_project_js["start_time"] = datetime.now().isoformat()
                                        deployment_project_js["end_time"] = datetime.now().isoformat()
                                        deployment_project_js["deployment_status_id"] = 2
                                        deployment_project_js["deployment_status_name"] = DEPLOYMENT_SUCCESS_STATUS
                                        
                                        deployment_solution_js["deployments_projects"].append(deployment_project_js)

                                    #================================
                                    # Deploy mode (Not a DryRun mode)
                                    #================================
                                    if (self.execution_mode in (DEPLOY_MODE, ALIGN_MODE)):
                                        if project_max_degree_in_parallel == None:
                                            project_max_degree_in_parallel = 1
                                        if (self.execution_mode == ALIGN_MODE and project_max_degree_in_parallel > 5):
                                            project_max_degree_in_parallel = 5
                                        pending_tasks = []
                                        failed_tasks = []

                                        target_connection_string = solution_obj.get_fixed_connection_string(connection_string, project_targets_compare_db)                                              

                                        # Get list targets
                                        targets_list_js = solution_obj.get_list_of_targets(project_targets_type_id, project_targets_list, target_connection_string, project_targets_sql_text, project_targets_priority, project_targets_exclude, project_targets_compare_db)
                                        
                                        # First try --> Check former deployment if failed
                                        if try_num == 1:
                                            task_statuses = Deploy.get_last_deployment_statuses(self, release_id, solution_id, project_id, targets_list_js, deploy_dir, self.db_file_name)     

                                        # Former try failed --> Get statuses by project from former try json results
                                        if (deployment_former_try_js != deployment_try_js):
                                            for js_former_solution in deployment_former_try_js['deployments_solutions']:
                                                if (js_former_solution["solution_id"] == solution_id):
                                                    for js_former_project in js_former_solution['deployments_projects']:
                                                        if (js_former_project["project_id"] == project_id):
                                                            task_statuses[js_former_project["target_database_name"]] = {"status_id": js_former_project['deployment_status_id'], "status_name": js_former_project['deployment_status_name'], "start_time": js_former_project['start_time'], "end_time": js_former_project['end_time'], "error_message": None}

                                        if (task_statuses != {}):
                                            for target_db in targets_list_js:  
                                                if (target_db in task_statuses):
                                                    # If did not deploy in former run within the same deployment --> run it now
                                                    if(task_statuses[target_db]['status_id'] == 0):
                                                        pending_tasks.append({"target_db": target_db})
                                                        task_statuses[target_db] = {"status_id": task_statuses[target_db]['status_id'], "status_name": task_statuses[target_db]['status_name'], "start_time": None, "end_time": None, "error_message": None}
                                                    # If deployed successfully in former run within the same deployment --> mark it as already deployed
                                                    elif(task_statuses[target_db]['status_id'] == 2):
                                                        task_statuses[target_db] = {"status_id": 5, "status_name": DEPLOYMENT_ALREADY_DEPLOYED_STATUS, "start_time": task_statuses[target_db]['start_time'], "end_time": task_statuses[target_db]['end_time'], "error_message": task_statuses[target_db]['error_message']}
                                                    else:
                                                        task_statuses[target_db] = {"status_id": task_statuses[target_db]['status_id'], "status_name": task_statuses[target_db]['status_name'], "start_time": task_statuses[target_db]['start_time'], "end_time": task_statuses[target_db]['end_time'], "error_message": task_statuses[target_db]['error_message']}
                                                        # Former failed deployment
                                                        if(task_statuses[target_db]['status_id'] == 4):
                                                            failed_tasks.append({"target_db": target_db})
                                                else:
                                                    # If any target database that did not yet run in the former try --> add it as pending
                                                    pending_tasks.append({"target_db": target_db})
                                                    task_statuses[target_db] = {"status_id": "0", "status_name": DEPLOYMENT_PENDING_STATUS, "start_time": None, "end_time": None, "error_message": None}                                                                              

                                        else:
                                            # New deployment --> deploy all target databases
                                            for target_db in targets_list_js:  
                                                pending_tasks.append({"target_db": target_db})
                                                task_statuses[target_db] = {"status_id": "0", "status_name": DEPLOYMENT_PENDING_STATUS, "start_time": None, "end_time": None, "error_message": None}                                                                              
                                        
                                        #===================================
                                        # Resolve former deployment failures
                                        #===================================
                                        for task in failed_tasks:
                                            
                                            target_db = task["target_db"]
                                            #========================
                                            # Generate upgrade script
                                            #========================
                                            target_connection_string = solution_obj.get_fixed_connection_string(connection_string, target_db)                                              
                                            upgrade_script = solution_obj.generate_upgrade_script(deploy_file_base_name, solution_id, project_id, project_name, target_db, source_file, target_connection_string, project_deployment_properties, solution_path)

                                            #======================
                                            # PRE POST SCRIPTS
                                            #======================
                                            self.update_update_scrip(upgrade_script,prepost_scripts,connection_type_id)


                                            try:
                                                task_statuses[target_db]["start_time"] = datetime.now().isoformat()
                                                result = solution_obj.run_upgrade_script(deploy_file_base_name, solution_id, project_id, project_name, target_db, upgrade_script, target_connection_string, sql_script_variables_list, project_fail_on_error)
                                                task_statuses[target_db]["status_id"] = 2
                                                task_statuses[target_db]["status_name"] = DEPLOYMENT_SUCCESS_STATUS
                                                task_statuses[target_db]["error_message"] = None
                                            except Exception as e:
                                                task_statuses[target_db]["status_id"] = 4
                                                task_statuses[target_db]["status_name"] = DEPLOYMENT_FAILED_STATUS
                                                task_statuses[target_db]["error_message"] = f"{str(e)}"
                                                failed = True
                                                if project_fail_on_error and failed:
                                                    raise Exception ('One or more projects deployment failed.')

                                            finally:
                                                task_statuses[target_db]["end_time"] = datetime.now().isoformat()
                                        
                                        #==============================
                                        # Run pending tasks in parallel
                                        #==============================
                                        if(len(pending_tasks) > 0):
                                        
                                            upgrade_script = None
                                            target_connection_string = None
                                            
                                            #========================
                                            # Generate upgrade script
                                            #========================
                                            if (self.execution_mode == DEPLOY_MODE):
                                                target_connection_string = solution_obj.get_fixed_connection_string(connection_string, project_targets_compare_db)
                                                upgrade_script = solution_obj.generate_upgrade_script(deploy_file_base_name, solution_id, project_id, project_name, project_targets_compare_db, source_file, target_connection_string, project_deployment_properties, solution_path)

                                                #======================
                                                # PRE POST SCRIPTS
                                                #======================
                                                self.update_update_scrip(upgrade_script,prepost_scripts,connection_type_id)

                                            # Queue pending tasks in parallel
                                            task_queue = Queue()
                                            for task in pending_tasks:
                                                task_queue.put(task)

                                            failed = False
                                            
                                            # Wrapper for parallel execution (Async threads)
                                            def task_wrapper(task: Dict[str, Any], upgrade_script, target_connection_string) -> None:
                                                target_db = task["target_db"]
                                                try:
                                                    if (target_db != project_targets_compare_db):
                                                        task_statuses[target_db]["start_time"] = datetime.now().isoformat()
                                                        if (self.execution_mode == ALIGN_MODE):
                                                            target_connection_string = solution_obj.get_fixed_connection_string(connection_string, target_db)
                                                            upgrade_script = solution_obj.generate_upgrade_script(deploy_file_base_name, solution_id, project_id, project_name, target_db, source_file, target_connection_string, project_deployment_properties, solution_path)

                                                            #======================
                                                            # PRE POST SCRIPTS
                                                            #======================
                                                            self.update_update_scrip(upgrade_script,prepost_scripts,connection_type_id)
                                            
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
                                                deployment_started = True
                                                for _ in range(project_max_degree_in_parallel):
                                                    if not task_queue.empty():
                                                        task = task_queue.get()
                                                        futures.append(executor.submit(task_wrapper, task, upgrade_script, target_connection_string))

                                                while futures:
                                                    done, _ = concurrent.futures.wait(futures, return_when=concurrent.futures.FIRST_COMPLETED)
                                                    for future in done:
                                                        futures.remove(future)
                                                        future.result()  # Re-raise exceptions if any

                                                    if failed and project_fail_on_error:
                                                        break

                                                    if not task_queue.empty() and not (failed and project_fail_on_error):
                                                        task = task_queue.get()
                                                        futures.append(executor.submit(task_wrapper, task, upgrade_script, target_connection_string))

                                            # Mark remaining pending_tasks as not started if there was a failure and project_fail_on_error is True
                                            if project_fail_on_error and failed:
                                                while not task_queue.empty():
                                                    task = task_queue.get()
                                                    task_statuses[task["target_db"]]["status_id"] = 0
                                                    task_statuses[task["target_db"]]["status_name"] = DEPLOYMENT_PENDING_STATUS
                                                raise Exception ('One or more projects deployment failed.')

                                            # Handle compare DB only after all other target database finished successfully
                                            if (project_targets_compare_db in targets_list_js):
                                                target_db = project_targets_compare_db
                                                try:
                                                    task_statuses[target_db]["start_time"] = datetime.now().isoformat()
                                                    if (self.execution_mode == ALIGN_MODE):
                                                        target_connection_string = solution_obj.get_fixed_connection_string(connection_string, target_db)
                                                        upgrade_script = solution_obj.generate_upgrade_script(deploy_file_base_name, solution_id, project_id, project_name, target_db, source_file, target_connection_string, project_deployment_properties, solution_path)
                                                        
                                                        #======================
                                                        # PRE POST SCRIPTS
                                                        #======================
                                                        self.update_update_scrip(upgrade_script,prepost_scripts,connection_type_id)
                                                        
                                                    result = solution_obj.run_upgrade_script(deploy_file_base_name, solution_id, project_id, project_name, target_db, upgrade_script, target_connection_string, sql_script_variables_list, project_fail_on_error)
                                                    task_statuses[target_db]["status_id"] = 2
                                                    task_statuses[target_db]["status_name"] = DEPLOYMENT_SUCCESS_STATUS
                                                except Exception as e:
                                                    task_statuses[target_db]["status_id"] = 4
                                                    task_statuses[target_db]["status_name"] = DEPLOYMENT_FAILED_STATUS
                                                    task_statuses[target_db]["error_message"] = f"{str(e)}"
                                                    failed = True
                                                finally:
                                                    task_statuses[target_db]["end_time"] = datetime.now().isoformat()
                                        
                                        #============================================
                                        # Summaries all projects deployments statuses
                                        #============================================
                                        for task in task_statuses:
                                            #======================
                                            # Generate Project JSON
                                            #======================
                                            deployment_project_js = Deploy.generate_project_json(self, project_id, project_name)

                                            deployment_project_js["target_database_name"] = task
                                            deployment_project_js["start_time"] = task_statuses[task]['start_time']
                                            deployment_project_js["end_time"] = task_statuses[task]['end_time']
                                            deployment_project_js["error_message"] = task_statuses[task]['error_message']
                                            deployment_project_js["deployment_status_id"] = task_statuses[task]['status_id']
                                            deployment_project_js["deployment_status_name"] = task_statuses[task]['status_name']
                                            
                                            deployment_solution_js["deployments_projects"].append(deployment_project_js)


                            deployment_solution_js["deployment_status_id"] = 2
                            deployment_solution_js["deployment_status_name"] = DEPLOYMENT_SUCCESS_STATUS
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

                    deployment_succeeded = True

                except Exception as e: 
                    if (deployment_started):
                        for task in task_statuses:
                            if (task_statuses[task]['status_id'] != 0):
                                #======================
                                # Generate Project JSON
                                #======================
                                deployment_project_js = Deploy.generate_project_json(self, project_id, project_name)

                                deployment_project_js["target_database_name"] = task
                                deployment_project_js["start_time"] = task_statuses[task]['start_time']
                                deployment_project_js["end_time"] = task_statuses[task]['end_time']
                                deployment_project_js["error_message"] = task_statuses[task]['error_message']
                                deployment_project_js["deployment_status_id"] = task_statuses[task]['status_id']
                                deployment_project_js["deployment_status_name"] = task_statuses[task]['status_name']
                                            
                                deployment_solution_js["deployments_projects"].append(deployment_project_js)
                                                                
                        deployment_solution_js["end_time"] = datetime.now().isoformat()           
                        deployment_solution_js["error_message"] = f"{e}"
                        deployment_solution_js["deployment_status_id"] = 4
                        deployment_solution_js["deployment_status_name"] = DEPLOYMENT_FAILED_STATUS
                        deployment_try_js["deployments_solutions"].append(deployment_solution_js)
                        deployment_try_js["deployment_status_id"] = 4
                        deployment_try_js["deployment_status_name"] = DEPLOYMENT_FAILED_STATUS
                        deployment_try_js["error_message"] = f"{e}"
                        deployment_try_js["end_time"] = datetime.now().isoformat()
                        
                        # Save try json result for retry statuses
                        deployment_former_try_js = deployment_try_js

                        deployment_js["deployments_tries"].append(deployment_try_js)
                        
                        if (try_num <= release_max_retries):
                            self.logger.error(f'Deployment try failed, {e}, queue retry #{try_num} (out of max {release_max_retries} retries)')
                        else:
                            raise Exception (f'{e}')
                    
                    else:
                        raise Exception (f'{e}')                                    


        except Exception as e: 
            if (deployment_started):
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
        
        