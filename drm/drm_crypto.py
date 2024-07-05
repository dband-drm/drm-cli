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

class EncryptResult:
    def __init__(self,execution_mode = EXECUTION_MODE_ENCRYPT):
        self.result = False
        self.execution_mode = execution_mode
        self.result_text = ""

class Encrypt:

    def __init__(self, deploy_config, encryption_key = "", execution_mode = EXECUTION_MODE_ENCRYPT, phrase = "", new_encryption_key=""): 
        self.deploy_config = deploy_config
        self.encryption_key = encryption_key
        self.execution_mode = execution_mode
        self.phrase = phrase
        self.new_encryption_key = new_encryption_key
        self.result_obj = EncryptResult(execution_mode) 
        build_dir = os.path.join(current_working_directory, self.deploy_config.build_folder_name)
        # SQLite to JSON
        if (deploy_config.installation_type == "sqlite"):
            self.parser = parser_sqlite_json
        else:
            self.parser = parser_json_json
        

    def update_connection_strings(self,data):
        """ 
        Update_connection_strings
        :return:
        """ 
        crpt = crypto.Crypto(self.encryption_key)
        crpt_new = crypto.Crypto(self.new_encryption_key)

        if isinstance(data, dict):
            for key, value in data.items():
                if key == "connections":#"connection_string":
                 conn = value
                 for item in conn:
                    for key, value in item.items():
                        if key == "connection_string":
                            item[key] = crpt_new.encrypt_string( crpt.decrypt_string(value))
                       # data[key] = crpt_new.encrypt_string( crpt.decrypt_string(value))
            else:
                self.update_connection_strings(value)
        elif isinstance(data, list):
            for item in data:
                self.update_connection_strings(item)

    def changepassword(self):
        """ 
        ChangePassword
        :return:
        """ 
        logger.info(f"EXECUTION: ChangePassword")
        #========================================
        # Choose DB & parser by installation type       
        #========================================
        # Move to parser  reencrypt
        # TODO ADD update config after reencrypt
        #SQLite
        if (self.deploy_config.installation_type == "sqlite"):
            db_file_name = os.path.join(current_working_directory, self.deploy_config.db_folder_name, self.deploy_config.db_file_name + "." + self.deploy_config.sqlite_file_ext)
            rows = self.parser.Connections.get_connections(db_file_name)
            crpt = crypto.Crypto(self.encryption_key)
            crpt_new = crypto.Crypto(self.new_encryption_key)
            new_rows = list()

            for r in rows:
                tuple_element = ((r[0],crpt_new.encrypt_string( crpt.decrypt_string(r[1]))))
                new_rows.append(tuple_element)
            new_rows = tuple(new_rows)
            self.parser.Connections.reencrypt(db_file_name,new_rows)
        # JSON
        else:
            db_file_name = os.path.join(current_working_directory, self.deploy_config.db_folder_name, self.deploy_config.db_file_name + "." + self.deploy_config.data_file_ext)
            file = files_and_folders.Files(db_file_name)
            drm_db_json = file.load_file()
            self.update_connection_strings(drm_db_json)
            json_obj = json.dumps(drm_db_json, indent=4)
            file.write_file(json_obj)

        #update config
        ##TODO
        logger.info("Updating Configuration")

        js = self.deploy_config.full_config
        security_text = "This drm cli was developed by d-band and it is amazing!!!"
        crpt = crypto.Crypto(self.new_encryption_key)
        encrypted_text = crpt.encrypt_string(security_text)
        installation_info = js['installation_info']
        installation_info['security_text'] = encrypted_text
        
        json_obj = json.dumps(js, indent=4)

        file = files_and_folders.Files( os.path.join(current_working_directory, DEPLOY_CONFIG_FILE_NAME))
        file.write_file(json_obj)

        logger.info("Configuration Updated")

        return True
    
    def command(self):
        """ 
        Encrypt_command
        :return:
        """ 
        try:
            if (execution_mode == EXECUTION_MODE_ENCRYPT):
                logger.info(f"EXECUTION_MODE: {EXECUTION_MODE_ENCRYPT}")
               
                crpt = crypto.Crypto(encryption_key)
                encrypted_text = crpt.encrypt_string(self.phrase)

                self.result_obj.result= True
                self.result_obj.result_text = encrypted_text
            
            elif(execution_mode == EXECUTION_MODE_CHANGEPASSWORD):
                logger.info(f"EXECUTION_MODE: {EXECUTION_MODE_CHANGEPASSWORD}")
                self.changepassword()
                self.result_obj.result= True

            #print(f"Command: {execution_mode},Encryption_key: {encryption_key},Text:{self.phrase},New_encryption_key {self.new_encryption_key}")
        except Exception as e:
            self.result_obj.result_text = e
        # Log any exceptions raised during the  execution
            logger.critical(f"{e}")
            logger.info(f"DRM encrypt failed!!!")
            logger.info('==================================')
        finally:
            return self.result_obj
        
        os.chdir(current_working_directory)

