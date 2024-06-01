import subprocess
import json
import logging
from modules import drm_logger

class MsSql:

    logger = drm_logger.configure_logging("mssql.MsSql")

    @drm_logger.log_decorator(logger) 
    def __init__(self, run_script_tool_file_name, connection_string):   
        """ 
        Constructor
        :param run_script_tool_file_name: SQL Server client tool
        :param connection_string: Connection string to SQL Server
        :return:
        """
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
        if(self.database == None):
            self.database = "master"
        

    @drm_logger.log_decorator(logger) 
    def execute_query(self, query_text):
        """ 
        Execute SQl Server query & return json result
        :param query_text: SQl Server query text
        :return: Query result (json)
        """ 
        # Construct the sqlcmd command
        cmd = [
            'sqlcmd', '-S', self.server, '-d', self.database,
            '-U', self.username, '-P', self.password,
            '-Q', query_text, '-y', '0', '-s', ',', '-W', '-w', '8192'
        ]

        # Execute the command and capture the output
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        except:
            cmd = [
                'sqlcmd', '-S', self.server,
                '-U', self.username, '-P', self.password,
                '-Q', query_text, '-s', ',', '-W', '-w', '8192'
            ]
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

        # Print JSON data
        return(json.dumps(json_data, indent=4))
