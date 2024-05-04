import sys
import argparse
import re
import os
import sqlite3
import datetime
import json
import shutil
from shutil import ignore_patterns
from pathlib import Path
from modules import drm_logger, init_db
from modules import crypto
import logging
from modules import files_and_folders

current_working_directory = Path(__file__).parent.resolve()

#===========
# Constrants
#===========
DRM_VERSION	= "1.0.0.0"
INSTALL_CONFIG_FILE_NAME = "install.config"
DRM_DB_JSON_PATH = "init_drm_db"
DRM_DB_JSON_FILE_NAME = "drm_db_data.json"
DRM_FOLDER_NAME = "drm"
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
		self.drm_version = DRM_VERSION 

		# Read file
		file_name = os.path.join(current_working_directory, INSTALL_CONFIG_FILE_NAME)
		file = files_and_folders.Files(file_name)
		js = file.load_file()

		# Extract variables values configured

		config_js = js['config']   
		self.build_folder_name = config_js['build_folder_name']      
		self.db_folder_name = config_js['db_folder_name']      
		self.db_file_name = config_js['db_file_name']      
		self.data_file_ext = config_js['data_file_ext']  
		self.sqlite_file_ext = config_js['sqlite_file_ext']    

		self.modules_js = js['modules'] 

		log_js = js['log']
		self.log_folder_name = log_js['folder_name']
		self.log_max_size_mb = log_js['max_size_mb']
		self.log_backup_count = log_js['backup_count']

#=======
# Helper
#=======
program = "install.py"
description = "This is a RDM Installer CLI, developed by d-band for Data deployments."
copyrights = "Copyright (C) 2023 d-band - All Rights Reserved"

parser = argparse.ArgumentParser(prog = program, description = description, epilog = copyrights)

#==========
# Functions
#==========
def get_installation_type():
	"""
	 This function returns the installation type entered by the user
	:return: installation type (string)
	"""
	try:
		#logger
		logger = logging.getLogger('get_installation_type')

		#========================
		# Enter installation type
		#========================
		install_type = "none"
		while install_type not in ("json", "sqlite", ""):
			install_type = input("Enter DRM installation type([JSON]/SQLite): ").lower()
		if install_type == "":
			logger.debug('Installation type selected default.')
			install_type = "sqlite"

		logger.debug('install_type: "{install_type"}'.format(install_type = install_type))
		return install_type
	except Exception as e:
		raise Exception ("failed to get installation type, " + str(e)) 

def get_encryption_key():
	"""
	This function returns the encryption key entered by the user
	:return: Encryption key (string)
	"""
	try:
		#logger
		logger = logging.getLogger('get_encryption_key')

		flag = -1
		while flag == -1:
			validate_policy = True
			#=====================
			# Enter encryption key
			#=====================
			encryption_key = input("Enter encryption key or enter '?' to see encryption key policy (Default, empty is not encrypted): ")
			
			# If user chooses clean text (not encrypted)
			if (encryption_key == "" or encryption_key == None):
				# Verify with the user
				user_choice = input(style.YELLOW + "Are you sure you want to keep sensitive Data as clear text? Enter [Y]/N to keep unsecured Data: " + style.RESET)
				if (user_choice.lower() == "y"):
					flag = 0
				else:
					validate_policy = False
					flag = -1

			# Encryption rules helper
			elif (encryption_key == "?"):
				flag = -1
				print("1. Minimum 8 characters.")
				print("2. The alphabet must be between [a-z]")
				print("3. At least one alphabet should be of Upper Case [A-Z]")
				print("4. At least 1 number or digit between [0-9].")
				print("5. At least 1 special character suc as !@#...")

			# Verify key policy
			elif (len(encryption_key)<=8):
				logger.debug('Validation rule (length) failed.')
				flag = -1
			elif not re.search("[a-z]", encryption_key):
				logger.debug('Validation rule ([a-z]) failed.')
				flag = -1
			elif not re.search("[A-Z]", encryption_key):
				logger.debug('Validation rule ([A-Z]) failed.')
				flag = -1
			elif not re.search("[0-9]", encryption_key):
				logger.debug('Validation rule ([0-9]) failed.')
				flag = -1
			elif not re.search("[~`!@#$%^&*()-_=+,<.>/?;:]" , encryption_key):
				logger.debug('Validation rule (Special Character) failed.')
				flag = -1
			else:
				flag = 0
			
			# selected key does not meet with policy
			if flag == -1 and encryption_key != "?" and validate_policy:
				logger.warning('The encryption key does not meet with validation policy!')
		return encryption_key
	except Exception as e:
				logger.error('Installation, get encryption key (Error: "%s")',str(e))
				logger.info('Failed to get encryption key')
				raise Exception ("failed to get encryption key, " + str(e))

