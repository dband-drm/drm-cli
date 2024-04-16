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
		for js_dictionary in js['dictionaries']:
			for js_table in js_dictionary.keys():
				table_name = js_table
			for rows in js_dictionary.values():
				for row in rows:
					sql_command = sql_command = parser.insert_row(table_name, row.keys(), row.values())
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
