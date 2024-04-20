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
		# For each release
		table_name = "releases"
		for row in js[table_name]:

			#===============
			# Insert release
			#===============
			row_without_sons = {key: value for key, value in row.items() if key != "solutions"}
			columns = list(row_without_sons.keys())
			values = list(row_without_sons.values())
			sql_command = parser.insert_row(table_name, columns, values)
			print(sql_command)
			sqlite.execute_command(conn, sql_command)



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
