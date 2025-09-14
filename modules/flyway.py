import os
import json
import logging
import subprocess
from pathlib import Path
from shutil import which
from modules import drm_logger, files_and_folders, postgresql, oracle

current_working_directory = Path(__file__).parent.parent.resolve()

#===========
# Constrants
#===========
DEPLOY_CONFIG_FILE_NAME = "drm_deploy.config"

class Flyway:

    logger = drm_logger.configure_logging("deploy.Flyway")

    @drm_logger.log_decorator(logger) 
    def __init__(self, deploy_config, connection_type_id): 

        self.connection_type_id = connection_type_id

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

        if (self.connection_type_id == 2):
            app_name = "sqlplus"
            sqlplus_path = next(
            (json.loads(loc)["sqlplus_path"] for loc in deploy_config.full_config["locations"] if "sqlplus_path" in json.loads(loc)) ,
            None 
            )
            if sqlplus_path is not None:
                self.run_script_tool_file_name = sqlplus_path
            else:
                # Utility not configured --> serach
                missing_object = True
                self.logger.info("{app_name} utility path was not supplied in drm_deploy.config, searching (This may take a while)...".format(app_name = app_name))
                self.run_script_tool_file_name = get_location (self, app_name)                    
                self.logger.info("{app_name} utility found & configured in drm_deploy.config for next deployments!!!".format(app_name = app_name))
                
                locations_js = json.loads(json.dumps('{"sqlplus_path": "' + self.run_script_tool_file_name.replace("\\","\\\\") + '"}', indent=4))
                js['locations'].append(locations_js)

        if (self.connection_type_id == 3):
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
    def get_list_of_targets(self, targets_type_id, targets_list, connection_string, targets_sql_text, targets_priority, targets_exclude, targets_compare_db):
        """ 
        Returns a list of target databases to deploy into
        :param targets_type_id: targets type id (list or query)
        :param targets_list: targets json list
        :param targets_sql_text: SQL query which returns a list of targets
        :param targets_priority: targets priority json 
        :param targets_exclude: targets json to exclude from list 
        :prams targets_compare_db: target compare database name
        :return: List of target databases (json)
        """ 
        try:
            
            #==========
            # JSON list
            #==========
            if targets_type_id == 1:
                targets = json.loads(targets_list)
                if len(targets) != 1:
                    raise ValueError("list of targets, !!! Not supported")
                return targets
            #==========
            # SQL query
            #==========
            elif targets_type_id == 2:
                raise Exception (f"query list of targets, !!! Not supported")

        except Exception as e:            
            raise Exception (f"failed to get list of targets: {e}")

    @drm_logger.log_decorator(logger) 
    def get_source_file(self, solution_path, solution_file_name, project_name):
        """ 
        returns the source file path 
        :param solution_path: solution path
        :param project_name: project_name
        :return: source file full path (String)
        """ 
        return solution_file_name
    
    @drm_logger.log_decorator(logger) 
    def get_fixed_connection_string(self, connection_string, project_targets_compare_db):
        """ 
        returns the fixed connection string using compare DB
        :param connection_string: connection string from the solution
        :param project_targets_compare_db: database name to connect into
        :return: fixed conneciton string (String)
        """ 
        return connection_string

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
        flyway_exec = self.upgrade_tool_file_name
        if os.name == "nt":  # only adjust for Windows
            base, ext = os.path.splitext(flyway_exec)
            if not ext:  # no extension provided
                flyway_exec += ".cmd"
        args_list.append(flyway_exec)
        
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
        
        if (self.connection_type_id == 2):
            db_obj = oracle.SqlPlus(self.run_script_tool_file_name, connection_string, target_name, sql_script_variables_list, upgrade_log_file)
        if (self.connection_type_id == 3):
            db_obj = postgresql.PostgreSQL(self.run_script_tool_file_name, connection_string, target_name, sql_script_variables_list, upgrade_log_file)            

        try:
            result = db_obj.run_script(upgrade_script)
            self.logger.info(f'Upgrade "{target_name}" finished successfully!!!')
            return result
        except Exception as e:
            if (project_fail_on_error):
                raise Exception(f'{e}')
            else:
                self.logger.warning(f'{e}')
