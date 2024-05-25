import os
import json
import zipfile
import sqlite3
import logging
import subprocess
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
DRYRUN_MODE = "DryRun"
DEPLOY_MODE = "Deploy"

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
    def get_list_of_targets(self, targets_type_id, targets_list, targets_sql_text):
        """ 
        Returns a list of target databases to deploy into
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
    def generate_upgrade_script(self, solution_id, project_id, project_name, project_targets_compare_db, source_file, connection_string, deployment_properties):
        """ 
        returns the fixed connection string using compare DB
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
        upgrade_script = os.path.join (current_working_directory, "bin", "S" + str(solution_id) + "-P" + str(project_id) + "-" + project_name + "-" + project_targets_compare_db + ".sql")
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
            deployment_properties = []
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
            #raise subprocess.CalledProcessError(
            #        returncode = result.returncode,
            #        cmd = result.args,
            #        stderr = result.stderr
            #        )
        self.logger.info("Upgrade script generated successfully!!!")

        return upgrade_script
               
    @drm_logger.log_decorator(logger) 
    def run_upgrade_script(self, solution_id, project_id, project_name, target_name, upgrade_script, connection_string):
        """ 
        returns the fixed connection string using compare DB
        :param solution_id: solution ID
        :param project_id: project ID
        :param project_name: project name
        :param target_name: target database name
        :param upgrade_script: upgrade script name
        :param connection_string: connection string
        :return: update script name (String)
        """ 
        upgrade_log_file = os.path.join (current_working_directory, "log", "S" + str(solution_id) + "-P" + str(project_id) + "-" + project_name + "-" + target_name + ".log")
        self.logger.info('Running upgrade script against "{target_name}" (log file: "{upgrade_log_file}")...'.format(target_name = target_name, upgrade_log_file = upgrade_log_file))
        
        # Exctract connection details
        connection_win_auth = False
        for param in connection_string.split(";"):
            if (param.find("=") != -1):
                [param_name, param_value] = param.split("=")
                if (param_name.lower() in ['server']):
                    connection_server = param_value
                elif (param_name.lower() in ['user id', 'uid']):
                    connection_username = param_value
                elif (param_name.lower() in ['password', 'pwd']):
                    connection_password = param_value
                elif (param_name.lower() in ['trusted_connection', 'integrated security']) and (param_value.lower() in ['yes', 'true', 'sspi']):
                    connection_win_auth = True

        #==========================================
        # Run upgrade script file against target DB
        #==========================================
        if not (connection_win_auth):
            result = subprocess.run([self.run_script_tool_file_name, "-S", connection_server, "-U", connection_username, "-P", connection_password, "-i", upgrade_script, "-o", upgrade_log_file], capture_output=True)
        else:
            result = subprocess.run([self.run_script_tool_file_name, "-S", connection_server, "-E", "-i", upgrade_script, "-o", upgrade_log_file], capture_output=True)

        # Check if process exit with a failure
        if result.stderr:
            raise Exception (result.stderr)
            #raise subprocess.CalledProcessError(
            #        returncode = result.returncode,
            #        cmd = result.args,
            #        stderr = result.stderr
            #        )
        self.logger.info("Upgrade finished successfully!!!")

        return upgrade_script


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
                        project_deployment_properties = js_project['deployment_properties']
                        project_fail_on_error = js_project['fail_on_error']

                        #========================
                        # Generate upgrade script
                        #========================
                        source_file = solution_obj.get_source_file(solution_path, project_name)
                        target_connection_string = solution_obj.get_fixed_connection_string(connection_string, project_targets_compare_db)                                              
                        upgrade_script = solution_obj.generate_upgrade_script(solution_id, project_id, project_name, project_targets_compare_db, source_file, target_connection_string, project_deployment_properties)

                        #================================
                        # Deploy mode (Not a DryRun mode)
                        #================================
                        if (self.execution_mode == DEPLOY_MODE):
                            # Get list targets
                            targets_list_js = solution_obj.get_list_of_targets(project_targets_type_id, project_targets_list, project_targets_sql_text)
                            for target_db in targets_list_js:
                                solution_obj.run_upgrade_script(solution_id, project_id, project_name, target_db, upgrade_script, target_connection_string)
                            