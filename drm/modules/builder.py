import sys
import os
import json
import shutil
import io
import zipfile
from modules import parser_sqlite_json
from modules import parser_json_json

BUILD_FOLDER_NAME = "bin"
CONFIG_FILE_NAME = "drm_deploy.config"
BUILD_FILE_NAME = "drm_deploy.json"
PACK_FILE_NAME = "deploy.drmpac"

class Release:
    def __init__(self, id, name = None, max_retries = None, is_active = None): 
        self.id = id       
        self.name = name       
        self.max_retries = max_retries       
        self.is_active = is_active       

class Solution:
    def __init__(self, release_id, id = None, name = None, ordinal = None, solution_type_id = None, path = None, is_active = None): 
        self.id = id       
        self.name = name       
        self.release_id = release_id       
        self.ordinal = ordinal       
        self.solution_type_id = solution_type_id       
        self.path = path       
        self.is_active = is_active       

class Connection:
    def __init__(self, solution_id, id = None, name = None, connection_type_id = None, connection_string = None, is_active = None): 
        self.id = id       
        self.name = name       
        self.solution_id = solution_id       
        self.connection_type_id = connection_type_id       
        self.connection_string = connection_string       
        self.is_active = is_active       

class Sql_Scripts_Variable:
    def __init__(self, solution_id, id = None, name = None, value = None): 
        self.id = id       
        self.name = name       
        self.solution_id = solution_id       
        self.value = value      

class Sql_Script:
    def __init__(self, solution_id, id = None, name = None, sql_text = None): 
        self.id = id       
        self.name = name       
        self.solution_id = solution_id       
        self.sql_text = sql_text      

class Project:
    def __init__(self, solution_id, id = None, name = None, ordinal = None, targets_compare_db = None, targets_type_id = None, targets_list = None, targets_sql_script_id = None, targets_sql_text = None, max_degree_in_parallel = None, timeout_in_min = None, sleep_time_in_sec = None, fail_on_error = None, is_active = None): 
        self.id = id       
        self.name = name       
        self.solution_id = solution_id       
        self.ordinal = ordinal      
        self.targets_compare_db = targets_compare_db      
        self.targets_type_id = targets_type_id      
        self.targets_list = targets_list      
        self.targets_sql_script_id = targets_sql_script_id      
        self.targets_sql_text = targets_sql_text      
        self.max_degree_in_parallel = max_degree_in_parallel      
        self.timeout_in_min = timeout_in_min      
        self.sleep_time_in_sec = sleep_time_in_sec      
        self.fail_on_error = fail_on_error      
        self.is_active = fail_on_error      

