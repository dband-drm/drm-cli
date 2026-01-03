import sys
import os
import logging
import shutil
import datetime
import json
from shutil import ignore_patterns
from pathlib import Path
from modules import files_and_folders, drm_logger, crypto, init_db

current_working_directory = Path(__file__).parent.parent.resolve()

#===========
# Constrants
#===========
DRM_DB_JSON_PATH = "init_drm_db"
DRM_DB_JSON_FILE_NAME = "drm_db_data.json"
DRM_SCHEM_JSON_FILE_NAME = "drm_db_schema.json"
DRM_FOLDER_NAME = "drm"
DRM_UPGRADE_PATH = "upgrade"
DRM_UPGRADE_FILE_NAME = "main.config"
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

class Install:

    logger = drm_logger.configure_logging("installer_scratch.Install")

    @drm_logger.log_decorator(logger) 
    def __init__(self, drm_path, install_config, install_type, encryption_key): 
        self.drm_path = drm_path
        self.install_config = install_config   
        self.install_type = install_type
        self.encryption_key = encryption_key


    @drm_logger.log_decorator(logger) 
    def copy_drm_content(self, modules_js):
        '''
        This function copies the DRM content into the DRM  directory
        :param modules_js: List of modules to copy
        :return:
        '''
        try:

            self.logger.info('Copying DRM content...')
        
            drm_config_file = os.path.join(self.drm_path, DEPLOY_CONFIG_FILE_NAME)
            file = files_and_folders.Files(drm_config_file)
            # Configuration already exists --> already installed (stop the installation)
            if (file.check_file_exists()):
                raise Exception ("DRM already installed in given path. Please select another path or unsinatall before reinstall")
            try:
                # Get drm content from installer
                drm_source_path = os.path.join(current_working_directory, DRM_FOLDER_NAME)

                #============================================
                # Copy DRM content into destination directory
                #============================================
                # If destination directory (selected by the user) differ from installer --> Copy the drm content to it
                if (drm_source_path != self.drm_path):
                    shutil.copytree(drm_source_path, self.drm_path, dirs_exist_ok=False, ignore=ignore_patterns('*.pyc', '__pycache__'))
                    for module in modules_js:
                        source_module_file_name = os.path.join(current_working_directory, "modules", module)
                        target_module_file_name = os.path.join(self.drm_path, "modules", module)
                        shutil.copy(source_module_file_name, target_module_file_name)

            except Exception as e:
                #======================================================================================
                # At least one content already exists in destination directory --> Request to overwrite
                #======================================================================================
                if (e.errno == 17):
                    emptyfolder = files_and_folders.Folders.is_folder_empty(self.drm_path)
                    user_choice = "n"
                    if(emptyfolder == False):
                        user_choice = input(style.YELLOW + "Content already exists in given directory. Enter [Y]/N to overwrite content: " + style.RESET)
                    if (user_choice.lower() == "y" or emptyfolder == True):
                        if (drm_source_path != self.drm_path):
                            shutil.copytree(drm_source_path, self.drm_path, dirs_exist_ok=True, ignore=ignore_patterns('*.pyc', '__pycache__'))
                            for module in modules_js:
                                source_module_file_name = os.path.join(current_working_directory, "modules", module)
                                target_module_file_name = os.path.join(self.drm_path, "modules", module)
                                shutil.copyfile(source_module_file_name, target_module_file_name,)
                    else:
                        raise Exception (str(e))
                else:
                    raise Exception (str(e))
            if (drm_source_path != self.drm_path):
                self.logger.info('Content copied successfully!!!')

        except Exception as e:
            raise Exception ("failed to copy content into DRM directory, " + str(e))


    @drm_logger.log_decorator(logger) 
    def create_drm_db(self, install_type, encryption_key):
        '''
        This function creates the DRM Database & DB objects
        :param install_type: Installation type
        :param encryption_key: Encryption key
        :return:
        '''
        try:

            config_js = self.install_config.full_config['config']
            db_folder_name = config_js['db_folder_name'] 
            db_file_name = config_js['db_file_name'] 
            sqlite_file_ext = config_js['sqlite_file_ext']
            data_file_ext = config_js['data_file_ext']

            #===================================
            # Create DB directory in destination
            #===================================            
            db_directory = os.path.join(self.drm_path, db_folder_name)
            folder = files_and_folders.Folders(db_directory)
            folder.create_folder()

            #=========================
            # SQLite installation type
            #=========================
            if (install_type == "sqlite"):
                self.logger.info('Creating DRM database...')

                sqlite_db_file_name = db_file_name + "." + sqlite_file_ext
                db_name = os.path.join(db_directory, sqlite_db_file_name)
                if(encryption_key == ""):
                    encryption_key = None
                drm_db = init_db.InitDB(db_name, encryption_key)

                # Create Database & load system Data
                drm_db.create_drm_db()
                
            #=======================
            # JSON installation type
            #=======================
            else:
                self.logger.info('Creating DRM database (Json style)...')
                src_drm_db_json = os.path.join(current_working_directory, DRM_DB_JSON_PATH, DRM_DB_JSON_FILE_NAME)
                
                # copy JSON DB from installer into destination DB directory
                shutil.copy(src_drm_db_json, db_directory)
                old_drm_db_json = os.path.join(current_working_directory, db_directory, DRM_DB_JSON_FILE_NAME)
                if(encryption_key != "" and encryption_key != None):
                    drm_db = init_db.InitDB(old_drm_db_json, encryption_key)
                    js = drm_db.encrypt_drm_json_db()
                    # Encrypt sensitive data
                    with open(old_drm_db_json, "w") as file:
                        json.dump(js, file, indent=4)
                db_json_file_name = db_file_name + "." + data_file_ext
                new_drm_db_json = os.path.join(db_directory, db_json_file_name)
                shutil.move(old_drm_db_json, new_drm_db_json)
                
            drm_db_schema_json = os.path.join(current_working_directory, DRM_DB_JSON_PATH, DRM_SCHEM_JSON_FILE_NAME)
            shutil.copy(drm_db_schema_json, db_directory)
            self.logger.info('DRM database created successfully!!!')

        except Exception as e:
            raise Exception ("failed to create DRM database, " + str(e))


    @drm_logger.log_decorator(logger) 
    def create_drm_config(self, install_type, encryption_key):
        '''
        This function creates a new drm.config file
        :param install_type: Document the install type inside the drm.config
        :param encryption_key: Encryption key
        '''
        try:

            self.logger.info('Creating drm.config...')

            drm_version = self.install_config.full_config['drm_version']

            config_js = self.install_config.full_config['config']
            build_folder_name = config_js['build_folder_name'] 
            db_folder_name = config_js['db_folder_name'] 
            db_file_name = config_js['db_file_name']
            data_file_ext = config_js['data_file_ext']
            sqlite_file_ext = config_js['sqlite_file_ext']

            log_js = self.install_config.full_config['log']
            log_folder_name = log_js['folder_name']
            log_max_size_mb = log_js['max_size_mb']
            log_backup_count = log_js['backup_count']

           #=============================================
            # Create configuration DRM file in destination
            #=============================================
            drm_config_file = os.path.join(self.drm_path, DEPLOY_CONFIG_FILE_NAME)
            installer_user = os.getlogin()
            install_timestamp = str(datetime.datetime.now())
            security_text = "This drm cli was developed by d-band and it is amazing!!!"
            encrypted = False
            # If user chose encryption key --> encrypt the security_text
            if (encryption_key != "" and encryption_key !=None):
                crpt = crypto.Crypto(encryption_key)
                security_text = crpt.encrypt_string(security_text)
                encrypted = True

            # Build configiration JSON
            content = {
                "drm_version": drm_version,
                "installation_info":
                {
                    "installed_by": installer_user,
                    "installation_time": install_timestamp,
                    "installation_type": install_type,
                    "db_secured": encrypted,
                    "security_text": security_text
                },
                "config":
                {
                    "build_folder_name": build_folder_name,
                    "db_folder_name": db_folder_name,
                    "db_file_name": db_file_name,
                    "data_file_ext": data_file_ext,
                    "sqlite_file_ext": sqlite_file_ext				
                },
                "log":{
                    "folder_name": log_folder_name,
                    "max_size_mb": log_max_size_mb,
                    "backup_count": log_backup_count
                },
                "locations": [],
                "trace_flags": []
            }
            json_obj = json.dumps(content, indent=4)
            file = files_and_folders.Files(drm_config_file)
            file.write_file(json_obj)

            self.logger.info('drm.config created successfully!!!')

        except Exception as e:	
            raise Exception ("failed to create drm.config, " + str(e))


    @drm_logger.log_decorator(logger) 
    def run_installer(self):
        '''
        This function runs the installer BL
        '''
        try:
            #====================================
            # Create DRM directory & copy content
            #====================================
            modules_js = self.install_config.full_config['modules']
            Install.copy_drm_content(self, modules_js)

            #==============
            # Create DRM DB
            #==============
            Install.create_drm_db(self, self.install_type, self.encryption_key)

            #==================
            # Create drm.config
            #==================
            Install.create_drm_config(self, self.install_type, self.encryption_key)
            
        except Exception as e:
            raise Exception ("failed to upgrade the DRM, " + str(e))
