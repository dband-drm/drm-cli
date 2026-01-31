import os
import subprocess
import json
import logging
import asyncio
import re
from pathlib import Path
from modules import drm_logger, files_and_folders

current_working_directory = Path(__file__).parent.parent.resolve()

#===========
# Constants
#===========
LOG_FILE_DEFAULT_NAME = "sqlplus.log"

class SqlPlus:

    logger = drm_logger.configure_logging("oracle.SqlPlus")

    @drm_logger.log_decorator(logger)
    def __init__(self, run_script_tool_file_name, connection_string, database_name=None, sql_script_variables_list=[], output_log_file=None):
        """ 
        Constructor
        :param run_script_tool_file_name: oracle client tool (sqlplus)
        :param connection_string: Connection string to Oracle
        :param database_name: Explicit database name to bypass connection string
        :param sql_script_variables_list: array of pairs of script variables (name, value)
        :param output_log_file: Explicit name of output log file
        """
        self.sql_script_variables_list = sql_script_variables_list
        self.output_log_file = output_log_file # os.path.join(current_working_directory, "log", LOG_FILE_DEFAULT_NAME)
        self.run_script_tool_file_name = run_script_tool_file_name
        
        # Parse connection string
        match1 = re.match(r'(?:url=)?jdbc:oracle:thin:@//([\d\.]+):(\d+)/(\w+);username=([^;]+);password=([^;]+);', connection_string) 
        match2 = re.match(r'(?:url=)?jdbc:oracle:thin:([^@]+)@([^/]+)//([\d\.]+):(\d+)/(\w+);', connection_string)
        
        if match1:
            server, port, dbname, username, password = match1.groups()
        elif match2:
            username, password, server, port, dbname = match2.groups()
        else:
            self.logger.error(f"Not valid connection string,  valid formats: 'url=jdbc:oracle:thin:@//server:port/db;username=user;password=pass;' or 'url=jdbc:oracle:thin:user@pass//server:port/db;'")
            raise ValueError(f"Not valid connection string")
        
        self.server = server
        self.port = port
        self.database = dbname
        self.username = username
        self.password = password
        
        #Override target DB
        if database_name is not None:
            self.database = database_name
 


    @drm_logger.log_decorator(logger)
    def execute_query(self, query_text):
        """ 
        Execute Oracle query & return json result
        :param query_text: SQL query text
        :return: Query result (json)
        """ 
        try:
            user = self.username
            password = self.password
            host = self.server
            port = self.port
            database = self.database

            conn_str = f"{user}/{password}@{host}:{port}/{database}"

            cmd = [
                self.run_script_tool_file_name,
                "-S",
                conn_str
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=env)
            output = result.stdout.strip()
            lines = output.split("\n")
            headers = lines[0].split(',')
            data = [dict(zip(headers, line.split(','))) for line in lines[1:] if line]
            return json.dumps(data, indent=4)
        except Exception as e:
            self.logger.error(f"Query execution failed: {str(e)}")
            raise

    @drm_logger.log_decorator(logger)
    def run_script(self, script_name):
        """ 
        Run SQL script
        :param script_name: Script name
        """
        try:
            user = self.username
            password = self.password
            host = self.server
            port = self.port
            database = self.database

            conn_str = f"{user}/{password}@{host}:{port}/{database}"

            with open(script_name, "r") as f:
                sql_script = f.read()
            sql_script += "\nEXIT;\n"
            cmd = [
                self.run_script_tool_file_name,
                "-S",
                conn_str
            ]
            result = subprocess.run(cmd, input=sql_script, capture_output=True, text=True, check=True)

        except subprocess.CalledProcessError as e: 
            # Split the string by newline and remove empty lines
            commands = [cmd.strip() for cmd in e.stdout.split('\n') if cmd.strip()] 
            # Get the last command (which should be the last non-empty string)
            last_command = commands[-1]  
            # Regular expression to extract the error message
            error_pattern = r'ERROR:.*'
            # Search for the error pattern in the log output
            match = re.search(error_pattern, e.stderr)
            if match:
                error_message = match.group()  
                # Extract the matched error message
            else:
                error_message = ''
            message = (f"Script execution failed: LastCommand: {last_command}, {error_message}")
            self.logger.error(f"{message}")
            raise Exception (f'{message}')

