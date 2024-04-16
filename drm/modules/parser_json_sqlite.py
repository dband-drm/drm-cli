import json
from lib import sqlite

class ParserJsonSqlite:
	def __init__(self) -> None:
		pass

	def drop_table (self, table_name):
		sql_command = "drop table if exists {table_name}".format(table_name = table_name)

		return sql_command


	def create_table (self, table_name, js_columns, js_constraints):
		first_column = True
		sql_command = "create table {table_name} (".format(table_name = table_name)
		for js_column in js_columns:
			
			column_name = js_column['name']
			data_type = js_column['data_type']
			if(data_type.lower() == "string"):
				data_type = "varchar"
			try:
				length = str(js_column['length'])
			except:
				length = None
			try:
				is_nullable = js_column['is_nullable']
			except:
				is_nullable = None
			try:
				default = str(js_column['default'])
			except:
				default = None

			if (first_column):
				first_column = False
			else:
				sql_command +=  ", "
			
			sql_command += column_name + " " + data_type
			if length is not None:
				sql_command += "(" + length + ")"
			if (is_nullable):
				sql_command += " NULL"
			else:
				sql_command += " NOT NULL"
			if	default is not None:
				if data_type in ("string", "text", "varchar", "char"):
					sql_command += " DEFAULT '{default}'".format(default = default)
				else:
					sql_command += " DEFAULT {default}".format(default = default)

		for js_constraint in js_constraints:
			try:
				constraint_name = js_constraint['name']
			except:
				constraint_name = None
			try:
				constraint_type = js_constraint['type']
			except:
				constraint_type = None
			try:
				constraint_columns = js_constraint['columns']
			except:
				constraint_columns = None
			try:
				constraint_ref_table = js_constraint['ref_table']
			except:
				ref_table = None
			try:
				constraint_ref_columns = js_constraint['ref_columns']
			except:
				constraint_ref_columns = None

			if (constraint_type == "PK"):
				sql_command += ", constraint {constraint_name} primary key ({constraint_columns})".format(constraint_name = constraint_name, constraint_columns = constraint_columns)
			if (constraint_type == "UQ"):
				sql_command += ", constraint {constraint_name} unique ({constraint_columns})".format(constraint_name = constraint_name, constraint_columns = constraint_columns)
			if (constraint_type == "FK"):
				sql_command += ", constraint {constraint_name} foreign key ({constraint_columns}) references {constraint_ref_table}({constraint_ref_columns})".format(constraint_name = constraint_name, constraint_columns = constraint_columns, constraint_ref_table = constraint_ref_table, constraint_ref_columns = constraint_ref_columns)
			
		sql_command += ");"
		
		return sql_command


	def insert_row (self, table_name, js_columns_names, js_columns_values):
		first_column = True
		sql_command = "insert into {table_name} (".format(table_name = table_name)

		for column_name in js_columns_names:
			if (first_column):
				first_column = False
			else:
				sql_command += ", "
			sql_command += 	column_name
		sql_command += 	") values ("

		first_column = True
		for column_value in js_columns_values:
			if (first_column):
				first_column = False
			else:
				sql_command += ", "
			sql_command += 	"'" + column_value + "'"
		sql_command += 	");"

		return sql_command
