import os
import time
import shutil
import sys
import argparse
import json
import logging
from pathlib import Path
from getpass import getpass
from modules import drm_logger

current_working_directory = Path(__file__).parent.resolve()
drm_directory = Path(__file__).parent.resolve()

DEPLOY_CONFIG_FILE_NAME = "drm_deploy.config"

#================
# Printing colors
#================
class style():
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

#=================
# Read config file
#=================
class Config():
    def __init__(self,path = None):
		# Read file
        file = os.path.join(path, DEPLOY_CONFIG_FILE_NAME)

        try:

            f = open(file)
            js = json.load(f)

            self.full_config = js

            # Extract variables values configured
            self.drm_version = js['drm_version']
            
            installation_info_js = js['installation_info']
            self.installation_type = installation_info_js['installation_type']
            self.db_secured = installation_info_js['db_secured']
            self.security_text = installation_info_js['security_text']
            
            config_js = js['config']
            self.build_folder_name = config_js['build_folder_name']
            self.db_folder_name = config_js['db_folder_name']
            self.db_file_name = config_js['db_file_name']
            self.data_file_ext = config_js['data_file_ext']
            self.sqlite_file_ext = config_js['sqlite_file_ext']
            
            log_js = js['log']
            self.log_folder_name = log_js['folder_name']
            self.log_max_size_mb = log_js['max_size_mb']
            self.log_backup_count = log_js['backup_count']

            if 'locations' in js:
                for location in js['locations']:
                    if 'sqlpackage_path' in location:
                        self.sqlpackage_path = location['sqlpackage_path']
                    if 'sqlcmd_path' in location:
                        self.sqlcmd_path = location['sqlcmd_path']
        
            f.close()
        except FileNotFoundError as e:
            raise Exception(f"File not found: {file} in path: {path}")
        except Exception as e:
            raise Exception(f"An unexpected error occurred: {e}")


#=================
# uninstall
#=================
def uninstall(path :str,retry_attempts=5, delay=2):
        """ 
        Uninstall DRM
        :param path: DRM Path
        :param retry_attempts: retry_attempts
        :param delay: delay
        :return:None
        """ 
        logger.info(f"EXECUTION: Uninstall")
        #========================================
        # Uninstall
        #========================================
        # Get the current directory of this script
        #current_dir = os.path.dirname(os.path.abspath(__file__))
        current_dir = path
        logger.info("Install dir: {path}".format(path=path))
        # Delete the directory and all its contents

        try:
            # Attempt to delete the directory and all its contents
            for attempt in range(retry_attempts):
                try:
                    shutil.rmtree(current_dir)
                    logger.info(f"Successfully uninstalled the application from {current_dir}")
                    break
                except OSError as e:
                    
                    logger.info(f"Attempt {attempt + 1} of {retry_attempts}: The process cannot access the file because it is being used by another process. Retrying in {delay} seconds...")
                    time.sleep(delay)
                    
            else:
                raise Exception("Failed to uninstall after multiple attempts. Please close any open files and try again.")
        except Exception as e:
            raise Exception(f"An unexpected error occurred: {e}")

os.system('')
logger = None
#=======
# Helper
#=======
program = "uninstall.py"
description = "This is a DRM CLI, developed by d-band that deploys releases configured in the DRM database."
copyrights = "Copyright (C) 2023 d-band - All Rights Reserved"
 
parser = argparse.ArgumentParser(prog = program, description = description, epilog = copyrights)

parser.add_argument("-p", "-encryption_key(Specify encryption_key, none is not encrypted)", required = False)
parser.add_argument("-f", "-install_path(Specify install folder path)", required = False)
parser.add_argument("--F","--Force", action='store_true', default=False, required = False)
parser.add_argument("--trace", action='store_true', default=False, required = False)
    
args = parser.parse_args()

#=====
# Main
#=====
try:

    os.chdir(drm_directory)

	#==================================
	# Create constants by configuration 
	#==================================
    result = False
    if(args.f != None):
        path = args.f
        file_path = os.path.join(path, DEPLOY_CONFIG_FILE_NAME)
        result = os.path.exists(file_path)
    while(result ==  False):
        try:
            path = input('Please enter folder path for configuration ,q for exit:')
            if(path.lower() == "q"):
                raise Exception ("Wrong configuration folder path!!!")
            file_path = os.path.join(path, DEPLOY_CONFIG_FILE_NAME)
            result = os.path.exists(file_path)
        except Exception as e:
             raise Exception ("Wrong configuration folder path!!!")


    deploy_config = Config(path)
    DRM_VERSION = deploy_config.drm_version
    INSTALLATION_TYPE = deploy_config.installation_type
    DB_SECURED= deploy_config.db_secured
    SECURITY_TEXT = deploy_config.security_text
    BUILD_FOLDER_NAME = deploy_config.build_folder_name
    DB_FOLDER_NAME = deploy_config.db_folder_name
    DB_FILE_NAME = deploy_config.db_file_name
    DATA_FILE_EXT = deploy_config.data_file_ext
    SQLITE_FILE_EXT = deploy_config.sqlite_file_ext

    LOG_FOLDER_NAME = deploy_config.log_folder_name
    LOG_MAX_SIZE_MB = deploy_config.log_max_size_mb
    LOG_BACKUP_COUNT = deploy_config.log_backup_count

    
    #=================
    # Set logger level
    #=================
    
    try:
        logger_level = logging.INFO
        logger_mode = 1 #0-install , 1-deploy 
        if (args.trace):
            logger_level = logging.DEBUG

        os.environ["DRM_LOGGER_LEVEL"] = str(logger_level)
        os.environ["DRM_LOGGER_MODE"] = str(logger_mode)
        os.environ["LOG_FOLDER_NAME"] = str(LOG_FOLDER_NAME)
        os.environ["LOG_MAX_SIZE_MB"] = str(LOG_MAX_SIZE_MB)
        os.environ["LOG_BACKUP_COUNT"] = str(LOG_BACKUP_COUNT)
        logger = drm_logger.configure_logging("uninstall")

    except (ImportError, AttributeError):
        raise ('Failed to init logger')
    #===============
    # Import modules
    #===============
    from modules import auth
    #======================
    # Verify encryption key
    #======================
    encryption_key = None
    auth = auth.Auth()
    if (DB_SECURED):
        if not (args.p):
            if ("DRM_SECRET" in os.environ):
                encryption_key = os.environ["DRM_SECRET"]
            else:
                encryption_key = auth.set_password()
                #getpass(prompt='Please enter encryption key: ')
        else:
            encryption_key = args.p
            
        auth_valid =  auth.validate_password(encryption_key,SECURITY_TEXT)

        if (auth_valid == False):
            raise Exception ("Wrong encryption key!!!")
        logger.info("==================================")
    
    user_choice ="n"
    skip = True
    if not (args.F):
        user_choice = input(style.YELLOW + "Are you sure you want to uninstall DRM? Enter [Y]/N : " + style.RESET)
        skip = False
    if (user_choice.lower() == "n" or user_choice =='') and not(skip):
        logger.info("Bye Bye ...")

    else:
        uninstall(path)
    
    
    
except Exception as e:
    # Log any exceptions raised during the  execution
    if  (logger != None):
        logger.critical(f"{e}")
        logger.info(f"DRM uninstall failed!!!")
        logger.info('==================================')
        os.chdir(current_working_directory)
    else:
        print(f"Error: {e}")
