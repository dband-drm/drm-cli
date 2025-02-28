import argparse
import os
import json
from pathlib import Path
import logging
from modules import drm_logger

current_working_directory = Path(__file__).parent.resolve()

#===========
# Constrants
#===========
INSTALL_CONFIG_FILE_NAME = "install.config"
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

#=================
# Read config file
#=================
class Config():
	def __init__(self):

		# Read file
		file_name = os.path.join(current_working_directory, INSTALL_CONFIG_FILE_NAME)
		file = files_and_folders.Files(file_name)
		js = file.load_file()
		self.full_config = js 


#=======
# Helper
#=======
program = "install.py"
description = "This is a DRM Installer CLI, developed by d-band for Data deployments."
copyrights = "Copyright (C) 2023 d-band - All Rights Reserved"

parser = argparse.ArgumentParser(prog = program, description = description, epilog = copyrights)
parser.add_argument("-p", "-encryption_key(Specify encryption_key, none is not encrypted)", required = False)
parser.add_argument("-d", "-install_type(Specify data structure)", required = False)
parser.add_argument("-f", "-install_path(Specify install folder path)", required = False)

parser.add_argument("--trace", action='store_true', default=False, required = False)
args = parser.parse_args()


#=================
# Set logger level
#=================
try:
    logger_level = logging.INFO
    logger_mode = 0 #0-install , 1-deploy ,2-crypto ,3-uninstall
    if (args.trace):
        logger_level = logging.DEBUG

    os.environ["DRM_LOGGER_LEVEL"] = str(logger_level)
    os.environ["DRM_LOGGER_MODE"] = str(logger_mode)
    os.environ["LOG_FOLDER_NAME"] = str('log')
    os.environ["LOG_MAX_SIZE_MB"] = str(10)
    os.environ["LOG_BACKUP_COUNT"] = str(3)
    logger = drm_logger.configure_logging("install")

except (ImportError, AttributeError):
    raise ('Failed to init logger')

#===============
# Import modules
#===============
from modules import init_db, crypto, files_and_folders, installer
from modules.auth import Auth


#=====================
# Read DRM config file
#=====================
class DrmConfig():
	def __init__(self, drm_path):
		# Read file
		file = os.path.join(drm_path, DEPLOY_CONFIG_FILE_NAME)
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


#==========
# Functions
#==========
@drm_logger.log_decorator(logger) 
def get_installation_type():
	"""
	 This function returns the installation type entered by the user
	:return: installation type (string)
	"""
	try:

		#========================
		# Enter installation type
		#========================
		install_type = "none"
		while install_type not in ("json", "sqlite", ""):
			install_type = input("Enter DRM installation type([JSON]/SQLite): ").lower()
		if install_type == "":
			install_type = "sqlite"

		return install_type
	except Exception as e:
		raise Exception ("failed to get installation type, " + str(e)) 

@drm_logger.log_decorator(logger) 
def get_drm_path():
	"""
	This function returns the installation path entered by the user
	:return: installation directory (string)
	"""
	try:

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
				drm_path = home
		return drm_path
	except Exception as e:
		raise Exception ("failed to get installation path, " + str(e))
	

@drm_logger.log_decorator(logger) 
def install_drm(drm_path, install_type, encryption_key, upgrade_mode):
	'''
	This function installs the DRM
	:param drm_path: The directory to install the DRM in
	:param install_type: Installation type
    :param encryption_key: Encryption key
	:param upgrade_mode: Is upgrade mode
	'''

	logger.info('==================================')
	logger.info('Installing DRM...')

	install_config = Config()	

	if (upgrade_mode):
		#========
		# Upgrade
		#========
		drm_conf = DrmConfig(drm_path)
		installer_obj = installer.Upgrade(drm_conf, drm_path, install_config)

	else:
		#=====================
		# Scratch installation
		#=====================
		installer_obj = installer.Install(drm_path, install_config, install_type, encryption_key)

	installer_obj.run_installer()

	logger.info('DRM installation finished successfully!!!')
	logger.info('==================================')


#=====
# Main
#=====
try:
	
	os.system('')

	#======================================
	# Get installation definition from user
	#======================================
	auth = Auth()
	upgrade_mode = False

	# Get drm path
	if not (args.f):
		drm_path = get_drm_path()
	else:
		drm_path = args.f
	# Check if already exists --> confirm upgrade	
	file_name = os.path.join(drm_path, DEPLOY_CONFIG_FILE_NAME)		
	file = files_and_folders.Files(file_name)
	if (files_and_folders.Files.check_file_exists(file)):
		upgrade_mode = True
		user_choice = input(style.YELLOW + "Do you want to upgrade the existing DRM? Enter [Y]/N to upgrade: " + style.RESET)
		if (user_choice.lower() == "y"):
			drm_conf = DrmConfig(drm_path)
		else:
			raise ValueError("Installation aborted")
		
	# Get encryption key
	if not(args.p):
		encryption_key = auth.set_password()
	elif  ((args.p) and ((args.p=="")or (args.p.lower()=="none"))):
		encryption_key = None
	else:
		auth_valid =  auth.validate_password_policy(password=args.p)
		if(auth_valid):
			encryption_key = args.p
		else:			
			while auth_valid == False :
				logger.info(" Not valid encryption key: {key}".format(key = args.p))

				encryption_key = auth.set_password()
				auth_valid =  auth.validate_password_policy(password=encryption_key)
			if(auth_valid == False ):
				raise ValueError(" Not valid encryption key: {key}".format(key = encryption_key))
	if (upgrade_mode):
		auth_valid = auth.validate_password(encryption_key, drm_conf.security_text)
		if (auth_valid == False):
			raise Exception ("Wrong encryption key!!!")


	# Get installation type
	if not (upgrade_mode):
		if not (args.d):
			install_type = get_installation_type()
		else:
			install_type = args.d 
			if(install_type not in ("json", "sqlite", "")):
				raise(" Not supported install_type: {type}".format(type = args.install_type))
			if install_type == "":
				install_type = "sqlite"
	else:
		install_type = drm_conf.installation_type
	
	#============
	# Install DRM
	#============
	install_drm(drm_path, install_type, encryption_key, upgrade_mode)
	os.chdir(current_working_directory)
	

except Exception as e:
    # Log any exceptions raised during the  execution
	logger.critical(f"{e}")
	logger.info(f"DRM installation failed!!!")
	logger.info('==================================')
	os.chdir(current_working_directory)
