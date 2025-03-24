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
from modules import parser_json_json, sqlite, parser_json_sqlite, mssql,postgresql

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
                raise Exception ('{app_name} utility not found!!!'.format(app_name = app_name))
            else:
                return (file_name.replace("\\", "/"))


        js = deploy_config.full_config
        missing_object = False
        self.default_data_path = None
        self.default_log_path = None 
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
    def generate_upgrade_script(self, deploy_file_base_name, solution_id, project_id, project_name, project_targets_compare_db, source_file, connection_string, deployment_properties, solution_path):
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
        :param solution_path: solution path
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
        
        if (deployment_properties == None or len(deployment_properties)==0):
            deployment_properties = '[]'
        else:
            js_deployment_properties = json.loads(deployment_properties)
            for property in js_deployment_properties:
                args_list.append("/p:" + property)
                if (property=="CommentOutSetVarDeclarations=True"):
                    target_db_obj = mssql.MsSql(self.run_script_tool_file_name, connection_string)
                    defaults_sql_text="SELECT SERVERPROPERTY('InstanceDefaultDataPath') AS DefaultDataPath,SERVERPROPERTY('InstanceDefaultLogPath') AS DefaultLogPath;"
                    result = target_db_obj.execute_query(defaults_sql_text)
                    js_result = json.loads(result)
                    if len(js_result)>0:
                        self.default_data_path = js_result[0]["DefaultDataPath"]
                        self.default_log_path = js_result[0]["DefaultLogPath"]
                        



        #=============================
        # Generate upgrade script file
        #=============================
        result = subprocess.run(args_list, capture_output=True)
        # Check if process exit with a failure
        if result.stderr:
            raise Exception (result.stderr)
            
        if (self.default_data_path != None):
            file = files_and_folders.Files(upgrade_script)
            text = f':setvar DefaultLogPath "{self.default_log_path}"\n'
            file.add_first_line_to_file(text)
            text = f':setvar DefaultDataPath "{self.default_data_path}"'
            file.add_first_line_to_file(text)
            
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
        
        if(self.default_data_path != None):
            db_obj.default_data_path = self.default_data_path
            db_obj.default_log_path = self.default_log_path
            

        try:
            result = db_obj.run_script(upgrade_script)
            self.logger.info(f'Upgrade "{target_name}" finished successfully!!!')
            return result
        except Exception as e:
            if (project_fail_on_error):
                raise Exception(f'{e}')
            else:
                self.logger.warning(f'{e}')
