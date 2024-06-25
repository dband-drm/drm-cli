import os
import subprocess
import json
import logging
import asyncio
from pathlib import Path
from modules import drm_logger, files_and_folders

current_working_directory = Path(__file__).parent.parent.resolve()

#===========
# Constrants
#===========
LOG_FILE_DEFAULT_NAME = "sqlcmd.log"

class MsSql:

    logger = drm_logger.configure_logging("mssql.MsSql")

    @drm_logger.log_decorator(logger) 
    def __init__(self, run_script_tool_file_name, connection_string, database_name = None, sql_script_variables_list = [], output_log_file = None):   
        """ 
        Constructor
        :param run_script_tool_file_name: SQL Server client tool
        :param connection_string: Connection string to SQL Server
        :param database_name: Explicit database name to bypass connection string
        :param sql_script_variables_list: array of pairs of script variables (name, value)
        :param output_log_file: Explicit name of output log file
        :return:
        """
        self.sql_script_variables_list = sql_script_variables_list
        self.output_log_file = output_log_file
        if (output_log_file == None):
            self.output_log_file = os.path.join (current_working_directory, "log", LOG_FILE_DEFAULT_NAME)
        self.run_script_tool_file_name = run_script_tool_file_name
        params_pair = connection_string.split(";")
        for conn_param in params_pair:
            if(len(conn_param) > 0):
                key, value = conn_param.split('=', 1)
                param_name = key.strip().lower()
                param_value = value.strip().lower()
                if(param_name in ['server', 'data source']):
                    self.server = param_value
                elif(param_name in ['database', 'initial catalog']):
                    self.database = param_value
                elif(param_name in ['user id', 'uid']):
                    self.username = param_value
                elif(param_name in ['password', 'pwd']):
                    self.password = param_value
                elif(param_name in ['trusted_connection', 'integrated security']):
                    if (param_value.lower() in ['yes', 'true']):
                        self.win_auth = True
                    else:
                        self.win_auth = False
        if database_name != None:
            self.database = database_name
        if(self.database == None):
            self.database = "master"
        

    @drm_logger.log_decorator(logger) 
    def execute_query(self, query_text):
        """ 
        Execute SQL Server query & return json result
        :param query_text: SQl Server query text
        :return: Query result (json)
        """ 
        try:
            # Construct the sqlcmd command with direct database
            cmd = [
                self.run_script_tool_file_name, '-S', self.server, '-d', self.database,
                '-U', self.username, '-P', self.password,
                '-Q', query_text, '-y', '0', '-s', ',', '-W', '-w', '8192', '-C'
            ]
            if (self.sql_script_variables_list != []):
                for var_name, var_value in self.sql_script_variables_list:
                    cmd.append('-v')
                    cmd.append(f'{var_name}={var_value}')
            # Run the command
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        except:
            # Construct the sqlcmd command without direct database
            cmd = [
                self.run_script_tool_file_name, '-S', self.server,
                '-U', self.username, '-P', self.password,
                '-Q', query_text, '-s', ',', '-W', '-w', '8192', '-C'
            ]
            if (self.sql_script_variables_list != []):
                for var_name, var_value in self.sql_script_variables_list:
                    cmd.append('-v')
                    cmd.append(f'{var_name}={var_value}')
            # Run the command
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Process the output
        output = result.stdout.strip()
        output_lines = output.split('\n')

        # Filter out lines with dashes under the headers and empty lines
        output_lines = [line for line in output_lines if line.strip() and not line.startswith('-')]

        # Find and exclude the "rows affected" line
        rows_affected_index = None
        for i, line in enumerate(output_lines):
            if 'rows affected' in line:
                rows_affected_index = i
                break
        if rows_affected_index is not None:
            output_lines.pop(rows_affected_index)

        # Extract headers and data
        headers = [header.strip() for header in output_lines[0].split(',')]
        data_lines = output_lines[1:]

        # Construct JSON object
        json_data = []
        for line in data_lines:
            values = [value.strip() for value in line.split(',')]
            row = dict(zip(headers, values))
            json_data.append(row)

        # Return JSON data
        return(json.dumps(json_data, indent=4))

    @drm_logger.log_decorator(logger) 
    def run_script(self, script_name):
        """ 
        Run script
        :param script_name: Script name
        :return:
        """ 
        try:
            # Construct the sqlcmd command with direct database
            cmd = [
                self.run_script_tool_file_name, '-S', self.server, '-d', self.database,
                '-U', self.username, '-P', self.password,
                '-i', script_name, '-y', '0', '-s', ',', '-W', '-w', '8192', '-C',
                '-o', self.output_log_file, "-v", "DatabaseName=" + self.database
            ]
            if (self.sql_script_variables_list != []):
                for var_name, var_value in self.sql_script_variables_list:
                    cmd.append('-v')
                    cmd.append(f'{var_name}={var_value}')
            # Run the command
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        except:
            try:
                # Construct the sqlcmd command without direct database
                cmd = [
                    self.run_script_tool_file_name, '-S', self.server,
                    '-U', self.username, '-P', self.password,
                    '-i', script_name, '-s', ',', '-W', '-w', '8192', '-C',
                    "-o", self.output_log_file, "-v", "DatabaseName=" + self.database
                ]
                if (self.sql_script_variables_list != []):
                    for var_name, var_value in self.sql_script_variables_list:
                        cmd.append('-v')
                        cmd.append(f'{var_name}={var_value}')
                # Run the command
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            except:
                pass

        # Check if process exit with a failure
        #if result.stderr:
        #    raise Exception (result.stderr)
        f = files_and_folders.Files(self.output_log_file)
        error_text, error_line = f.find_text_in_file("msg")
        if (error_line != None):
            error_text = f.get_line_in_file(error_line+1)
            error_text = error_text.replace("'", '"')
            raise Exception (f'Failed running script ""{script_name}"", {error_text}, see details in "{self.output_log_file}", line {error_line+1}.')

 