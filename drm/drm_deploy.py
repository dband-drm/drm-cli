import os
import sys
import argparse
import json
import logging
from pathlib import Path
from getpass import getpass
from modules import drm_logger

current_working_directory = Path(__file__).parent.resolve()
drm_directory = Path(__file__).parent.resolve()

#===========
# Constrants
#===========
DRYRUN_MODE = "DryRun"
DEPLOY_MODE = "Deploy"
ALIGN_MODE = "Align"
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
    def __init__(self):
		# Read file
        file = os.path.join(current_working_directory, DEPLOY_CONFIG_FILE_NAME)
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

os.system('')

#=======
# Helper
#=======
program = "drm_deploy.py"
description = "This is a DRM CLI, developed by d-band that deploys releases configured in the DRM database."
copyrights = "Copyright (C) 2023 d-band - All Rights Reserved"
 
parser = argparse.ArgumentParser(prog = program, description = description, epilog = copyrights)
parser.add_argument("-c", "--connection", help = "Connection name", required = True)
parser.add_argument("-r", "--release", help = "Release ID", required = True)
parser.add_argument("-p", "-password", required = False)
parser.add_argument("--dryrun", action='store_true', default=False, required = False)
parser.add_argument("--deploy", action='store_true', default=False, required = False)
parser.add_argument("--align", action='store_true', default=False, required = False)

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
    deploy_config = Config()
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
        logger = drm_logger.configure_logging("drm_deploy")

    except (ImportError, AttributeError):
        raise ('Failed to init logger')
    #===============
    # Import modules
    #===============
    from modules.builder import Build
    from modules.validator import Validate
    from modules import crypto, deploy,auth
    
    #======================
    # Verify encryption key
    #======================
    encryption_key = None
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

    #=========================
    # Determine execution mode
    #=========================
    execution_mode = DRYRUN_MODE
    methods_count = 0
    if (args.dryrun):
        methods_count += 1
    if (args.deploy):
        methods_count += 1
    if (args.align):
        methods_count += 1

    if (methods_count > 1):
        raise Exception("Error, command supports only single operation mode (--dryrun / --deploy / --align)")

    if (args.deploy):
        execution_mode = DEPLOY_MODE
    elif (args.align):
        execution_mode = ALIGN_MODE
    else:
        execution_mode = DRYRUN_MODE

    #=========================
    # Get release name from DB
    #=========================
    logger.info('Starting DRM {execution_mode} (Release ID: "{release_id}", Connection name: "{connection_name}")'.format(execution_mode = execution_mode, release_id = args.release, connection_name = args.connection))
    
    logger.info("Building release...")   
    build = Build(deploy_config)
    build.generate_release_full_details(args.release, args.connection)    
    validate = Validate(deploy_config)
    validate.validate_release(args.connection)
    logger.info("Build finished successfully!!!")

    deploy = deploy.Deploy(deploy_config, encryption_key, execution_mode, args.connection)
    deploy.deploy_release()    

    logger.info(f"DRM {execution_mode} finished successfully!!!")
    logger.info("==================================")
    os.chdir(current_working_directory)
    
    
except Exception as e:
    # Log any exceptions raised during the  execution
    logger.critical(f"{e}")
    logger.info(f"DRM {execution_mode} failed!!!")
    logger.info('==================================')
    os.chdir(current_working_directory)
