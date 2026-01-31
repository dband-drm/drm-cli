import sys
import os
import logging
import shutil
import datetime
import json
from shutil import ignore_patterns
from pathlib import Path
from modules import files_and_folders, drm_logger, sqlite, parser_json_sqlite, parser_json_json,parser_sqlite_json

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

    logger = drm_logger.configure_logging("installer_upgrade.Install")

    @drm_logger.log_decorator(logger) 
    def __init__(self, drm_path, install_config, install_type, encryption_key, drm_config): 
        self.drm_path = drm_path
        self.install_config = install_config
        self.install_type = install_type
        self.encryption_key = encryption_key
        self.drm_config = drm_config  

        # Read main upgrade configuration file
        file_name = os.path.join(DRM_UPGRADE_PATH, DRM_UPGRADE_FILE_NAME)
        file = files_and_folders.Files(file_name)
        self.main_config = file.load_file()
        self.system_tables_type = ["dictionaries"]
        		
        # Read drm_deploy.config
        drm_config_file = os.path.join(drm_path, DEPLOY_CONFIG_FILE_NAME)
        fl = files_and_folders.Files(drm_config_file)
        self.drm_config_js = fl.load_file()

        # Redirect parser by installation type
        if (install_type == "json"):
            self.parser = parser_json_json.Generic
            self.json_parser = parser_json_json.Generic

            db_file_name = self.drm_config_js["config"]["db_file_name"] + "." + self.drm_config_js["config"]["data_file_ext"]
            db_path = self.drm_config_js["config"]["db_folder_name"]
            self.db_name = os.path.join(self.drm_path, db_path, db_file_name)
            self.Db = JsonDb
                                    
        else:
            self.parser = parser_json_sqlite.ParserJsonSqlite()
            self.json_parser = parser_json_json.Generic

            db_directory = os.path.join(drm_path, self.drm_config_js['config']['db_folder_name'])
            sqlite_db_file_name = self.drm_config_js['config']['db_file_name'] + "." + self.drm_config_js['config']['sqlite_file_ext']
            self.db_name = os.path.join(db_directory, sqlite_db_file_name)
            self.Db = SqliteDb

    @drm_logger.log_decorator(logger) 
    def read_version_config(self, version):	
		# Read file
        file_name = os.path.join(DRM_UPGRADE_PATH, version + ".config")
        file = files_and_folders.Files(file_name)
        return (file.load_file())    

    @drm_logger.log_decorator(logger) 
    def upgrade_drm_folders(self, drm_version_config):
        '''
        This function upgrades the DRM structured folders
        :param drm_version_config: DRM version config
        :return:
        '''
        try:

            self.logger.info('Upgrading DRM folders...')

            if ("folders" in drm_version_config):
                js = drm_version_config['folders']

                #============
                # Add folders
                #============
                if ("add" in js):
                    folders_js = js['add']
                    for folder in folders_js:
                        folder_name = os.path.join(self.drm_path, folder['target_path'], folder['name'])
                        fldr = files_and_folders.Folders(folder_name)
                        # Create folder
                        fldr.create_folder()

                #===============
                # Delete folders
                #===============
                if ("del" in js):
                    folders_js = js['del']
                    for folder in folders_js:
                        folder_name = os.path.join(self.drm_path, folder['target_path'], folder['name'])
                        fldr = files_and_folders.Folders(folder_name)
                        # Delete folder content recursively
                        fldr.delete_folder_content()
                        # Delete folder
                        fldr.delete_folder()

                self.logger.info('Folders upgraded successfully!!!')
            else:
                self.logger.info('Nothing to upgrade!!!')

        except Exception as e:
            raise Exception (str(e))
        

    @drm_logger.log_decorator(logger) 
    def upgrade_drm_binaries(self, drm_version_config):
        '''
        This function upgrades the DRM bin files
        :param drm_version_config: DRM version config
        :return:
        '''
        try:

            self.logger.info('Upgrading DRM binaries...')

            if ("bin" in drm_version_config):
                js = drm_version_config['bin']

                #=============
                # Add binaries
                #=============
                if ("add" in js):
                    files_js = js['add']
                    for file in files_js:
                        source_file_name = os.path.join(current_working_directory, file['source_path'], file['name'])
                        target_file_name = os.path.join(self.drm_path, file['target_path'], file['name'])
                        fl = files_and_folders.Files(source_file_name)
                        if (fl.check_file_exists()):
                            # Copy file
                            shutil.copy(source_file_name, target_file_name)

                #================
                # Update binaries
                #================
                if ("upd" in js):
                    files_js = js['upd']
                    for file in files_js:
                        source_file_name = os.path.join(current_working_directory, file['source_path'], file['name'])
                        target_file_name = os.path.join(self.drm_path, file['target_path'], file['name'])
                        fl = files_and_folders.Files(source_file_name)
                        if (fl.check_file_exists()):
                            # Copy file
                            shutil.copy(source_file_name, target_file_name)

                #================
                # Delete binaries
                #================
                if ("del" in js):
                    files_js = js['del']
                    for file in files_js:
                        target_file_name = os.path.join(self.drm_path, file['target_path'], file['name'])
                        fl = files_and_folders.Files(target_file_name)
                        # Delete folder content recursively
                        fl.delete_file()

                self.logger.info('Binaries upgraded successfully!!!')
            else:
                self.logger.info('Nothing to upgrade!!!')

        except Exception as e:
            raise Exception (str(e))


    @drm_logger.log_decorator(logger) 
    def upgrade_drm_database_schema(self, js):
        '''
        This function upgrades the DRM database schema
        :param js: DRM version config
        :return:
        '''
        try:

            db_js = js['schema']

            #======================================
            # Get latest upgrade schema definitions
            #======================================
            source_drm_db_schema_json = os.path.join(current_working_directory, DRM_DB_JSON_PATH, DRM_SCHEM_JSON_FILE_NAME)
            fl = files_and_folders.Files(source_drm_db_schema_json)
            source_js = fl.load_file()

            #=======================
            # Get TARGET schema JSON
            #=======================
            target_drm_db_schema_json = os.path.join(self.drm_path, self.drm_config_js["config"]["db_folder_name"], DRM_SCHEM_JSON_FILE_NAME)
            fl = files_and_folders.Files(target_drm_db_schema_json)
            target_js = fl.load_file()

            #======================
            # Update / Create table
            #======================
            ops = ["add", "upd"]
            for op in ops:                            
                if (op in db_js):
                    for db in db_js[op]:
                        name = db['name']
                        source_path = db['source_path']

                        # Find upgraded table in SOURCE JSON
                        source_table = None
                        for table in source_js[source_path]:
                            if table['name'] == name:
                                source_table = table
                                break

                        # If SOURCE table found, Find it in TARGET JSON
                        if source_table:
                            table_exists = any(table['name'] == source_table['name'] for table in target_js[source_path])
                        
                            # Table found in both SOURCE & TARGET --> Upgrade
                            if (table_exists):
                                # Get TARGET table
                                for table in target_js[source_path]:
                                    if (table['name'] == name):
                                        target_table = table
                                        # Find changes between SOURCE & TARGET tables
                                        changes_js = self.json_parser.compare_tables(target_table, source_table)
                                        # Differece includes columns changes
                                        if ('columns' in changes_js):
                                            for change in changes_js['columns']:
                                                self.Db.alter_table(self, "column", target_js, source_path, name, change, target_drm_db_schema_json)
                                        # Differece includes constraints changes
                                        if ('constraints' in changes_js):
                                            for change in changes_js['constraints']:
                                                self.Db.alter_table(self, "constraint", target_js, source_path, name, change, target_drm_db_schema_json)
                            else:
                                # Create table
                                self.Db.create_table(self, target_js, source_path, source_table, target_drm_db_schema_json)
                                
                
            #===========
            # Drop table
            #===========
            if ("del" in db_js):
                for db in db_js["del"]:
                    name = db['name']
                    source_path = db['source_path']
                    #Drop table
                    self.Db.drop_table(self, target_js, source_path, name, target_drm_db_schema_json)

        except Exception as e:
            raise Exception (str(e))

 
    @drm_logger.log_decorator(logger) 
    def upgrade_drm_database_data(self, js):
        '''
        This function upgrades the DRM database schema
        :param js: DRM version config
        :return:
        '''
        try:

            db_js = js['data']

            #==============================
            # Get latest schema definitions
            #==============================
            source_drm_db_schema_json = os.path.join(current_working_directory, DRM_DB_JSON_PATH, DRM_SCHEM_JSON_FILE_NAME)
            fl = files_and_folders.Files(source_drm_db_schema_json)
            source_schema_js = fl.load_file()

            #================
            # Get latest data
            #================
            source_drm_db_data_json = os.path.join(current_working_directory, DRM_DB_JSON_PATH, DRM_DB_JSON_FILE_NAME)
            fl = files_and_folders.Files(source_drm_db_data_json)
            source_data_js = fl.load_file()

            #===================================
            # Add / Update / Delete table's Data
            #===================================
            ops = ["add", "upd", "del"]
            for op in ops:
                if (op in db_js):
                    for db in db_js[op]:
                        name = db['name']
                        source_path = db['source_path']
                        schema_source_path = db['schema_source_path']

                        if (source_path in self.system_tables_type):
                            # Get table data
                            source_data = None                            
                            for table in source_data_js[source_path]:
                                if name in table:
                                    source_data = table
                                    break
                            
                            # Get table schema
                            source_table = None
                            for table in source_schema_js[schema_source_path]:
                                if table['name'] == name:
                                    source_table = table
                                    break

                            # Both SCHEMA & DATA found
                            if (source_data and source_table):
                                # Get table PK fields
                                constraints_js = None
                                if ('constraints' in source_table):
                                    constraints_js = source_table['constraints']
                                        
                                if (constraints_js) is not None:
                                    for constraint in constraints_js:
                                        if (constraint["type"] == "PK"):
                                            pk_columns = constraint["columns"]
                                            items = pk_columns.split(',')
                                            cleaned_items = [item.strip() for item in items]
                                            pk_columns = ','.join(cleaned_items)
                                else:
                                    pk_columns = ""
                                    for column in source_table['columns']:
                                        if (pk_columns):
                                            pk_columns += "," + column['name'].strip()
                                        else:
                                            pk_columns += column['name'].strip()

                                # Get target DATA
                                target_data = self.Db.get_table_data(self, name, source_path)
                                
                                # Find DATA changes
                                changes_js = self.json_parser.compare_table_data(name, target_data, source_data, pk_columns)
                                
                                for change in changes_js:
                                    row = change['row']
                                    action = change['action']
                                    # Insert row
                                    if (action == "add"):
                                        self.Db.insert_row(self, source_path, name, target_data, row)
                                    # Update row
                                    elif (action == "upd"):
                                        self.Db.update_row(self, source_path, name, target_data, row, pk_columns)
                                    # Delete row
                                    elif (action == "del"):
                                        self.Db.delete_row(self, source_path, name, target_data, row, pk_columns)                                                                 

        except Exception as e:
            raise Exception (str(e))


    @drm_logger.log_decorator(logger) 
    def upgrade_drm_database(self, drm_version_config):
        '''
        This function upgrades the DRM database
        :param drm_version_config: DRM version config
        :return:
        '''
        try:

            self.logger.info('Upgrading DRM database...')

            if ("db" in drm_version_config):
                js = drm_version_config['db']

                #===============
                # Upgrade Schema                
                #===============
                if ("schema" in js):
                    self.upgrade_drm_database_schema(js)

                #=============
                # Upgrade Data                
                #=============
                if ("data" in js):
                    self.upgrade_drm_database_data(js)

                self.logger.info('Database upgraded successfully!!!')
            else:
                self.logger.info('Nothing to upgrade!!!')

        except Exception as e:
            raise Exception (str(e))


    @drm_logger.log_decorator(logger) 
    def upgrade_drm_configs(self, drm_version_config):
        '''
        This function upgrades the DRM config files
        :param drm_version_config: DRM version config
        :return:
        '''
        try:

            self.logger.info('Upgrading DRM configuration...')

            if ("config" in drm_version_config):
                js = drm_version_config['config']

                #============
                # Add configs
                #============
                if ("add" in js):
                    files_js = js['add']
                    for file in files_js:
                        source_file_name = os.path.join(current_working_directory, file['source_path'], file['name'])
                        target_file_name = os.path.join(self.drm_path, file['target_path'], file['name'])
                        fl = files_and_folders.Files(source_file_name)
                        if (fl.check_file_exists()):
                            # Copy file
                            shutil.copy(source_file_name, target_file_name)

                #===============
                # Update configs
                #===============
                if ("upd" in js):
                    files_js = js['upd']
                    for file in files_js:
                        target_file_name = os.path.join(self.drm_path, file['target_path'], file['name'])
                        fl = files_and_folders.Files(target_file_name)
                        if (fl.check_file_exists()):
                            config_file_js = fl.load_file()

                            #=============
                            # Add new keys
                            #=============
                            if "add" in file['changes']:
                                keys_js = file['changes']['add']
                                for key in keys_js:
                                    path_parts = key['path'].split('/') if key['path'] else []  # Handle empty path
                                    current = config_file_js

                                    # If path is empty, modify the root
                                    if not path_parts:
                                        # Only set the value if the key does not already exist
                                        if key['name'] not in config_file_js:
                                            config_file_js[key['name']] = key['value']
                                        # If it's an array, do nothing
                                        elif isinstance(config_file_js[key['name']], list):
                                            continue  # Prevent overwriting an existing list
                                        else:
                                            continue  # If it's a dictionary, do nothing
                                        continue

                                    # Traverse the dictionary to the correct level
                                    for i, part in enumerate(path_parts):
                                        if isinstance(current, list):  
                                            current = None
                                            break
                                        
                                        # If the key doesn't exist, create the correct structure
                                        if part not in current:
                                            if i == len(path_parts) - 1:
                                                # Decide between list or object based on key['value']
                                                current[part] = [] if isinstance(key['value'], list) else {}
                                            else:
                                                current[part] = {}

                                        current = current[part]

                                    if current is not None:
                                        if isinstance(current, list):
                                            # Check if an identical object exists; if not, add a new one
                                            if not any(isinstance(item, dict) and item == {key['name']: key['value']} for item in current):
                                                current.append({key['name']: key['value']})
                                        elif isinstance(current, dict) and key['name'] not in current:
                                            current[key['name']] = key['value']

                                with open(target_file_name, "w") as file_:
                                    json.dump(config_file_js, file_, indent=4)

                            #============
                            # Update keys
                            #============
                            if "upd" in file['changes']:
                                keys_js = file['changes']['upd']
                                for key in keys_js:
                                    path_parts = key['path'].split('/')
                                    current = config_file_js

                                    # Traverse the dictionary to reach the target level
                                    for part in path_parts:
                                        if part in current:
                                            current = current[part]
                                        else:
                                            current = None
                                            break  # Exit early if path doesn't exist

                                    # Only update if the path exists
                                    if current is not None and isinstance(current, dict):  
                                        if key['name'] in current:
                                            current[key['name']] = key['value']

                                with open(target_file_name, "w") as file_:
                                    json.dump(config_file_js, file_, indent=4)
                                    
                            #============
                            # Delete keys
                            #============
                            if "del" in file['changes']:
                                keys_js = file['changes']['del']
                                for key in keys_js:
                                    path_parts = key['path'].split('/') if key['path'] else []  # Handle empty path
                                    current = config_file_js

                                    # If path is empty, delete directly from root
                                    if not path_parts:
                                        config_file_js.pop(key['name'], None)
                                    else:
                                        # Traverse the dictionary to the correct level
                                        for part in path_parts:
                                            if part in current:
                                                current = current[part]
                                            else:
                                                current = None
                                                break  # Exit if path doesn't exist

                                        # Only delete if the path exists
                                        if current is not None and isinstance(current, dict):
                                            current.pop(key['name'], None)

                                with open(target_file_name, "w") as file_:
                                    json.dump(config_file_js, file_, indent=4)

 
                #===============
                # Delete configs
                #===============
                if ("del" in js):
                    files_js = js['del']
                    for file in files_js:
                        target_file_name = os.path.join(self.drm_path, file['target_path'], file['name'])
                        fl = files_and_folders.Files(target_file_name)
                        # Delete folder content recursively
                        fl.delete_file()

                self.logger.info('Configuration upgraded successfully!!!')
            else:
                self.logger.info('Nothing to upgrade!!!')

        except Exception as e:
            raise Exception (str(e))


    @drm_logger.log_decorator(logger) 
    def run_installer(self):
        '''
        This function runs the installer BL
        '''
        try:
            supported_version = False
            upgraded = False
            # Use getpass.getuser() instead of os.getlogin() for WSL2 compatibility
            try:
                import getpass
                installer_user = getpass.getuser()
            except:
                installer_user = os.environ.get('USER', os.environ.get('USERNAME', 'unknown'))
            install_timestamp = str(datetime.datetime.now())
            

            for version in self.main_config["versions"]:
                if (version == self.drm_config.drm_version):
                    supported_version = True
                    self.logger.info('Current DRM: "' + version + '"')
                if (version != self.drm_config.drm_version and supported_version):
                    self.logger.info('Upgrading DRM to version: "' + version + '"')
                    upgraded = True

                    #========================================
                    # Read upgrade version configuration file
                    #========================================
                    drm_version_config = Install.read_version_config(self, version)

                    #================
                    # Upgrade folders
                    #================
                    Install.upgrade_drm_folders(self, drm_version_config)

                    #============
                    # Upgrade bin
                    #============
                    Install.upgrade_drm_binaries(self, drm_version_config)

                    #===============
                    # Upgrade config
                    #===============
                    Install.upgrade_drm_configs(self, drm_version_config)

                    #===========
                    # Upgrade db
                    #===========
                    Install.upgrade_drm_database(self, drm_version_config)

                    #===============================
                    # Document installation hitstory
                    #===============================
                    drm_version_config = '{' \
                                            '"config": {' \
                                                '"upd": [' \
                                                    '{' \
                                                        '"name": "drm_deploy.config",' \
                                                        '"target_path": "",' \
                                                        '"changes": {' \
                                                            '"add": [' \
                                                                '{"path": "", "name": "installation_info", "value": []},' \
                                                                '{"path": "installation_info", "name": "upgrades_history", "value": []},' \
                                                                '{"path": "installation_info/upgrades_history", "name": "version", "value": "' + version + ', installed_by: ' + installer_user + ', installation_time: ' + install_timestamp + '"}' \
                                                            ']' \
                                                        '}' \
                                                    '}' \
                                                ']' \
                                            '}' \
                                        '}'
                    drm_version_config = json.loads(drm_version_config)
                    Install.upgrade_drm_configs(self, drm_version_config)
                    
                    #==================================
                    # Update drm version in config file
                    #==================================
                    file_name = os.path.join(self.drm_path, DEPLOY_CONFIG_FILE_NAME)
                    fl = files_and_folders.Files(file_name)
                    config_file_js = fl.load_file()   
                    config_file_js['drm_version'] = version
                    with open(file_name, 'w', encoding='utf-8') as file:
                        json.dump(config_file_js, file, indent=4)
            
            if not (supported_version):
                raise Exception ('Upgrade from version "' + self.drm_config.drm_version + '" to version "' + version + '" is not supported')

            if not (upgraded):
                self.logger.info('No available upgrade version found')

        except Exception as e:
            raise Exception ("failed to upgrade the DRM, " + str(e))