def get_drm_path():
	"""
	This function returns the installation path entered by the user
	:return: installation directory (string)
	"""
	try:
		#logger
		logger = logging.getLogger('get_drm_path')

		#===========================================
		# Enter destination (installation) directory
		#===========================================
		# get the user default home directory
		home = os.path.join(str(Path.home()), "drm")
		drm_path = ""

		while drm_path == "":
			drm_path = input("Enter path to install the DRM on (Default: " + home + "): ")
			# Empty --> user default home directory
			if(drm_path == ""):
				logger.debug('DRM path use default')
				drm_path = home
		return drm_path
	except Exception as e:
		raise Exception ("failed to get installation path, " + str(e))

def copy_drm_content(drm_path, modules_js):
	'''
	This function copies the DRM content into the DRM  directory
	:param drm_path: DRM full path directory
	:param modules_js: List of modules to copy
	:return:
	'''
	try:
		#logger
		logger = logging.getLogger('copy_drm_content')

		logger.info('Copying DRM content...')
	
		drm_config_file = os.path.join(drm_path, DEPLOY_CONFIG_FILE_NAME)
		file = files_and_folders.Files(drm_config_file)
		# Configuration already exists --> already installed (stop the installation)
		if (file.check_file_exists()):
			logger.warning('DRM already installed in given path. Please select another path or unsinatall before reinstall')
			logger.info('DRM already installed')
			raise Exception ("DRM already installed in given path. Please select another path or unsinatall before reinstall")
		try:
			# Get drm content from installer
			drm_source_path = os.path.join(current_working_directory, DRM_FOLDER_NAME)

			#============================================
			# Copy DRM content into destination directory
			#============================================
			# If destination directory (selected by the user) differ from installer --> Copy the drm content to it
			logger.debug('drm_source_path: "{drm_source_path}", drm_path = "{drm_path}"'.format(drm_source_path = drm_source_path, drm_path = drm_path))
			if (drm_source_path != drm_path):
				logger.debug('Calling function shutil.copytree...')
				shutil.copytree(drm_source_path, drm_path, dirs_exist_ok=False, ignore=ignore_patterns('*.pyc', '__pycache__'))
				logger.debug('Function shutil.copytree exit successfully!!!')
				logger.debug('Copying modules...')
				for module in modules_js:
					source_module_file_name = os.path.join(current_working_directory, "modules", module)
					target_module_file_name = os.path.join(drm_path, "modules", module)
					logger.debug('source_module_file_name: "{source_module_file_name}", target_module_file_name = "{target_module_file_name}"'.format(source_module_file_name = source_module_file_name, target_module_file_name = target_module_file_name))
					logger.debug('Calling function shutil.copy...')
					shutil.copy(source_module_file_name, target_module_file_name)
					logger.debug('Function shutil.copcopyytree exit successfully!!!')

		except Exception as e:
			#======================================================================================
			# At least one content already exists in destination directory --> Request to overwrite
			#======================================================================================
			if (e.errno == 17):
				logger.warning('Content already exists in given directory')
				user_choice = input(style.YELLOW + "Content already exists in given directory. Enter [Y]/N to overwrite content: " + style.RESET)
				if (user_choice.lower() == "y"):
					logger.warning('Owerriding Content')
					if (drm_source_path != drm_path):
						shutil.copytree(drm_source_path, drm_path, dirs_exist_ok=True, ignore=ignore_patterns('*.pyc', '__pycache__'))
						for module in modules_js:
							source_module_file_name = os.path.join(current_working_directory, "modules", module)
							target_module_file_name = os.path.join(drm_path, "modules", module)
							logger.debug('Calling function shutil.copytree...')
							shutil.copyfile(source_module_file_name, target_module_file_name,)
							logger.debug('Function shutil.copytree exit successfully!!!')
				else:
					raise Exception (str(e))
		if (drm_source_path != drm_path):
			logger.info('Content copied successfully!!!')

	except Exception as e:
		raise Exception ("failed to copy content into DRM directory, " + str(e))

