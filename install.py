import sys
import argparse
import re
import os
import sqlite3
import datetime
import json
import shutil
from pathlib import Path
from modules import init_db
from modules import crypto

INSTALL_CONFIG_FILE_NAME = "install.config"
DRM_DB_JSON_PATH = "init_drm_db"
DRM_DB_JSON_FILE_NAME = "drm_db_data.json"
DRM_FOLDER_NAME = "drm"
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
		f = open(INSTALL_CONFIG_FILE_NAME)
		js = json.load(f)

		self.drm_version = js['drm_version'] 

		config_js = js['config']   
		self.build_folder_name = config_js['build_folder_name']      
		self.db_folder_name = config_js['db_folder_name']      
		self.db_file_name = config_js['db_file_name']      
		self.data_file_ext = config_js['data_file_ext']  
		self.sqlite_file_ext = config_js['sqlite_file_ext']    

		f.close()

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
	:return:
	"""
	try:
		print("")
		install_type = "none"
		while install_type not in ("json", "sqlite", ""):
			install_type = input("Enter DRM installation type([JSON]/SQLite): ").lower()
		if install_type == "":
			install_type = "sqlite"

		return install_type
	except Exception as e:
		raise Exception ("failed to get installation type, " + str(e)) 

def get_encryption_key():
	"""
	This function returns the encryption key entered by the user
	:return:
	"""
	try:
		flag = -1
		while flag == -1:
			encryption_key = input("Enter encryption key or enter '?' to see encryption key policy (" + style.YELLOW + "Make sure you save this key protected!!!" + style.RESET + "): ")
			if (encryption_key == "?"):
				flag = -1
				print("1. Minimum 8 characters.")
				print("2. The alphabet must be between [a-z]")
				print("3. At least one alphabet should be of Upper Case [A-Z]")
				print("4. At least 1 number or digit between [0-9].")
				print("5. At least 1 character from [ _ or @ or $ ].")
			elif (len(encryption_key)<=8):
				flag = -1
			elif not re.search("[a-z]", encryption_key):
				flag = -1
			elif not re.search("[A-Z]", encryption_key):
				flag = -1
			elif not re.search("[0-9]", encryption_key):
				flag = -1
			elif not re.search("[_@$]" , encryption_key):
				flag = -1
			#elif re.search("\s" , encryption_key):
		    #    	flag = -1
			else:
				flag = 0
			
			if flag == -1 and encryption_key != "?":
				print(style.RED + "The encryption key does not meet with validation policy!" + style.RESET)
		return encryption_key
	except Exception as e:
                raise Exception ("failed to get encryption key, " + str(e))

def get_drm_path():
	"""
	This function returns the installation path entered by the user
	:return:
	"""
	try:
		home = os.path.join(str(Path.home()), "drm")
		drm_path = ""
		while drm_path == "":
			drm_path = input("Enter path to install the DRM on (Default: " + home + "): ")
			if(drm_path == ""):
				drm_path = home
		return drm_path
	except Exception as e:
                raise Exception ("failed to get installation path, " + str(e))

def copy_drm_content(drm_path):
	'''
	This function copies the DRM content into the DRM  directory
	:param drm_path: DRM full path directory
	'''
	try:
		print("Copying DRM content...")

		drm_config_file = os.path.join(drm_path, DEPLOY_CONFIG_FILE_NAME)
		if (os.path.exists(drm_config_file)):
			raise Exception ("DRM already installed in given path. Please select another path or unsinatall before reinstall")
		try:
			current_working_directory = os.getcwd()
			drm_source_path = os.path.join(current_working_directory, DRM_FOLDER_NAME)
			if (drm_source_path != drm_path):
				shutil.copytree(drm_source_path, drm_path, dirs_exist_ok=False)

		except Exception as e:
			if (e.errno == 17):
				user_choice = input(style.YELLOW + "Content already exists in given directory. Enter [Y]/N to overwrite content: " + style.RESET)
				if (user_choice == "Y"):
					if (drm_source_path != drm_path):
						shutil.copytree(drm_source_path, drm_path, dirs_exist_ok=True)
				else:
					raise Exception (str(e))
		if (drm_source_path != drm_path):
			print("Content copied successfully!!!")
			print("")
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
		print("Creating drm.config...")

		drm_config_file = os.path.join(drm_path, DEPLOY_CONFIG_FILE_NAME)
		#installer_user = os.environ.get("USER")
		installer_user = os.getlogin()
		install_timestamp = str(datetime.datetime.now())
		crpt = crypto.Crypto(encryption_key)
		security_text = crpt.encrypt_string("This drm cli was developed by d-band and it is amazing!!!")

		content = {
			"drm_version": DRM_VERSION,
			"installation_info":
			{
				"installed_by": installer_user,
				"installation_time": install_timestamp,
				"installation_type": install_type,
				"security_text": security_text
			},
			"config":
			{
				"build_folder_name": BUILD_FOLDER_NAME,
				"db_folder_name": DB_FOLDER_NAME,
				"db_file_name": DB_FILE_NAME,
				"data_file_ext": DATA_FILE_EXT,
				"sqlite_file_ext": SQLITE_FILE_EXT				
			}
		}
		json_obj = json.dumps(content, indent=4)
		with open (drm_config_file, "w") as outfile:
			outfile.write(json_obj)

		print("File created successfully!!!")
		print("")

	except Exception as e:
                raise Exception ("failed to create drm.config, " + str(e))

def create_drm_db(drm_path, install_type):
	'''
	This function creates the DRM Database & DB objects
	:param drm_path: The directory to install the DRM in
	:param install_type: Installation type
	'''
	if (install_type == "sqlite"):
		try:
			print("Creating DRM DB...")

			# Create DB directory
			db_directory = os.path.join(drm_path, DB_FOLDER_NAME)
			if not(os.path.exists(db_directory)):
				os.mkdir(db_directory)
			sqlite_db_file_name = DB_FILE_NAME + "." + SQLITE_FILE_EXT
			db_name = os.path.join(db_directory, sqlite_db_file_name)
			drm_db = init_db.InitDB(db_name)
			# Create Database & load system Data
			drm_db.create_drm_db()

			print("DRM database created successfully!!!")
			print("")
		except Exception as e:
			raise Exception ("failed to create DRM database, " + str(e))
	else: #JSON
		try:
			print("Creating DRM DB (Json style)...")

			# Create DB directory
			db_directory = os.path.join(drm_path, DB_FOLDER_NAME)
			if not(os.path.exists(db_directory)):
				os.mkdir(db_directory)
			
			src_drm_db_json = os.path.join(DRM_DB_JSON_PATH, DRM_DB_JSON_FILE_NAME)
			shutil.copy(src_drm_db_json, db_directory)
			old_drm_db_json = os.path.join(db_directory, DRM_DB_JSON_FILE_NAME)
			db_json_file_name = DB_FILE_NAME + "." + DATA_FILE_EXT
			new_drm_db_json = os.path.join(db_directory, db_json_file_name)
			shutil.move(old_drm_db_json, new_drm_db_json)
			
			print("DRM database created successfully!!!")
			print("")
		except Exception as e:
			raise Exception ("failed to create DRM database, " + str(e))

def install_drm(drm_path, install_type, encryption_key):
	'''
	This function installs the DRM
	:param drm_path: The directory to install the DRM in
	:param install_type: Installation type
    :param encryption_key: Encryption key
	'''
	try:
		#print("==================================")
		print("Installing DRM...")
		print("")

		#====================================
		# Create DRM directory & copy content
		#====================================
		copy_drm_content(drm_path)

		#==============
		# Create DRM DB
		#==============
		create_drm_db(drm_path, install_type)

		#==================
		# Create drm.config
		#==================
		create_drm_config(drm_path, install_type, encryption_key)

		print(style.GREEN + "DRM installation finished successfully!!!" + style.RESET)
		print("==================================")

	except Exception as e:
		raise Exception ("installation failed, " + str(e))


try:
	
	os.system('')

	#==================================
	# Create constants by configuration 
	#==================================
	install_config = Config()
	DRM_VERSION = install_config.drm_version
	BUILD_FOLDER_NAME = install_config.build_folder_name
	DB_FOLDER_NAME = install_config.db_folder_name
	DB_FILE_NAME = install_config.db_file_name
	DATA_FILE_EXT = install_config.data_file_ext
	SQLITE_FILE_EXT = install_config.sqlite_file_ext
	
	#======================================
	# Get installation definition from user
	#======================================
	install_type = get_installation_type()
	encryption_key = get_encryption_key()
	drm_path = get_drm_path()
	print ("")

	#============
	# Install DRM
	#============
	install_drm(drm_path, install_type, encryption_key)

except Exception as e:
	print(style.RED + "Error: " + str(e) + style.RESET)
	print("")
	print(style.RED + "DRM installation failed!!!" + style.RESET)
	print("==================================")