os.system('')

#=======
# Helper
#=======
program = "drm_crypto.py"
description = "This is a DRM CLI, developed by d-band that deploys releases configured in the DRM database."
copyrights = "Copyright (C) 2023 d-band - All Rights Reserved"
 
parser = argparse.ArgumentParser(prog = program, description = description, epilog = copyrights)
# Create a mutually exclusive group for the flags
group = parser.add_mutually_exclusive_group(required=True)

# Add the flags to the group
group.add_argument("-e", "--encrypt", help = "EncryptText", action='store_true')
group.add_argument("-c", "--changepassword", help = "ChangePassword",action='store_true')

parser.add_argument("-p", "--password", required = False)
parser.add_argument("-n", "--newpassword", required = False)
parser.add_argument("-t", "--text" , required = False)
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
    from modules import crypto, parser_sqlite_json,parser_json_json, files_and_folders
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
            

        security_text = "This drm cli was developed by d-band and it is amazing!!!"

        crpt = crypto.Crypto(encryption_key)
        encrypted_text = crpt.encrypt_string(security_text)
        if (encrypted_text != SECURITY_TEXT):
            raise Exception ("Wrong encryption key!!!")
        
    #=========================
    # Determine execution mode
    #=========================

    new_key = None
    phrase =None
    if (args.changepassword):
        execution_mode = EXECUTION_MODE_CHANGEPASSWORD
        if not (args.newpassword):
            new_key = getpass(prompt='Please enter new encryption key: ') 
        else:
            new_key = args.newpassword
        if new_key is None:
            raise Exception ("New Encryption key not provided!!!")
        
    if (args.encrypt):
        execution_mode = EXECUTION_MODE_ENCRYPT

        if(encryption_key == None and not DB_SECURED):
           raise Exception("Error, DB NOT SECURED for operation mode(--encrypt )")

        if not (args.text):
            phrase = input('Please enter phrase to  encrypt: ')
        else:
            phrase = args.text

        if phrase is None:
            raise Exception ("Phrase not provided!!!")

    logger.info("Finished DRM encrypt Validation")

    #=========================
    # Get release name from DB
    #=========================
    logger.info("Starting DRM encryption Operation ")
    
    build = Build(deploy_config)
    logger.debug(f"Debug Info Encrypt: {args.encrypt},Text: {phrase}, Newkey: ****, Execution mode:{execution_mode}, Changepassword:{args.changepassword}")
    
    #do encrypt operation
    encrypt = Encrypt(deploy_config,encryption_key,execution_mode,phrase,new_key)
    result_ = encrypt.command()
    #result
    if(result_.result):
        if(result_.execution_mode == EXECUTION_MODE_ENCRYPT):
            logger.info(f"Encrypted phrase : {result_.result_text}")
        elif(result_.execution_mode == EXECUTION_MODE_CHANGEPASSWORD):
            logger.info(f"Password changed ")
        logger.info("Finished DRM encrypt successfully")    
    else:
        logger.info("DRM encrypt failed")
        logger.info(f"Details: {result_.result_text}")
        raise Exception ("DRM encrypt operation failed")
    logger.info("==================================")
    os.chdir(current_working_directory)
    
    
    
except Exception as e:
    # Log any exceptions raised during the  execution
    logger.critical(f"{e}")
    logger.info(f"DRM encrypt failed!!!")
    logger.info('==================================')
    os.chdir(current_working_directory)

