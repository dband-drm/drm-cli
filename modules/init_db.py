import os
import json
import logging
from pathlib import Path
from modules import crypto, sqlite, parser_json_sqlite, files_and_folders, drm_logger

current_working_directory = Path(__file__).parent.parent.resolve()

#===========
# Constrants
#===========
INIT_SCHEMA_JSON = "init_drm_db/drm_db_schema.json"
INIT_DATA_JSON = "init_drm_db/drm_db_data.json"

class InitDB:

	logger = drm_logger.configure_logging("init_db.InitDB")

	@drm_logger.log_decorator(logger) 
	def __init__(self, db_name = "", encryption_key = None):
		"""
		Constructor
		:param db_name: SQLite databae name
		:return:
		"""
		self.db_name = db_name
		self.encryption_key = encryption_key
		level = os.environ.get('DRM_LOGGER_LEVEL')


	@drm_logger.log_decorator(logger) 
	def create_tables(conn):
		"""
		Create schema
		:param conn: Connectionstring
		:return:
		"""
		parser = parser_json_sqlite.ParserJsonSqlite()

		file_name = os.path.join(current_working_directory, INIT_SCHEMA_JSON)
		file = files_and_folders.Files(file_name)
		js = file.load_file()

		#==========================================================
		#Disable all FK constraints before dropping existing tables
		#==========================================================
		sql_command = "PRAGMA foreign_keys = OFF;"
		sqlite.execute_command(conn, sql_command)

		for js_table in js['tables']: 

			#=====================================
			# Drop table if exists before recreate
			#=====================================
			sql_command = parser.drop_table(js_table['name'])
			sqlite.execute_command(conn, sql_command)

			#=============
			# Create table
			#=============
			sql_command = parser.create_table(js_table['name'], js_table['columns'], js_table['constraints'])
			sqlite.execute_command(conn, sql_command)

		#=========================
		#Enable all FK constraints
		#=========================
		sql_command = "PRAGMA foreign_keys = ON;"
		sqlite.execute_command(conn, sql_command)
		

	@drm_logger.log_decorator(logger) 
	def load_data(conn, encryption_key):
		"""
		Load init (syste) Data
		:param conn: Connectionstring
		:param encryption_key: Encryption key
		:return:
		"""
		
		parser = parser_json_sqlite.ParserJsonSqlite()

		file_name = os.path.join(current_working_directory, INIT_DATA_JSON)
		file = files_and_folders.Files(file_name)
		js = file.load_file()

		#==================
		# Load dictionaries
		#==================
		for js_dictionary in js['dictionaries']:
			table_name = list(js_dictionary.keys())[0]
			for row in js_dictionary[table_name]:
				columns = list(row.keys())
				values = list(row.values())
				sql_command = parser.insert_row(table_name, row.keys(), row.values())
				sqlite.execute_command(conn, sql_command)

		#==================
		# Load Demo release
		#==================
		solution_id = 1
		connection_id = 1
		sql_scripts_variables_id = 1
		project_id = 1
		sql_script_id = 1

		# For each release
		table_name = "releases"
		for release_row in js[table_name]:

			table_name = "releases"

			#===============
			# Insert release
			#===============
			release_row_without_sons = {key: value for key, value in release_row.items() if key != "solutions"}
			columns = list(release_row_without_sons.keys())
			values = list(release_row_without_sons.values())
			sql_command = parser.insert_row(table_name, columns, values)
			sqlite.execute_command(conn, sql_command)

			id_row = {key: value for key, value in release_row.items() if key == "id"}
			release_id = list(id_row.values())[0]
			
			# For each solution
			table_name = "solutions"
			for solution_row in release_row[table_name]:

				#================
				# Insert solution
				#================
				solution_row_without_sons = {key: value for key, value in solution_row.items() if key not in ("projects", "sql_scripts_variables", "connections")}
				columns = list(solution_row_without_sons.keys())
				values = list(solution_row_without_sons.values())
				columns.append("id")
				values.append(solution_id)
				columns.append("ordinal")
				values.append(solution_id)
				columns.append("release_id")
				values.append(release_id)
				sql_command = parser.insert_row(table_name, columns, values)
				sqlite.execute_command(conn, sql_command)

				# For each connection
				table_name = "connections"
				for connection_row in solution_row[table_name]:
					#===================
					# Insert connections
					#===================
					if (encryption_key != "" and encryption_key != None):
						columns = []
						values = []
						crpt = crypto.Crypto(encryption_key)
						for key,value in connection_row.items():
							columns.append(key)
							if(key == "connection_string"):
								encrypted_text = crpt.encrypt_string(value)
								values.append(encrypted_text)
							else:
								values.append(value)
					else:
						columns = list(connection_row.keys())
						values = list(connection_row.values())    
					columns.append("id")
					values.append(connection_id)
					columns.append("solution_id")
					values.append(solution_id)
					sql_command = parser.insert_row(table_name, columns, values)
					sqlite.execute_command(conn, sql_command)

					connection_id += 1

				# For each sql_scripts_variables
				table_name = "sql_scripts_variables"
				if (table_name in solution_row):
					for sql_scripts_variable_row in solution_row[table_name]:
						#=============================
						# Insert sql_scripts_variables
						#=============================
						columns = list(sql_scripts_variable_row.keys())
						values = list(sql_scripts_variable_row.values())
						columns.append("id")
						values.append(sql_scripts_variables_id)
						columns.append("solution_id")
						values.append(solution_id)
						sql_command = parser.insert_row(table_name, columns, values)
						sqlite.execute_command(conn, sql_command)

						sql_scripts_variables_id += 1

				# For each sql_scripts_variables
				table_name = "projects"
				for project_row in solution_row[table_name]:
					#=============================
					# Insert sql_scripts_variables
					#=============================
					project_row_without_sons = {key: value for key, value in project_row.items() if key not in ("targets_sql_text")}
					columns = list(project_row_without_sons.keys())
					values = list(project_row_without_sons.values())
					columns.append("id")
					values.append(project_id)
					columns.append("ordinal")
					values.append(project_id)
					columns.append("solution_id")
					values.append(solution_id)

					#==================
					# Insert sql_script
					#==================
					script_name_name = "sql_scripts"
					sql_script_row = {key: value for key, value in project_row.items() if key in ("targets_sql_text")}
					if (len(list(sql_script_row.keys())) > 0):
						sql_text = list(sql_script_row.values())[0].replace("'", "''")
						script_columns = ["id", "name", "solution_id", "sql_text"]
						script_values = [sql_script_id, sql_script_id, solution_id, sql_text]
						sql_command = parser.insert_row(script_name_name, script_columns, script_values)
						sqlite.execute_command(conn, sql_command)
						columns.append("targets_sql_script_id")
						values.append(sql_script_id)
						sql_script_id += 1		
					
					sql_command = parser.insert_row(table_name, columns, values)
					sqlite.execute_command(conn, sql_command)

					project_id += 1

			solution_id += 1


	@drm_logger.log_decorator(logger) 
	def create_drm_db(self):
		"""
		Creates DRM database with system Data
		:return:
		"""
		#================
		# Create Database
		#================
		conn = sqlite.create_connection(self.db_name)

		#==============
		# Create tables
		#==============
		InitDB.create_tables(conn)

		#=================
		# Insert init Data
		#=================
		InitDB.load_data(conn, self.encryption_key)

		#==========================
		# Close database connection
		#==========================
		sqlite.close_connection(conn)


	@drm_logger.log_decorator(logger) 
	def encrypt_value_by_key(json_obj, key_to_encrypt, encryption_key):
		"""
		Replace value in json by key
		param json_obj: JSON
		param key_to_encrypt: key to encrypt in the JSON
		param encryption_key: Encryption key
		return: JSON with sensitive data encrypted (JSON)
		"""
		if isinstance(json_obj, dict):
			for key, value in json_obj.items():
				if key == key_to_encrypt:
					crpt = crypto.Crypto(encryption_key)
					encrypted_text = crpt.encrypt_string(value)						
					json_obj[key] = encrypted_text
				else:
					InitDB.encrypt_value_by_key(value, key_to_encrypt, encryption_key)
		elif isinstance(json_obj, list):
			for item in json_obj:
				InitDB.encrypt_value_by_key(item, key_to_encrypt, encryption_key)
		return json_obj


	@drm_logger.log_decorator(logger) 
	def encrypt_drm_json_db(self):
		"""
		Creates DRM database with system Data
		:return:
		"""
		file = files_and_folders(self.db_name)
		js = file.load_file()

		if(self.encryption_key != "" and self.encryption_key != None):
			js = InitDB.encrypt_value_by_key(js, "connection_string", self.encryption_key)

		return js
