import json
import logging
from modules import sqlite, drm_logger

class ParserJsonSqlite:

	logger = drm_logger.configure_logging("parser_json_sqlite.ParserJsonSqlite")

	def __init__(self) -> None:
		pass

	@drm_logger.log_decorator(logger) 
	def drop_table (self, table_name):
		"""
		Generate a drop table if exists command
        :param table_name: Table name
        :return: SQL Command (string)
        """
		sql_command = "drop table if exists {table_name}".format(table_name = table_name)

		return sql_command


	@drm_logger.log_decorator(logger) 
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


	@drm_logger.log_decorator(logger) 
	def alter_table (self, target_table_js, change_type, change_js):
		""" 
        Generate a alter table command including constraints
        :param table_name: Table name
        :param js_columns: JSON includes list of columns names, data types & sizes
        :param js_constraints: JSON includes list of constraints on the table
        :return: SQL Command (string)
        """
		table_name = target_table_js['name']

		#===========================
		# Handle column modification
		#===========================
		if (change_type == "column"):

			action_type = change_js['action']

			#====================
			# Add / Delete column
			#====================
			if (action_type in ["add", "del"]):
				
				sql_command = "alter table {table_name} ".format(table_name = table_name)

				#==================
				# Column definition
				#==================	
				# Column name
				column_name = change_js['name']

				if (action_type == "add"):
					# Data type
					data_type = change_js['data_type']
					if(data_type.lower() == "string"):
						data_type = "varchar"

					# Length
					try:
						length = str(change_js['length'])
					except:
						length = None

					# Nullable?
					try:
						is_nullable = change_js['is_nullable']
					except:
						is_nullable = None

					# Defult value
					try:
						default = str(change_js['default'])
					except:
						default = None

					# Concatenate column definition into basic table alter & build a command
					sql_command += "ADD COLUMN " + column_name + " " + data_type
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


				elif (action_type == "del"):
					sql_command += " DROP  COLUMN " + column_name

			#==============
			# Modify column
			#==============
			else:

				# Column name
				column_name = change_js['name']
				
				for index, column in enumerate(target_table_js['columns']):
					if (column['name'] == column_name):
						target_table_js['columns'][index] = change_js
				target_table_ddl = self.create_table(table_name + "_new", target_table_js['columns'], target_table_js['constraints'])
				
				# Disable constraints
				sql_command = f"PRAGMA foreign_keys=OFF; -- Temporarily disable foreign keys"
				# Create a new table in target
				sql_command += f"\n{target_table_ddl}"
				# Copy data from old table to new in target
				sql_command += f"\nINSERT INTO {table_name}_new SELECT * FROM {table_name};"
				# Drop the old table
				sql_command += f"\nDROP TABLE {table_name};"
				# Rename the new table to the original table name
				sql_command += f"\nALTER TABLE {table_name}_new RENAME TO {table_name};"
				# Re-enable constraints
				sql_command += f"\nPRAGMA foreign_keys=ON; -- Re-enable foreign keys"

			
		#===============================
		# Handle constraint modification
		#===============================
		else: 
			action_type = change_js['action']

			# Constraint name
			constraint_name = change_js['name']
			constraint_exists = False
			
			for index, constraint in enumerate(target_table_js['constraints']):
				if (constraint['name'] == constraint_name):
					constraint_exists = True
					if (action_type in ["add", "upd"]):
						# Add or modify constraint
						target_table_js['constraints'][index] = change_js
					elif action_type == "del":
						# Delete the constraint from the target table
						del target_table_js['constraints'][index]
						break  # Exit the loop since we've found and removed the constraint
			if not constraint_exists and action_type == "add":
				target_table_js['constraints'].append(change_js)
			target_table_ddl = self.create_table(table_name + "_new", target_table_js['columns'], target_table_js['constraints'])
			
			# Disable constraints
			sql_command = f"PRAGMA foreign_keys=OFF;"
			# Create a new table in target
			sql_command += f"\n{target_table_ddl}"
			# Copy data from old table to new in target
			sql_command += f"\nINSERT INTO {table_name}_new SELECT * FROM {table_name};"
			# Drop the old table
			sql_command += f"\nDROP TABLE {table_name};"
			# Rename the new table to the original table name
			sql_command += f"\nALTER TABLE {table_name}_new RENAME TO {table_name};"
			# Re-enable constraints
			sql_command += f"\nPRAGMA foreign_keys=ON;"
		
		return sql_command


	@drm_logger.log_decorator(logger) 
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

	@drm_logger.log_decorator(logger) 
	def update_row (self, table_name, columns_names, columns_values, where_query):
		""" 
        Generate an update record in a table command
        :param table_name: Table name
        :param columns_names: list of columns
        :param columns_values: List of values respectively
        :return: SQL Command (string)
        """
		columns_names_list = ", ".join(columns_names)
		columns_values_list = ", ".join([f"'{value}'" if isinstance(value, str) else str(value) for value in columns_values])
		update_command = " set "
		for c in columns_names:
			for value in columns_values:
				update_command += f"{c} = '{value if isinstance(value, str) else str(value)}',"
		#remove last ,
		if(update_command != " set "):
			update_command = update_command[:-1]

		sql_command = f"update {table_name} {update_command} where {where_query}"
		return sql_command