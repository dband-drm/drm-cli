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

class Build:
    def __init__(self, installation_type = "json"):   
        """ Constructor
        :param installation_type: Installation type (json/sqlite)
        :return:
        """
        self.installation_type = installation_type

    def generate_release_full_details(self, release_id):
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
            # Get release details
            #====================
            release_obj = Release(release_id)
            release_parser = json.loads(parser_sqlite_json.Releases.get_release_by_id(release_id, release_obj))           
            if (release_parser['is_active'] == 1):
                release_js.update(release_parser)
                
                #==========================
                # Get all Release Solutions
                #==========================
                release_js.update(json.loads('{"solutions":[]}'))
                solution_obj = Solution(release_parser['id'])
                solutions_parser = json.loads(parser_sqlite_json.Solutions.get_solutions_by_release_id(release_parser['id'], solution_obj))           
                for solution in solutions_parser['solutions']:
                    if solution['is_active'] == 1:
                        release_js['solutions'].append(solution)

            else:
                raise Exception ("Release ID not found." )

        #=======================
        # Create build JSON file
        #=======================
        build_file_name = os.path.join(build_dir, BUILD_FILE_NAME)
        with open(build_file_name, 'w') as f:
            json.dump(release_js, f)
        f.close() 


