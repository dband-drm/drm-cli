import os
import json
import zipfile
import sqlite3
import logging
from pathlib import Path
from sqlite3 import Error
from shutil import which
from modules import drm_logger, files_and_folders, crypto

current_working_directory = Path(__file__).parent.parent.resolve()

#===========
# Constrants
#===========
DEPLOY_CONFIG_FILE_NAME = "drm_deploy.config"
BUILD_FILE_NAME = "drm_deploy.json"
PACK_FILE_NAME = "deploy.drmpac"

class MsSql:

    logger = drm_logger.configure_logging("deploy.MsSql")

    @drm_logger.log_decorator(logger) 
    def __init__(self, deploy_config): 

        # Get SqlPackage from configuration
        if hasattr(deploy_config, 'sqlpackage_path'):
            self.file_name = deploy_config.sqlpackage_path
        else:
            self.logger.info("sqlpackage utility path was not supplied in drm_deploy.config, searching (This may take a while)...")
            # Known from PATH or in current directory
            app = "sqlpackage"
            if which(app) != None:
                self.file_name = app
            app = "sqlpackage.exe"
            if which(app) != None:
                self.file_name = app
            # Not known --> search
            if (which("sqlpackage") == None and which("sqlpackage.exe") == None):
                f = files_and_folders.Files("sqlpackage")
                self.file_name = f.find_file_in_dir("/")
                if (self.file_name == None):
                    f = files_and_folders.Files("sqlpackage.exe")
                    self.file_name = f.find_file_in_dir("/")
                if (self.file_name == None):
                    raise ('sqlpackage utility not found!!!')
                else:
                    self.file_name = (self.file_name.replace("\\", "\\\\"))
                    
            self.logger.info("sqlpackage utility found & configured in drm_deploy.config for next deployments!!!")
            locations_js = json.loads('{"sqlpackage_path": "' + self.file_name + '"}')
            js = deploy_config.full_config
            js['locations'].append(locations_js)
            json_obj = json.dumps(js, indent=4)
            drm_config_file = os.path.join(current_working_directory, DEPLOY_CONFIG_FILE_NAME)
            file = files_and_folders.Files(drm_config_file)
            file.write_file(json_obj)
                

    @drm_logger.log_decorator(logger) 
    def get_list_of_targets(self, targets_type_id, targets_list, targets_sql_text):
        """ 
        Deploy release
        :param targets_type_id: targets type id (list or query)
        :param targets_list: targets json list
        :param targets_sql_text: SQL query which returns a list of targets
        :return: List of target databases (json)
        """ 
        #==========
        # JSON list
        #==========
        if targets_type_id == 1:
            return json.loads(targets_list)


class Deploy:

    logger = drm_logger.configure_logging("deploy.Deploy")

    @drm_logger.log_decorator(logger) 
    def __init__(self, deploy_config, encryption_key = False): 
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

    @drm_logger.log_decorator(logger) 
    def deploy_release(self):
        """ 
        Deploy release
        :return:
        """ 
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
                        project_fail_on_error = js_project['fail_on_error']

                        targets_list_js = solution_obj.get_list_of_targets(project_targets_type_id, project_targets_list, project_targets_sql_text)
                        print(len(targets_list_js))
                        for target_db in targets_list_js:
                            print(target_db)
                            