class Liquibase:

    logger = drm_logger.configure_logging("deploy.Liquibase")

    @drm_logger.log_decorator(logger) 
    def __init__(self, deploy_config): 
        def get_location (self, app_name):
           
            app = "{app_name}.bat".format(app_name = app_name)
            if which(app) != None:
                return which(app)
            app = "{app_name}.exe".format(app_name = app_name)
            if which(app) != None:
                return which(app)
            if which(app_name) != None:
                return which(app_name)
            # Not known --> search
            f = files_and_folders.Files(app_name)
            file_name = f.find_file_in_dir("/")
            if (file_name == None):
                f = files_and_folders.Files("{app_name}.bat".format(app_name = app_name))
                file_name = f.find_file_in_dir("/")
            if (file_name == None):
                f = files_and_folders.Files("{app_name}.exe".format(app_name = app_name))
                file_name = f.find_file_in_dir("/")
            if (file_name == None):
                raise Exception ('{app_name} utility not found!!!'.format(app_name = app_name))
            else:
                return (file_name.replace("\\", "/"))


        js = deploy_config.full_config
        missing_object = False
        self.default_data_path = None
        self.default_log_path = None 
        #============================
        # Identify SqlPackage utility
        #============================
        #todo add more types 
        app_name = "liquibase"
        liquibase_path = next(
           (json.loads(loc)["liquibase_path"] for loc in deploy_config.full_config["locations"] if "liquibase_path" in json.loads(loc)) ,
           None 
        )
        if liquibase_path is not None:
            self.upgrade_tool_file_name = liquibase_path
        else:
            # Utility not configured --> serach
            missing_object = True
            self.logger.info("{app_name} utility path was not supplied in drm_deploy.config, searching (This may take a while)...".format(app_name = app_name))
            self.upgrade_tool_file_name = get_location (self, app_name)                    
            self.logger.info("{app_name} utility found & configured in drm_deploy.config for next deployments!!!".format(app_name = app_name))
            
            locations_js = json.loads(json.dumps('{"liquibase_path": "' + self.upgrade_tool_file_name.replace("\\","\\\\") + '"}', indent=4))
            js['locations'].append(locations_js)

        app_name = "psql"
        psql_path = next(
           (json.loads(loc)["psql_path"] for loc in deploy_config.full_config["locations"] if "psql_path" in json.loads(loc)) ,
           None 
        )
        if psql_path is not None:
            self.run_script_tool_file_name = psql_path
        else:
            # Utility not configured --> serach
            missing_object = True
            self.logger.info("{app_name} utility path was not supplied in drm_deploy.config, searching (This may take a while)...".format(app_name = app_name))
            self.run_script_tool_file_name = get_location (self, app_name)                    
            self.logger.info("{app_name} utility found & configured in drm_deploy.config for next deployments!!!".format(app_name = app_name))
            
            locations_js = json.loads(json.dumps('{"psql_path": "' + self.run_script_tool_file_name.replace("\\","\\\\") + '"}', indent=4))
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
                target_db_obj = postgresql.PostgreSQL(self.run_script_tool_file_name, connection_string)
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
        #TODO change to changelog
        #return os.path.join (solution_path,  "changelog.xml")
        return "changelog.xml"

    @drm_logger.log_decorator(logger) 
    def get_fixed_connection_string(self, connection_string, project_targets_compare_db):
        """ 
        returns the fixed connection string using compare DB
        :param connection_string: connection string from the solution
        :param project_targets_compare_db: database name to connect into
        :return: fixed conneciton string (String)
        """ 
        #jdbc_url = self.parse_connection_string(connection_string,"url")
        #--url=jdbc:postgresql://127.0.0.1:5432/postgres ^
        #--url=jdbc:postgresql://127.0.0.1:5432/mydatabase ^
        #return url.replace("/postgres",f"/{project_targets_compare_db}")
        return re.sub(r"(url=jdbc:postgresql://[^/]+/)(\w+)", rf"\1{project_targets_compare_db}", connection_string)
        
        #return connection_string + "Database={project_targets_compare_db};".format(project_targets_compare_db = project_targets_compare_db)

    @drm_logger.log_decorator(logger) 
    def parse_connection_string(self, connection_string, key):
        """ 
        returns the  connection string value for key
        :param connection_string: connection string from the solution
        :param key: key in the connection (e.g., 'url', 'username', 'password')
        :return: value of conneciton string for key (String)
        """ 
        key = key.lower()
        parts = connection_string.split(';')
        # Map each key to its corresponding prefix in the connection string
        key_map = {
            "url": "url=",
            "username": "username=",
            "password": "password="
        }

        # Check if the key exists in the map and return the corresponding value
        for part in parts:
            if part.startswith(key_map.get(key, "")):
                return part.split('=')[1]
        return None 

    @drm_logger.log_decorator(logger) 
    def generate_upgrade_script(self, deploy_file_base_name, solution_id, project_id, project_name, project_targets_compare_db, source_file, connection_string, deployment_properties, solution_path):
        """ 
        returns the fixed connection string using compare DB
        :param deploy_file_base_name: file base name (prefix)
        :param solution_id: solution ID
        :param project_id: project ID
        :param project_name: project name
        :param project_targets_compare_db: target database name to compare with
        :param source_file: source file name (changelog)
        :param connection_string: connection string
        :param deployment_properties: array of deployment properties
        :param solution_path: solution path
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
        
        #changeLogFile  C:\Users\vikil\liquibase\Project_P01
        args_list.append("--changeLogFile=" + source_file)
        #SearchPath
        f = files_and_folders.Files(os.path.join(solution_path, source_file))
         
        if  f.check_file_exists():
            args_list.append("--search-path=" + solution_path)
        else:
            f = files_and_folders.Files(os.path.join(solution_path, project_name, source_file))
            if  f.check_file_exists():
                args_list.append("--search-path=" + os.path.join(solution_path, project_name))
            else:
                raise Exception ("Search path not defined")
        #parse connection_string
        url = self.parse_connection_string(connection_string,"url")
        username = self.parse_connection_string(connection_string,"username")
        password = self.parse_connection_string(connection_string,"password")

        args_list.append("--url=" + url)
        #user
        args_list.append("--username=" + username)
        #password
        args_list.append("--password=" + password)
        # Output log file
        #args_list.append("--logFile=" + "./liquibase.log")
        args_list.append("--logLevel=SEVERE")
        # Generate script
        args_list.append("updateSql" )
        # Deployment properties
        
        if (deployment_properties == None or len(deployment_properties)==0):
            deployment_properties = '[]'
        else:
            js_deployment_properties = json.loads(deployment_properties)
        
                  



        #=============================
        # Generate upgrade script file
        #=============================
        output_file =  upgrade_script

        with open(output_file, "w") as f:
            result = subprocess.run(args_list, stdout=f, stderr=subprocess.PIPE, text=True)


        # Check if process exit with a failure
        if result.returncode != 0:
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
        
        db_obj = postgresql.PostgreSQL(self.run_script_tool_file_name, connection_string, target_name, sql_script_variables_list, upgrade_log_file)
        
        #if(self.default_data_path != None):
        #    db_obj.default_data_path = self.default_data_path
        #    db_obj.default_log_path = self.default_log_path
            

        try:
            result = db_obj.run_script(upgrade_script)
            self.logger.info(f'Upgrade "{target_name}" finished successfully!!!')
            return result
        except Exception as e:
            if (project_fail_on_error):
                raise Exception(f'{e}')
            else:
                self.logger.warning(f'{e}')
class Flyway:

    logger = drm_logger.configure_logging("deploy.Flyway")

    @drm_logger.log_decorator(logger) 
    def __init__(self, deploy_config): 
        def get_location (self, app_name):
            if which(app_name) != None:
                return which(app_name)
            app = "{app_name}.cmd".format(app_name = app_name)
            if which(app) != None:
                return which(app)
            app = "{app_name}.exe".format(app_name = app_name)
            if which(app) != None:
                return which(app)

            # Not known --> search
            f = files_and_folders.Files(app_name)
            file_name = f.find_file_in_dir("/")
            if (file_name == None):
                f = files_and_folders.Files("{app_name}.cmd".format(app_name = app_name))
                file_name = f.find_file_in_dir("/")
            if (file_name == None):
                f = files_and_folders.Files("{app_name}.exe".format(app_name = app_name))
                file_name = f.find_file_in_dir("/")
            if (file_name == None):
                raise Exception ('{app_name} utility not found!!!'.format(app_name = app_name))
            else:
                return (file_name.replace("\\", "/"))


        js = deploy_config.full_config
        missing_object = False
        self.default_data_path = None
        self.default_log_path = None 
        #============================
        # Identify SqlPackage utility
        #============================
        #todo add more types 
        app_name = "flyway"
        flyway_path = next(
           (json.loads(loc)["flyway_path"] for loc in deploy_config.full_config["locations"] if "flyway_path" in json.loads(loc)) ,
           None 
        )
        if flyway_path is not None:
            self.upgrade_tool_file_name = flyway_path
        else:
            # Utility not configured --> serach
            missing_object = True
            self.logger.info("{app_name} utility path was not supplied in drm_deploy.config, searching (This may take a while)...".format(app_name = app_name))
            self.upgrade_tool_file_name = get_location (self, app_name)                    
            self.logger.info("{app_name} utility found & configured in drm_deploy.config for next deployments!!!".format(app_name = app_name))
            
            locations_js = json.loads(json.dumps('{"flyway_path": "' + self.upgrade_tool_file_name.replace("\\","\\\\") + '"}', indent=4))
            js['locations'].append(locations_js)

        app_name = "psql"
        psql_path = next(
           (json.loads(loc)["psql_path"] for loc in deploy_config.full_config["locations"] if "psql_path" in json.loads(loc)) ,
           None 
        )
        if psql_path is not None:
            self.run_script_tool_file_name = psql_path
        else:
            # Utility not configured --> serach
            missing_object = True
            self.logger.info("{app_name} utility path was not supplied in drm_deploy.config, searching (This may take a while)...".format(app_name = app_name))
            self.run_script_tool_file_name = get_location (self, app_name)                    
            self.logger.info("{app_name} utility found & configured in drm_deploy.config for next deployments!!!".format(app_name = app_name))
            
            locations_js = json.loads(json.dumps('{"psql_path": "' + self.run_script_tool_file_name.replace("\\","\\\\") + '"}', indent=4))
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
                target_db_obj = postgresql.PostgreSQL(self.run_script_tool_file_name, connection_string)
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
        #TODO change to changelog
        #return os.path.join (solution_path,  "changelog.xml")
        return "changelog.xml"

    @drm_logger.log_decorator(logger) 
    def get_fixed_connection_string(self, connection_string, project_targets_compare_db):
        """ 
        returns the fixed connection string using compare DB
        :param connection_string: connection string from the solution
        :param project_targets_compare_db: database name to connect into
        :return: fixed conneciton string (String)
        """ 
        #jdbc_url = self.parse_connection_string(connection_string,"url")
        #--url=jdbc:postgresql://127.0.0.1:5432/postgres ^
        #--url=jdbc:postgresql://127.0.0.1:5432/mydatabase ^
        #return url.replace("/postgres",f"/{project_targets_compare_db}")
        return re.sub(r"(url=jdbc:postgresql://[^/]+/)(\w+)", rf"\1{project_targets_compare_db}", connection_string)
        
        #return connection_string + "Database={project_targets_compare_db};".format(project_targets_compare_db = project_targets_compare_db)

    @drm_logger.log_decorator(logger) 
    def parse_connection_string(self, connection_string, key):
        """ 
        returns the  connection string value for key
        :param connection_string: connection string from the solution
        :param key: key in the connection (e.g., 'url', 'username', 'password')
        :return: value of conneciton string for key (String)
        """ 
        key = key.lower()
        parts = connection_string.split(';')
        # Map each key to its corresponding prefix in the connection string
        key_map = {
            "url": "url=",
            "username": "username=",
            "password": "password="
        }

        # Check if the key exists in the map and return the corresponding value
        for part in parts:
            if part.startswith(key_map.get(key, "")):
                return part.split('=')[1]
        return None 

    @drm_logger.log_decorator(logger) 
    def generate_upgrade_script(self, deploy_file_base_name, solution_id, project_id, project_name, project_targets_compare_db, source_file, connection_string, deployment_properties, solution_path):
        """ 
        returns the fixed connection string using compare DB
        :param deploy_file_base_name: file base name (prefix)
        :param solution_id: solution ID
        :param project_id: project ID
        :param project_name: project name
        :param project_targets_compare_db: target database name to compare with
        :param source_file: source file name (changelog)
        :param connection_string: connection string
        :param deployment_properties: array of deployment properties
        :param solution_path: solution path
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
        
 
        #-dryRunOutput=/home/osboxes/flyway/Project_FL_01/dryrun_output.sql \
        #-outputFile=/home/osboxes/flyway/Project_FL_01/output.log \

        #locations
        f = files_and_folders.Folders(os.path.join(solution_path, project_name))
        if  f.check_folder_exists():
            args_list.append("-locations=filesystem:" + os.path.join(solution_path, project_name))
        else:
            raise Exception ("Search path not defined(locations)")
        #parse connection_string
        url = self.parse_connection_string(connection_string,"url")
        username = self.parse_connection_string(connection_string,"username")
        password = self.parse_connection_string(connection_string,"password")

        args_list.append("-url=" + url)
        #user
        args_list.append("-user=" + username)
        #password
        args_list.append("-password=" + password)
        #dryRunOutput
        args_list.append("-dryRunOutput=" + upgrade_script)
        args_list.append("-q")
        # Generate script
        args_list.append("migrate" )
        # Deployment properties
        
        if (deployment_properties == None or len(deployment_properties)==0):
            deployment_properties = '[]'
        else:
            js_deployment_properties = json.loads(deployment_properties)
        
                  



        #=============================
        # Generate upgrade script file
        #=============================
        output_file =  upgrade_script

        with open(output_file, "w") as f:
            result = subprocess.run(args_list, stdout=f, stderr=subprocess.PIPE, text=True)


        # Check if process exit with a failure
        if result.returncode != 0:
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
        
        db_obj = postgresql.PostgreSQL(self.run_script_tool_file_name, connection_string, target_name, sql_script_variables_list, upgrade_log_file)
        
        #if(self.default_data_path != None):
        #    db_obj.default_data_path = self.default_data_path
        #    db_obj.default_log_path = self.default_log_path
            

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

                            #=======================
                            # Generate Solution JSON
                            #=======================
                            deployment_solution_js = Deploy.generate_solution_json(self, solution_id, solution_name)                            

                            if (solution_type_id == 1): #mssql
                                solution_obj = MsSql(self.deploy_config)
                            if (solution_type_id == 2): #liquibase
                                solution_obj = Liquibase(self.deploy_config)
                            if (solution_type_id == 3): #flyway
                                solution_obj = Flyway(self.deploy_config)

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
                                    project_max_degree_in_parallel = js_project['max_degree_in_parallel']
                                    project_timeout_in_min = js_project['timeout_in_min']
                                    project_sleep_time_in_sec = js_project['sleep_time_in_sec']
                                    project_deployment_properties = js_project['deployment_properties']
                                    project_fail_on_error = js_project['fail_on_error']

                                    source_file = solution_obj.get_source_file(solution_path, project_name)                                    

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
                                        targets_list_js = solution_obj.get_list_of_targets(project_targets_type_id, project_targets_list, target_connection_string, project_targets_sql_text, project_targets_compare_db)
                                        
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
        
        