def create_drm_config(drm_path, install_type, encryption_key):
	'''
	This function creates a new drm.config file
	:param drm_path: DRM full path directory
	:param install_type: Document the install type inside the drm.config
    :param encryption_key: Encryption key
	'''
	try:
		#logger
		logger = logging.getLogger('create_drm_config')

		logger.info('Creating drm.config...')

		#=============================================
		# Create configuration DRM file in destination
		#=============================================
		drm_config_file = os.path.join(drm_path, DEPLOY_CONFIG_FILE_NAME)
		installer_user = os.getlogin()
		install_timestamp = str(datetime.datetime.now())
		security_text = "This drm cli was developed by d-band and it is amazing!!!"
		encrypted = False
		# If user chose encryption key --> encrypt the security_text
		if (encryption_key != ""):
			crpt = crypto.Crypto(encryption_key)
			logger.debug('Calling function crpt.encrypt_string...')
			security_text = crpt.encrypt_string(security_text)
			logger.debug('Function crpt.encrypt_string exit successfully!!!')
			encrypted = True

		# Build configiration JSON
		logger.debug('Build configiration JSON...')
		content = {
			"drm_version": DRM_VERSION,
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
				"build_folder_name": BUILD_FOLDER_NAME,
				"db_folder_name": DB_FOLDER_NAME,
				"db_file_name": DB_FILE_NAME,
				"data_file_ext": DATA_FILE_EXT,
				"sqlite_file_ext": SQLITE_FILE_EXT				
			},
			"log":{
				"folder_name": LOG_FOLDER_NAME,
				"max_size_mb": LOG_MAX_SIZE_MB,
				"backup_count": LOG_BACKUP_COUNT
			},
			"trace_flags": []
		}
		json_obj = json.dumps(content, indent=4)
		file = files_and_folders.Files(drm_config_file)
		logger.debug('Calling function write_file...')
		file.write_file(json_obj)
		logger.debug('Function write_file exit successfully!!!')
		logger.debug('Build configiration JSON finished successfully!!!')

		logger.info('drm.config created successfully!!!')

	except Exception as e:	
		raise Exception ("failed to create drm.config, " + str(e))

def create_drm_db(drm_path, install_type, encryption_key):
	'''
	This function creates the DRM Database & DB objects
	:param drm_path: The directory to install the DRM in
	:param install_type: Installation type
	:param encryption_key: Encryption key
	:return:
	'''
	try:
		#logger
		logger = drm_logger.configure_install_logging('create_drm_db')

		#===================================
		# Create DB directory in destination
		#===================================
		db_directory = os.path.join(drm_path, DB_FOLDER_NAME)
		folder = files_and_folders.Folders(db_directory)
		logger.debug('Calling function Folders.create_folder...')
		folder.create_folder()
		logger.debug('Function function Folders.create_folder exit successfully!!!')

		#=========================
		# SQLite installation type
		#=========================
		if (install_type == "sqlite"):
			logger.info('Creating DRM DB...')

			sqlite_db_file_name = DB_FILE_NAME + "." + SQLITE_FILE_EXT
			db_name = os.path.join(db_directory, sqlite_db_file_name)
			if(encryption_key == ""):
				encryption_key = None
			logger.debug('Calling function init_db.InitDB...')
			drm_db = init_db.InitDB(db_name, encryption_key)
			logger.debug('Function function init_db.InitDB exit successfully!!!')
			# Create Database & load system Data
			logger.debug('Calling function create_drm_db...')
			drm_db.create_drm_db()
			logger.debug('Function function create_drm_db exit successfully!!!')
			
			logger.info('DRM database created successfully!!!')

		#=======================
		# JSON installation type
		#=======================
		else:
			logger.info('Creating DRM DB (Json style)...')
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
			db_json_file_name = DB_FILE_NAME + "." + DATA_FILE_EXT
			new_drm_db_json = os.path.join(db_directory, db_json_file_name)
			shutil.move(old_drm_db_json, new_drm_db_json)
			
			logger.info('DRM database created successfully!!!')

	except Exception as e:
		raise Exception ("failed to create DRM database, " + str(e))

