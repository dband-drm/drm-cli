import os
import sys
import argparse
import json
from getpass import getpass
from modules.builder import Build
from modules import crypto

DRYRUN_MODE = "DryRun"
DEPLOY_MODE = "Deploy"
DEPLOY_CONFIG_FILE_NAME = "drm_deploy.config"

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
    
class Config():
    def __init__(self):
        f = open(DEPLOY_CONFIG_FILE_NAME)
        js = json.load(f)
        
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
        
        f.close()

os.system('')

#=======
# Helper
#=======
program = "drm.py"
description = "This is a RDM CLI, developed by d-band that deploys releases configured in the DRM database."
copyrights = "Copyright (C) 2023 d-band - All Rights Reserved"
 
parser = argparse.ArgumentParser(prog = program, description = description, epilog = copyrights)
parser.add_argument("-c", "--connection", help = "Connection name", required = True)
parser.add_argument("-r", "--release", help = "Release ID", required = True)
parser.add_argument("--password", action='store_true', default=False, required = False)
parser.add_argument("--dryrun", action='store_true', default=False, required = False)
parser.add_argument("--deploy", action='store_true', default=False, required = False)
args = parser.parse_args()

try:

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

    #======================
    # Verify encryption key
    #======================
    if not (args.password):
        if ("DRM_SECRET" in os.environ):
            encryption_key = os.environ["DRM_SECRET"]
    else:
        encryption_key = getpass(prompt='Please enter encryption key: ')

    if encryption_key is None:
        raise Exception ("Encryption key not provided!!!")

    security_text = "This drm cli was developed by d-band and it is amazing!!!"
    if (DB_SECURED):
        crpt = crypto.Crypto(encryption_key)
        encrypted_text = crpt.encrypt_string(security_text)
        if (encrypted_text != SECURITY_TEXT):
            raise Exception ("Wrong encryption key!!!")

    #=========================
    # Determine execution mode
    #=========================
    executionMode = DRYRUN_MODE
    if (args.dryrun and args.deploy):
    	raise Exception("Error, command supports only single operation mode (--dryrun / --deploy)")
    if (args.deploy):
    	executionMode = DEPLOY_MODE
    else:
    	executionMode = DRYRUN_MODE

    #=========================
    # Get release name from DB
    #=========================
    print('Starting DRM deployment (Release ID: "{release_id}", Connection name: "{connection_name}")'.format(release_id = args.release, connection_name = args.connection))
    print("")
    
    print("Building release...")   
    build = Build(deploy_config)
    build.generate_release_full_details(args.release, args.connection)    
    print("Build finished successfully!!!")
    print("")

    print(style.GREEN + "DRM deployment finished successfully!!!" + style.RESET)
    print("==================================")
    print("")
    
except Exception as e:
	print(style.RED + "Error: " + str(e) + style.RESET)
	print("")
	print(style.RED + "DRM deployment failed!!!" + style.RESET)
	print("==================================")
