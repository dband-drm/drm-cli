import json
from modules import sqlite
from modules import parser_json_sqlite

INIT_SCHEMA_JSON = "init_drm_db/drm_db_schema.json"
INIT_DATA_JSON = "init_drm_db/drm_db_data.json"

class InitDB:
	def __init__(self, db_name = ""):
		"""
		Constructor
		:param db_name: SQLite databae name
		:return:
		"""
		self.db_name = db_name

	def create_tables(conn):
		"""
		Create schema
		:param conn: Connectionstring
		"""
		
		sql_command = "PRAGMA foreign_keys = ON;"
		sqlite.execute_command(conn, sql_command)

		parser = parser_json_sqlite.ParserJsonSqlite()

		f = open(INIT_SCHEMA_JSON)
		js = json.load(f)
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

		f.close()


	def load_data(conn):
		"""
		Load init (syste) Data
		:param conn: Connectionstring
		"""
		
		parser = parser_json_sqlite.ParserJsonSqlite()

		f = open(INIT_DATA_JSON)
		js = json.load(f)

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

		f.close()


	def create_drm_db(self):
		"""
		Creates DRM database with system Data
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
		InitDB.load_data(conn)

		#==========================
		# Close database connection
		#==========================
		sqlite.close_connection(conn)
