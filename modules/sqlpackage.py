import os
import json
import logging
import subprocess
from pathlib import Path
from shutil import which
from modules import drm_logger, files_and_folders, mssql

current_working_directory = Path(__file__).parent.parent.resolve()

#===========
# Constrants
#===========
DEPLOY_CONFIG_FILE_NAME = "drm_deploy.config"

class SqlPackage:

    logger = drm_logger.configure_logging("sqlpackage.SqlPackage")

    @drm_logger.log_decorator(logger) 
    def __init__(self, deploy_config, connection_type_id): 

        self.connection_type_id = connection_type_id

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
        sqlpackage_path = next(
            (
                (loc if isinstance(loc, dict) else json.loads(loc))["sqlpackage_path"]
                for loc in deploy_config.full_config.get("locations", [])
                if "sqlpackage_path" in (loc if isinstance(loc, dict) else json.loads(loc))
            ),
            None
        )
        if sqlpackage_path is not None:
            # Get utility location from configuration
            self.upgrade_tool_file_name = sqlpackage_path
        else:
            # Utility not configured --> serach
            missing_object = True
            self.logger.info("{app_name} utility path was not supplied in drm_deploy.config, searching (This may take a while)...".format(app_name = app_name))
            self.upgrade_tool_file_name = get_location (self, app_name)                    
            self.logger.info("{app_name} utility found & configured in drm_deploy.config for next deployments!!!".format(app_name = app_name))
            locations_js = json.loads('{"sqlpackage_path": "' + self.upgrade_tool_file_name + '"}')
            js['locations'].append(locations_js)

        app_name = "sqlcmd"
        sqlcmd_path = next(
            (
                (loc if isinstance(loc, dict) else json.loads(loc))["sqlcmd_path"]
                for loc in deploy_config.full_config.get("locations", [])
                if "sqlcmd_path" in (loc if isinstance(loc, dict) else json.loads(loc))
            ),
            None
        )
        if sqlcmd_path is not None:
            # Get utility location from configuration
            self.run_script_tool_file_name = sqlcmd_path
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
            # Sort targets
            def final_sort_key(item):
                # Priority items first, in given order
                if targets_priority and item in targets_priority:
                    return (0, targets_priority.index(item))
                
                # Compare-db always last
                if item == targets_compare_db:
                    return (2, item)
                
                # Normal items (alphabetical)
                return (1, item)
            
            #==========
            # JSON list
            #==========
            if targets_type_id == 1:
                items = json.loads(targets_list)
                if targets_exclude:
                    items = [i for i in items if i not in targets_exclude]
                return sorted(items, key=final_sort_key)
            #==========
            # SQL query
            #==========
            elif targets_type_id == 2:
                target_db_obj = mssql.MsSql(self.run_script_tool_file_name, connection_string)
                result = target_db_obj.execute_query(targets_sql_text)
                names = [entry["name"] for entry in json.loads(result)]
                if targets_exclude:
                    names = [n for n in names if n not in targets_exclude]
                return sorted(names, key=final_sort_key)
        except Exception as e:            
            raise Exception (f"failed to get list of targets: {e}")
               

    @drm_logger.log_decorator(logger) 
    def get_source_file(self, solution_path, solution_file_name, project_name):
        """ 
        returns the source file path 
        :param solution_path: solution path
        :param solution_file_name: solution file name
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
