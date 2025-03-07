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
LOG_FILE_DEFAULT_NAME = "psql.log"

class PostgreSQL:

    logger = drm_logger.configure_logging("postgresql.PostgreSQL")

    @drm_logger.log_decorator(logger)
    def __init__(self, run_script_tool_file_name, connection_string, database_name=None, sql_script_variables_list=[], output_log_file=None):
        """ 
        Constructor
        :param run_script_tool_file_name: PostgreSQL client tool (psql)
        :param connection_string: Connection string to PostgreSQL
        :param database_name: Explicit database name to bypass connection string
        :param sql_script_variables_list: array of pairs of script variables (name, value)
        :param output_log_file: Explicit name of output log file
        """
        self.sql_script_variables_list = sql_script_variables_list
        self.output_log_file = output_log_file # os.path.join(current_working_directory, "log", LOG_FILE_DEFAULT_NAME)
        self.run_script_tool_file_name = run_script_tool_file_name
        

        # Parse connection string
         
        match = re.search(r'jdbc:postgresql://([\d\.]+):(\d+)/(\w+);username=(\w+);password=(\w+);', connection_string)

        if match:
            server, port, dbname, username, password = match.groups()
            self.server = server
            self.port = port
            self.database = dbname
            self.username = username
            self.password = password
        else:
            self.logger.error(f"Not valid connection string,  valid format 'url=jdbc:postgresql://server:port/db;username=user;password=pass;'")
            raise ValueError(f"Not valid connection string")
        
        #Override target DB
        if database_name is not None:
            self.database = database_name
 


    @drm_logger.log_decorator(logger)
    def execute_query(self, query_text):
        """ 
        Execute PostgreSQL query & return json result
        :param query_text: SQL query text
        :return: Query result (json)
        """ 
        try:
            cmd = [
                self.run_script_tool_file_name, "-h", self.server, "-p", self.port,
                "-U", self.username, "-d", self.database, "-c", query_text, "--csv"
            ]
            env = os.environ.copy()
            if self.password:
                env["PGPASSWORD"] = self.password
            
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
            cmd = [
                self.run_script_tool_file_name, "-h", self.server, "-p", self.port,
                "-U", self.username, "-d", self.database, "-f", script_name,
                "-o", self.output_log_file
            ]
            env = os.environ.copy()
            if self.password:
                env["PGPASSWORD"] = self.password
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=env)
        except Exception as e:
            self.logger.error(f"Script execution failed: {str(e)}")
            raise
