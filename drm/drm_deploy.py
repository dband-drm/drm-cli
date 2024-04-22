import os
import sys
import argparse
import json
from getpass import getpass
from modules.builder import Build
from modules import crypto

DRYRUN_MODE = "DryRun"
DEPLOY_MODE = "Deploy"
DRM_CONFIG_FILE_NAME = "drm_deploy.config"

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

    current_working_directory = os.getcwd()
    drm_config_file = os.path.join(current_working_directory, DRM_CONFIG_FILE_NAME)
    f = open(drm_config_file)
    js = json.load(f)
    drm_version = js['drm_version']
    installation_type = js['installation_type']
    encrypted_security_text = js['security_text']
    crpt = crypto.Crypto(encryption_key)
    security_text = crpt.encrypt_string("This drm cli was developed by d-band and it is amazing!!!")
    if (security_text != encrypted_security_text):
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
    build = Build(drm_version, installation_type)
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