class JsonDb:

    logger = drm_logger.configure_logging("installer_upgrade.Db")

    @drm_logger.log_decorator(logger) 
    def update_json_file(self, js, file_name):
        with open(file_name, "w") as file_:
            json.dump(js, file_, indent=4)

    @drm_logger.log_decorator(logger) 
    def create_table(self, target_js, source_path, source_table, target_drm_db_schema_json):
        target_js = self.json_parser.create_table(target_js, source_path, source_table) 
        JsonDb.update_json_file(self, target_js, target_drm_db_schema_json)

    @drm_logger.log_decorator(logger) 
    def alter_table(self, alter_type, target_js, source_path, name, change, target_drm_db_schema_json):       
        target_js = self.json_parser.alter_table(self, alter_type, target_js, source_path, name, change)
        JsonDb.update_json_file(self, target_js, target_drm_db_schema_json)

        if (self.install_type == 'json' and alter_type =='column'):
            # Delete column DATA in JSON
            fl = files_and_folders.Files(self.db_name)
            target_js = fl.load_file()
            column_name = change['name']
            target_js = self.json_parser.delete_column_data(target_js, 'dictionaries', name, column_name)
            JsonDb.update_json_file(self, target_js, self.db_name) 

 
    @drm_logger.log_decorator(logger) 
    def drop_table(self, target_js, source_path, name, target_drm_db_schema_json): 
        target_js = self.json_parser.drop_table(target_js, source_path, name)
        JsonDb.update_json_file(self, target_js, target_drm_db_schema_json)

        if (self.install_type == 'json'):
            # Drop table DATA in JSON
            fl = files_and_folders.Files(self.db_name)
            target_js = fl.load_file()
            target_js = self.json_parser.drop_table_data(target_js, 'dictionaries', name)
            JsonDb.update_json_file(self, target_js, self.db_name)

    @drm_logger.log_decorator(logger) 
    def get_table_data(self, name, source_path): 
        fl = files_and_folders.Files(self.db_name)
        target_js = fl.load_file()
        table_found = False
        for table in target_js[source_path]:
            if name in table:
                target_data = table
                table_found = True
                break
        if not table_found:
            target_data = {name: []}
        return target_data
    
    @drm_logger.log_decorator(logger) 
    def insert_row(self, source_path, name, target_data, row): 
        fl = files_and_folders.Files(self.db_name)
        target_js = fl.load_file()
        target_data = self.json_parser.insert_row(name, target_data, row)
        table_found = False
        for table_dict in target_js[source_path]:
            # Table found --> add new row
            if name in table_dict:
                table_found = True
                table_dict[name].append(row)

        if not table_found:
            # Table not found --> add new table & new row
            new_table = {name: [row]}
            target_js[source_path].append(new_table)
        JsonDb.update_json_file(self, target_js, self.db_name)


    @drm_logger.log_decorator(logger) 
    def update_row(self, source_path, name, target_data, row, pk_columns): 
        fl = files_and_folders.Files(self.db_name)
        target_js = fl.load_file()
        target_data = self.parser.update_row(name, target_data, row, pk_columns)
        for table_dict in target_js[source_path]:
            if name in table_dict:
                table_dict[name] = target_data[name]
                break
        JsonDb.update_json_file(self, target_js, self.db_name)

    @drm_logger.log_decorator(logger) 
    def delete_row(self, source_path, name, target_data, row, pk_columns): 
        fl = files_and_folders.Files(self.db_name)
        target_js = fl.load_file()
        target_data = self.parser.delete_row(name, target_data, row, pk_columns)
        for table_dict in target_js[source_path]:
            if name in table_dict:
                table_dict[name] = target_data[name]
                break
        JsonDb.update_json_file(self, target_js, self.db_name)