class Build:
    def __init__(self, drm_version, installation_type = "json"):   
        """ Constructor
        :param installation_type: Installation type (json/sqlite)
        :return:
        """
        self.installation_type = installation_type
        self.drm_version = drm_version

    def generate_release_full_details(self, release_id, connection_name):
        """ Generates full details of a release as JSON by id
        :param id: Release ID
        :return:
        """
        
        if (self.installation_type == "sqlite"):
            parser = parser_sqlite_json
        else:
            parser = parser_json_json

        #===========================================
        # Check if active release & connection exist
        #===========================================
        check_parser = json.loads(parser.Releases.check_release_by_id_and_connection_name(release_id, connection_name))           
        if (check_parser['release_id'] == None):
            raise Exception ('Release ID "' + str(release_id) + '" not found.' )
        elif (check_parser['connection_id'] == None):
            raise Exception (('No active connection "{connection_name}" is associated with release ID "' + str(release_id) + '".' ).format(connection_name = connection_name))
        

        #=============================
        # Create build (bin) directory
        #=============================
        current_working_directory = os.getcwd()
        build_dir = os.path.join(current_working_directory, BUILD_FOLDER_NAME)
        if (os.path.exists(build_dir)):
            shutil.rmtree(build_dir)
        if not(os.path.exists(build_dir)):
            os.mkdir(build_dir)
        
        release_js = {}
        
        #====================
        # Get Release details
        #====================
        release_obj = Release(release_id)
        release_parser = json.loads(parser.Releases.get_release_by_id(release_id, release_obj))           
        if (release_parser['is_active'] == 1):
            release_js.update(release_parser)

            #==========================
            # Get all Release Solutions
            #==========================
            solutions_js = {"solutions":[]}
            solution_obj = Solution(release_parser['id'])
            solutions_parser = json.loads(parser.Solutions.get_solutions_by_release_id(release_parser['id'], solution_obj))           
            for solution in solutions_parser['solutions']:
                if solution['is_active'] == 1:
                    solution_js = {}
                    solution_js.update(solution)

                    #=============================
                    # Get all Solution Connections
                    #=============================
                    connections_js = {"connections":[]}
                    connection_obj = Connection(solution['id'])
                    connections_parser = json.loads(parser.Connections.get_connection_by_solution_id_and_name(release_id, solution['id'], connection_name, connection_obj))           
                    for connection in connections_parser['connections']:
                        if connection['is_active'] == 1:
                            connections_js['connections'].append(connection)
                            solution_js.update(connections_js)                                

                    #======================================
                    # Get all Solution Sql_Script_Variables
                    #======================================
                    sql_scripts_variables_js = {"sql_scripts_variables":[]}
                    sql_scripts_variable_obj = Sql_Scripts_Variable(solution['id'])
                    sql_scripts_variables_parser = json.loads(parser.SqlScriptsVariables.get_sql_scripts_variables_by_solution_id(release_id, solution['id'], sql_scripts_variable_obj))           
                    for sql_scripts_variable in sql_scripts_variables_parser['sql_scripts_variables']:
                        sql_scripts_variables_js['sql_scripts_variables'].append(sql_scripts_variable)
                        solution_js.update(sql_scripts_variables_js)

                    #=============================
                    # Get all Solution Sql_Scripts
                    #=============================
                    sql_scripts_js = {"sql_scripts":[]}
                    sql_script_obj = Sql_Script(solution['id'])
                    sql_scripts_parser = json.loads(parser.SqlScripts.get_sql_scripts_by_solution_id(release_id, solution['id'], sql_script_obj))           
                    for sql_script in sql_scripts_parser['sql_scripts']:
                        sql_scripts_js['sql_scripts'].append(sql_script)
                        solution_js.update(sql_scripts_js)

                    #==========================
                    # Get all Solution projects
                    #==========================
                    projects_js = {"projects":[]}
                    project_obj = Project(solution['id'])
                    projects_parser = json.loads(parser.Projects.get_projects_by_solution_id(release_id, solution['id'], project_obj))           
                    for project in projects_parser['projects']:
                        projects_js['projects'].append(project)
                        solution_js.update(projects_js)

                    solutions_js['solutions'].append(solution_js)
                    
                    
                    release_js.update(solutions_js)

        else:
            raise Exception ('Release ID "' + str(release_id) + '" not found.' )

        #=======================================
        # generate deployment configuration file
        #=======================================
        version_js = {"drm_vrsion": self.drm_version}
        config_file_name = os.path.join(build_dir, CONFIG_FILE_NAME)
        with open(config_file_name, 'w') as f:
            json.dump(version_js, f)
        f.close() 

        #=======================
        # Create build JSON file
        #=======================
        build_file_name = os.path.join(build_dir, BUILD_FILE_NAME)
        with open(build_file_name, 'w') as f:
            json.dump(release_js, f)
        f.close() 
        
        #===============
        # Zip build file
        #===============
        pack_file_name = os.path.join(build_dir, PACK_FILE_NAME)
        with zipfile.ZipFile(pack_file_name, 'w', zipfile.ZIP_DEFLATED) as myzip:
            myzip.write(build_file_name, BUILD_FILE_NAME)
            myzip.write(config_file_name, CONFIG_FILE_NAME)
            
#        if os.path.exists(build_file_name):
#            os.remove(build_file_name)
#        if os.path.exists(config_file_name):
#            os.remove(config_file_name)