def install_drm(drm_path, install_type, encryption_key, modules_js):
	'''
	This function installs the DRM
	:param drm_path: The directory to install the DRM in
	:param install_type: Installation type
    :param encryption_key: Encryption key
    :param modules_js: list of modules to copy
	'''
	#logger
	logger = drm_logger.configure_install_logging('install_drm')
	logger.info('==================================')
	logger.info('Installing DRM...')

	#====================================
	# Create DRM directory & copy content
	#====================================
	logger.debug('Calling function copy_drm_content...')
	copy_drm_content(drm_path, modules_js)
	logger.debug('Function copy_drm_content exit successfully!!!')

	#==============
	# Create DRM DB
	#==============
	logger.debug('Calling function create_drm_db...')
	create_drm_db(drm_path, install_type, encryption_key)
	logger.debug('Function create_drm_db exit successfully!!!')

	#==================
	# Create drm.config
	#==================
	logger.debug('Calling function create_drm_config...')
	create_drm_config(drm_path, install_type, encryption_key)
	logger.debug('Function create_drm_config exit successfully!!!')

	logger.info('DRM installation finished successfully!!!')
	logger.info('==================================')


#=====
# Main
#=====
try:
	
	#logger
	logger = drm_logger.configure_install_logging('install')

	os.system('')

	#==================================
	# Create constants by configuration 
	#==================================
	logger.debug('Reading configuration...')
	install_config = Config()
	DRM_VERSION = install_config.drm_version
	logger.debug('DRM_VERSION: "%s")',DRM_VERSION)
	BUILD_FOLDER_NAME = install_config.build_folder_name
	logger.debug('BUILD_FOLDER_NAME: "%s")',BUILD_FOLDER_NAME)
	DB_FOLDER_NAME = install_config.db_folder_name
	logger.debug('DB_FOLDER_NAME: "%s")',DB_FOLDER_NAME)
	DB_FILE_NAME = install_config.db_file_name
	logger.debug('DB_FILE_NAME: "%s")',DB_FILE_NAME)
	DATA_FILE_EXT = install_config.data_file_ext
	logger.debug('DATA_FILE_EXT: "%s")',DATA_FILE_EXT)
	SQLITE_FILE_EXT = install_config.sqlite_file_ext
	logger.debug('SQLITE_FILE_EXT: "%s")',SQLITE_FILE_EXT)
	LOG_FOLDER_NAME = install_config.log_folder_name
	logger.debug('LOG_FOLDER_NAME: "%s")',LOG_FOLDER_NAME)
	LOG_MAX_SIZE_MB = install_config.log_max_size_mb
	logger.debug('LOG_MAX_SIZE_MB: "%s")',LOG_MAX_SIZE_MB)
	LOG_BACKUP_COUNT = install_config.log_backup_count
	logger.debug('LOG_BACKUP_COUNT: "%s")',LOG_BACKUP_COUNT)
	logger.debug('Configuration reading finished successfully!!!')

	modules_js = install_config.modules_js
	
	#======================================
	# Get installation definition from user
	#======================================
	logger.debug('Calling function get_installation_type...')
	install_type = get_installation_type()	    
	logger.debug('Function get_installation_type exit successfully!!!')

	logger.debug('Calling function get_encryption_key...')
	encryption_key = get_encryption_key()
	logger.debug('Function get_encryption_key exit successfully!!!')

	logger.debug('Calling function get_drm_path...')
	drm_path = get_drm_path()
	logger.debug('Function get_drm_path exit successfully!!!')
	
	#============
	# Install DRM
	#============
	logger.debug('Calling function install_drm...')
	install_drm(drm_path, install_type, encryption_key, modules_js)
	logger.debug('Function install_drm exit successfully!!!')

except Exception as e:
	logger.error('Error: "%s"',str(e))
	logger.info('DRM installation failed!!!')

