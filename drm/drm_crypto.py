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
EXECUTION_MODE_ENCRYPT = "Encrypt"
EXECUTION_MODE_CHANGEPASSWORD = "Changepassword"
DEPLOY_CONFIG_FILE_NAME = "drm_deploy.config"

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
class Encrypt:
    def __init__(self, deploy_config, encryption_key = "", execution_mode = EXECUTION_MODE_ENCRYPT, phrase = "", new_encryption_key=""): 
        self.deploy_config = deploy_config
        self.encryption_key = encryption_key
        self.execution_mode = execution_mode
        self.phrase = phrase
        self.new_encryption_key = new_encryption_key
        build_dir = os.path.join(current_working_directory, self.deploy_config.build_folder_name)
    def changepassword(self):
        """ 
        ChangePassword
        :return:
        """ 
        # todo 
        # by db type 
        # replace connection_string
    def command(self):
        """ 
        Encrypt_command
        :return:
        """ 
        try:
            if (execution_mode == EXECUTION_MODE_ENCRYPT):
                logger.info(f"EXECUTION_MODE: {EXECUTION_MODE_ENCRYPT}")

                print(EXECUTION_MODE_ENCRYPT)
                crpt = crypto.Crypto(encryption_key)
                encrypted_text = crpt.encrypt_string(self.phrase)
                return encrypted_text
            
            elif(execution_mode == EXECUTION_MODE_CHANGEPASSWORD):
                logger.info(f"EXECUTION_MODE: {EXECUTION_MODE_CHANGEPASSWORD}")
                changepassword()

            print(f"Command: {execution_mode},Encryption_key: {encryption_key},Text:{self.phrase},New_encryption_key {self.new_encryption_key}")
        except Exception as e:
        # Log any exceptions raised during the  execution
            logger.critical(f"{e}")
            logger.info(f"DRM encrypt failed!!!")
            logger.info('==================================')
        os.chdir(current_working_directory)
os.system('')

#=======
# Helper
#=======
program = "drm_crypto.py"
description = "This is a DRM CLI, developed by d-band that deploys releases configured in the DRM database."
copyrights = "Copyright (C) 2023 d-band - All Rights Reserved"
 
parser = argparse.ArgumentParser(prog = program, description = description, epilog = copyrights)
parser.add_argument("-e", "--encrypt", help = "EncryptText", action='store_true', default=False, required = False)
parser.add_argument("-c", "--changepassword", help = "ChangePassword",action='store_true', default=False, required = False)
parser.add_argument("-t", "--text", help = "Text", required = False)
parser.add_argument("-p", "--password", action='store_true', default=False, required = False)

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
        logger = drm_logger.configure_logging("drm_crypto")

    except (ImportError, AttributeError):
        raise ('Failed to init logger')
    #===============
    # Import modules
    #===============
    from modules.builder import Build
    from modules.validator import Validate
    from modules import crypto, deploy
    
    #======================
    # Verify encryption key
    #======================
    encryption_key = None
    if (DB_SECURED):
        if not (args.password):
            if ("DRM_SECRET" in os.environ):
                encryption_key = os.environ["DRM_SECRET"]
            else:
                encryption_key = getpass(prompt='Please enter encryption key: ')
        else:
            encryption_key = args.password
            
        if encryption_key is None:
            raise Exception ("Encryption key not provided!!!")

        security_text = "This drm cli was developed by d-band and it is amazing!!!"

        crpt = crypto.Crypto(encryption_key)
        encrypted_text = crpt.encrypt_string(security_text)
        if (encrypted_text != SECURITY_TEXT):
            raise Exception ("Wrong encryption key!!!")

    #=========================
    # Determine execution mode
    #=========================
    #execution_mode = encrypt
    if (args.encrypt and args.changepassword):
        raise Exception("Error, command supports only single operation mode (--encrypt / --changepassword)")

    new_key = None
    if (args.changepassword):
            #todo
            #remove text from arguments
            execution_mode = EXECUTION_MODE_CHANGEPASSWORD
            new_key = getpass(prompt='Please enter new encryption key: ')    
        
    else:
        execution_mode = EXECUTION_MODE_ENCRYPT
            
        if(encryption_key == None and not DB_SECURED):
           raise Exception("Error, DB NOT SECURED for operation mode(--encrypt )")

    #=========================
    # Get release name from DB
    #=========================
    logger.info("Starting DRM encryption Operation ")
    
    build = Build(deploy_config)

    print(f" Encrypt: {args.encrypt},Text: {args.text}, Newkey: {new_key}, Execution mode:{execution_mode}, Changepassword:{args.changepassword}")
    encrypt = Encrypt(deploy_config,encryption_key,execution_mode,args.text,new_key)
    encryptedText = encrypt.command()

    logger.info(f"Encrypted phrase : {encryptedText}")

    logger.info("Finished DRM encrypt successfully")
    logger.info("==================================")
    os.chdir(current_working_directory)
    
    
except Exception as e:
    # Log any exceptions raised during the  execution
    logger.critical(f"{e}")
    logger.info(f"DRM encrypt failed!!!")
    logger.info('==================================')
    os.chdir(current_working_directory)

