import json
from modules import sqlite

class ParserJsonSqlite:
	def __init__(self) -> None:
		pass

	def drop_table (self, table_name):
        """ 
        Generate a drop table if exists command
        :param table_name: Table name
        :return: SQL Command (string)
        """
		sql_command = "drop table if exists {table_name}".format(table_name = table_name)

		return sql_command


	def create_table (self, table_name, js_columns, js_constraints):
        """ 
        Generate a create table command including constraints
        :param table_name: Table name
        :param js_columns: JSON includes list of columns names, data types & sizes
        :param js_constraints: JSON includes list of constraints on the table
        :return: SQL Command (string)
        """
		first_column = True
		#=====================
		# Create a basic table
		#=====================
		sql_command = "create table {table_name} (".format(table_name = table_name)

		#==================================
		# Add columns definitions from list
		#==================================
		for js_column in js_columns:
			
			# Column name
			column_name = js_column['name']

			# Data type
			data_type = js_column['data_type']
			if(data_type.lower() == "string"):
				data_type = "varchar"

			# Length
			try:
				length = str(js_column['length'])
			except:
				length = None

			# Nullable?
			try:
				is_nullable = js_column['is_nullable']
			except:
				is_nullable = None

			# Defult value
			try:
				default = str(js_column['default'])
			except:
				default = None

			# Concatenate columns definition into basic table creation & build a command
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

		#======================================
		# Add constraints definitions from list
		#======================================
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


	def insert_row (self, table_name, columns_names, columns_values):
        """ 
        Generate an insert record into a table command
        :param table_name: Table name
        :param columns_names: list of columns
        :param columns_values: List of values respectively
        :return: SQL Command (string)
        """
		columns_names_list = ", ".join(columns_names)
		columns_values_list = ", ".join([f"'{value}'" if isinstance(value, str) else str(value) for value in columns_values])
		
		sql_command = "insert into {table_name} ({columns_names}) values ({columns_values})".format(table_name = table_name, columns_names = columns_names_list, columns_values = columns_values_list)
		return sql_command