class SqliteDb:

    logger = drm_logger.configure_logging("installer_upgrade.Db")

    @drm_logger.log_decorator(logger) 
    def create_table(self, target_js, source_path, source_table, target_drm_db_schema_json):
        # Create table from database
        constraints_js = []
        if ('constraints' in source_table):
            constraints_js = source_table['constraints']
        sql_command = self.parser.create_table(source_table['name'], source_table['columns'], constraints_js)
        Sqlite.execute_command(self, self.db_name, sql_command)

        # Create table in schema JSON
        JsonDb.create_table(self, target_js, source_path, source_table, target_drm_db_schema_json)

    @drm_logger.log_decorator(logger) 
    def alter_table(self, alter_type, target_js, source_path, name, change, target_drm_db_schema_json): 
        db = parser_sqlite_json.Db(self.db_name)
        target_table = db.get_table_ddl (name)
        sql_commands = self.parser.alter_table(target_table, alter_type, change)
        if (sql_commands is not None):
            # Run upgrade changes on target
            commands = sql_commands.strip().split(';')
            for sql_command in commands:
                Sqlite.execute_command(self, self.db_name, sql_command)

        # Alter table in schema JSON
        JsonDb.alter_table(self, alter_type, target_js, source_path, name, change, target_drm_db_schema_json)      

    @drm_logger.log_decorator(logger) 
    def drop_table(self, target_js, source_path, name, target_drm_db_schema_json): 
        sql_command = self.parser.drop_table(name)
        Sqlite.execute_command(self, self.db_name, sql_command)

        # Delete table in schema JSON
        JsonDb.drop_table(self, target_js, source_path, name, target_drm_db_schema_json)

    @drm_logger.log_decorator(logger) 
    def get_table_data(self, name, source_path): 
        db = parser_sqlite_json.Db(self.db_name)
        target_data = db.get_table_data(name)
        return target_data

    @drm_logger.log_decorator(logger) 
    def insert_row(self, source_path, name, target_data, row): 
        sql_command = self.parser.insert_row(name, row.keys(), row.values())
        Sqlite.execute_command(self, self.db_name, sql_command)

    @drm_logger.log_decorator(logger) 
    def update_row(self, source_path, name, target_data, row, pk_columns): 
        sql_command = self.parser.update_row(name, row.keys(), row.values(), pk_columns)
        Sqlite.execute_command(self, self.db_name, sql_command)

    @drm_logger.log_decorator(logger) 
    def delete_row(self, source_path, name, target_data, row, pk_columns): 
        sql_command = self.parser.delete_row(name, row.keys(), row.values(), pk_columns)
        Sqlite.execute_command(self, self.db_name, sql_command)


class Sqlite:

    logger = drm_logger.configure_logging("installer_upgrade.Sqlite")

    @drm_logger.log_decorator(logger) 
    def execute_command(self, db_file, sql_command):
        conn = sqlite.create_connection(db_file)
        sqlite.execute_command(conn, sql_command)
        sqlite.close_connection(conn)

    @drm_logger.log_decorator(logger) 
    def execute_query(self, db_file, sql_command):
        conn = sqlite.create_connection(db_file)
        rows = sqlite.execute_query(conn, sql_command)
        sqlite.close_connection(conn)
        return(rows)
