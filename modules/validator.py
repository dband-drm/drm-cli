import os
import json
import zipfile
import logging
from pathlib import Path
from modules import drm_logger

current_working_directory = Path(__file__).parent.parent.resolve()

#===========
# Constrants
#===========
BUILD_FILE_NAME = "drm_deploy.json"
PACK_FILE_NAME = "deploy.drmpac"

#====================
# Entities validators
#====================
class Release:

    logger = drm_logger.configure_logging("validator.Release")

    @drm_logger.log_decorator(logger) 
    def verify_fields(release):
        """ 
        Verify fields values
        :param release: release json
        :return:
        """       
        #=====================
        # Validate Max Retries
        #=====================
        if "max_retries" in release:
            if int(release['max_retries']) >  5:
                print('Warninig, high max retries is defined for the release!!! (defined "' + str(release['max_retries']) + '", highest advised: "5")')
        else:
            print('Warninig, max retries for the release is not defined. No retries is defined by default!!!')


class Solution:

    logger = drm_logger.configure_logging("validator.Solution")

    @drm_logger.log_decorator(logger) 
    def verify_active_exists(release):
        """ 
        Verify release has at least one active solution
        :param release: release json
        :return:
        """       
        valid = False
        
        if "solutions" in release:
            for solution in release['solutions']:
                if solution['is_active'] == True:
                    valid = True
        if not(valid):
            raise Exception ("No active Solution found!!!")

    @drm_logger.log_decorator(logger) 
    def verify_uniqueness(release):
        """ 
        Verify IDs & Names are unique
        :param release: release json
        :return:
        """       
        ids = []
        names = []
        
        for solution in release['solutions']:
            if solution['id'] not in ids:
                ids.append(solution['id'])
            else:
                raise Exception ('Solution ID "' + str(solution['id']) + '" found in multiple solutions!!!')
            if solution['name'] not in names:
                names.append(solution['name'])
            else:
                raise Exception ('Solution name "' + str(solution['name']) + '" found in multiple solutions!!!')

    @drm_logger.log_decorator(logger) 
    def verify_fields(release):
        """ 
        Verify fields values
        :param release: release json
        :return:
        """       
        for solution in release['solutions']:
            if solution['is_active'] == True:
                #=======================
                # Validate Solution Type
                #=======================
                if "solution_type_id" in solution:
                    if solution['solution_type_id'] not in [1, 2]:
                        raise Exception ('Solution type "' + str(solution['solution_type_id']) + '" in solution "' + str(solution['name']) + '" is not yet supported!!! (legal values: 1, 2)')
                else:
                    raise Exception ('No Solution Type defined for solution "' + str(solution['id']) + '"!!!')
                #==============
                # Validate path
                #==============
                if "path" in solution:
                    if not (os.path.exists(solution['path'])):
                        raise Exception ('Solution path "' + solution['path'] + '" not found for solution "' + str(solution['name']) + '"!!!')
                else:
                    raise Exception ('No path found for solution "' + str(solution['id']) + '"!!!')


class Project:

    logger = drm_logger.configure_logging("validator.Project")

    @drm_logger.log_decorator(logger) 
    def verify_active_exists(release):
        """ 
        Verify release has at least one active project in an active solution
        :param release: release json
        :return:
        """       
        valid = False
        #=========================================================
        # Verify at lease one Project exists under Active solution        
        #=========================================================
        if "solutions" in release:
            for solution in release['solutions']:
                if solution['is_active'] == True:
                    if "projects" in solution:
                        for project in solution['projects']:
                            if project['is_active'] == True:
                                valid = True
        if not(valid):
            raise Exception ("No active Project found!!!")

    @drm_logger.log_decorator(logger) 
    def verify_uniqueness(release):
        """ 
        Verify IDs are unique
        :param release: release json
        :return:
        """               
        for solution in release['solutions']:
            ids = []
            names = []
            if "projects" in solution:
                for project in solution['projects']:
                    if project['id'] not in ids:
                        ids.append(project['id'])
                    else:
                        raise Exception ('Multiple project ID "' + str(project['id']) + '" found in solution "' + str(solution['name']) + '"!!!')
                    #if project['name'] not in names:
                    #    names.append(project['name'])
                    #else:
                    #    raise Exception ('Multiple project Name "' + str(project['name']) + '" found in solution "' + str(solution['name']) + '"!!!')

    @drm_logger.log_decorator(logger) 
    def verify_fields(release):
        """ 
        Verify fields values
        :param release: release json
        :return:
        """      
        for solution in release['solutions']:
            if solution['is_active'] == True:
                if "projects" in solution:
                    for project in solution['projects']:
                        #============================
                        # Validate targets_compare_db
                        #============================
                        if "targets_compare_db" not in project:
                            raise Exception ('No targets compare DB defined for project "' + project['name'] + '" in solution "' + str(solution['id']) + '"!!!')
                        #=================
                        # Validate targets
                        #=================
                        if "targets_type_id" in project:
                            if project['targets_type_id'] in [1]:
                                if "targets_list" in project:
                                    if project['targets_list'] == None:
                                        raise Exception ('No targets list defined for project "' + project['name'] + '" in solution "' + str(solution['id']) + '"!!!')
                                else:
                                    raise Exception ('No targets list defined for project "' + project['name'] + '" in solution "' + str(solution['id']) + '"!!!')
                            elif project['targets_type_id'] in [2]:
                                if "targets_sql_script_id" not in project:
                                    raise Exception ('No Sql script ID is defined for project "' + project['name'] + '" in solution "' + str(solution['name']) + '"!!! (legal values: 1/2)')                                   
                                else:
                                    if project['targets_sql_script_id'] == None:
                                        raise Exception ('No Sql script ID is defined for project "' + project['name'] + '" in solution "' + str(solution['name']) + '"!!! (legal values: 1/2)')                                   
                                if "targets_sql_text" not in project:
                                    raise Exception ('No Sql script ID is defined for project "' + project['name'] + '" in solution "' + str(solution['name']) + '"!!! (legal values: 1/2)')                                   
                                else:
                                    if project['targets_sql_text'] == None:
                                        raise Exception ('No Sql script text is defined for project "' + project['name'] + '" in solution "' + str(solution['name']) + '"!!! (legal values: 1/2)')                                   
                            elif project['targets_type_id'] not in [1,2]:
                                raise Exception ('Invalid targets type "' + str(project['targets_type_id']) + '" is defined for project "' + project['name'] + '" in solution "' + str(solution['name']) + '"!!! (legal values: 1/2)')                                   
                        else:
                            raise Exception ('No targets type defined for project "' + project['name'] + '" in solution "' + str(solution['id']) + '"!!!')

#=====================
# Validator main class
#=====================
class Validate:

    logger = drm_logger.configure_logging("validator.Validate")

    @drm_logger.log_decorator(logger) 
    def __init__(self, deploy_config):   
        """ 
        Constructor
        :param installation_type: Installation type (json/sqlite)
        :return:
        """
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

    @drm_logger.log_decorator(logger) 
    def validate_release(self, connection_name):
        """ 
        Validate release JSON
        :return:
        """       
        try:

            #==========================
            # Release validation checks
            #==========================
            Release.verify_fields(self.release)

            #============================
            # Solutions validation checks
            #============================
            Solution.verify_active_exists(self.release)
            Solution.verify_uniqueness(self.release)
            Solution.verify_fields(self.release)
            
            #===========================
            # Projects validation checks
            #===========================
            Project.verify_active_exists(self.release)
            Project.verify_uniqueness(self.release)            
            Project.verify_fields(self.release)

        except Exception as e:
            raise Exception ("Validation failed, " + str(e))
