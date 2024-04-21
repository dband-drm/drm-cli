import sys
import os
import json
import shutil
from modules import parser_sqlite_json

BUILD_FOLDER_NAME = "bin"
BUILD_FILE_NAME = "deploy.json"

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

class Project:
    def __init__(self, solution_id, id = None, name = None, ordinal = None, targets_compare_db = None): 
        self.id = id       
        self.name = name       
        self.solution_id = solution_id       
        self.ordinal = ordinal      
        self.targets_compare_db = targets_compare_db      

class Build:
    def __init__(self, installation_type = "json"):   
        """ Constructor
        :param installation_type: Installation type (json/sqlite)
        :return:
        """
        self.installation_type = installation_type

    def generate_release_full_details(self, release_id, connection_name):
        """ Generates full details of a release as JSON by id
        :param id: Release ID
        :return:
        """
        if (self.installation_type == "sqlite"):
            
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
            release_parser = json.loads(parser_sqlite_json.Releases.get_release_by_id(release_id, release_obj))           
            if (release_parser['is_active'] == 1):
                release_js.update(release_parser)
 
                #==========================
                # Get all Release Solutions
                #==========================
                solutions_js = {"solutions":[]}
                solution_obj = Solution(release_parser['id'])
                solutions_parser = json.loads(parser_sqlite_json.Solutions.get_solutions_by_release_id(release_parser['id'], solution_obj))           
                for solution in solutions_parser['solutions']:
                    if solution['is_active'] == 1:
                        solution_js = {}
                        solution_js.update(solution)

                        #=============================
                        # Get all Solution Connections
                        #=============================
                        connections_js = {"connections":[]}
                        connection_obj = Connection(solution['id'])
                        connections_parser = json.loads(parser_sqlite_json.Connections.get_connection_by_solution_id_and_name(solution['id'], connection_name, connection_obj))           
                        for connection in connections_parser['connections']:
                            if connection['is_active'] == 1:
                                connections_js['connections'].append(connection)
                                solution_js.update(connections_js)                                

                        #======================================
                        # Get all Solution Sql_Script_Variables
                        #======================================
                        sql_scripts_variables_js = {"sql_scripts_variables":[]}
                        sql_scripts_variable_obj = Sql_Scripts_Variable(solution['id'])
                        sql_scripts_variables_parser = json.loads(parser_sqlite_json.SqlScriptsVariables.get_sql_scripts_variables_by_solution_id(solution['id'], sql_scripts_variable_obj))           
                        for sql_scripts_variable in sql_scripts_variables_parser['sql_scripts_variables']:
                            sql_scripts_variables_js['sql_scripts_variables'].append(sql_scripts_variable)
                            solution_js.update(sql_scripts_variables_js)

                        solutions_js['solutions'].append(solution_js)
                        
                        
                        release_js.update(solutions_js)

            else:
                raise Exception ("Release ID not found." )

        #=======================
        # Create build JSON file
        #=======================
        build_file_name = os.path.join(build_dir, BUILD_FILE_NAME)
        with open(build_file_name, 'w') as f:
            json.dump(release_js, f)
        f.close() 


