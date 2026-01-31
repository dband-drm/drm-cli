import logging
from logging.handlers import TimedRotatingFileHandler,RotatingFileHandler
import os
from pathlib import Path
import getpass
import socket
import json
from datetime import datetime
from functools import wraps
import traceback
import re

#===========
# Constrants
#===========
current_working_directory = Path(__file__).parent.parent.resolve()
BYTES_PER_MB = 1024 * 1024
LOG_DIR = "log"
LOG_DIR_TRACE = "trace"
DRM_INSTALL_LOG_FILE_NAME = "drm_install.log"
DRM_INSTALL_LOG_FILE_NAME_TRACE = "drm_install_trace.log"
DRM_UNINSTALL_LOG_FILE_NAME = "drm_uninstall.log"
DRM_UNINSTALL_LOG_FILE_NAME_TRACE = "drm_uninstall_trace.log"
DRM_DEPLOY_LOG_FILE_NAME = "drm_deploy.log"
DRM_DEPLOY_LOG_FILE_NAME_TRACE = "drm_deploy_trace.log"
DRM_CRYPTO_LOG_FILE_NAME = "drm_crypto.log"
DRM_CRYPTO_LOG_FILE_NAME_TRACE = "drm_crypto_trace.log"


#Log Level: The level of the log (DEBUG, INFO, WARNING, ERROR, CRITICAL).

# Extend the log record 
class UserHostFormatter(logging.Formatter):
    """Custom formatter to convert log records to include user and host name
    """
    def format(self, record):
        # Get the current user - handle WSL2 edge cases
        try:
            user = getpass.getuser()
        except Exception:
            user = os.environ.get('USER', os.environ.get('USERNAME', 'unknown'))
        
        # Get the host name - use environment to avoid socket issues on WSL2
        host = os.environ.get('HOSTNAME', os.environ.get('COMPUTERNAME', 'unknown'))
        
        # Extend the log record with user and host
        record.user = user
        record.host = host
        # Return the formatted log message
        return super().format(record)

class JSONFormatter(logging.Formatter):
    """Custom formatter to convert log records into JSON
    """
    # Method that formats a logging record into JSON
    def format(self, record):
        # Convert the record's creation time to an ISO 8601 formatted string
        timestamp = datetime.fromtimestamp(record.created).isoformat()
        
        # Get user - handle WSL2 edge cases
        try:
            user = getpass.getuser()
        except Exception:
            user = os.environ.get('USER', os.environ.get('USERNAME', 'unknown'))
        
        # Get host from environment - avoid socket calls that can fail on WSL2
        host = os.environ.get('HOSTNAME', os.environ.get('COMPUTERNAME', 'unknown'))
        
        # Create a dictionary containing log details
        log_record = {
            "timestamp": timestamp,
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "pathname": record.pathname,
            "lineno": record.lineno,
            "funcName": record.funcName,
            "threadName": record.threadName,
            "process": record.process,
            "user": user,
            "host": host
        }
    # Convert the dictionary into a JSON-formatted string
        return json.dumps(log_record)

class CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    #format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
    format = "%(asctime)s - %(levelname)s - %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
       
def get_verify_directory(dirname):
    """ Verify directory exists 
    :param dirname: directory name
    :return: directory path
    """       
    #===========================
    # Build path by adding folder name to current path  --> folder path 
    #===========================
    current_dir = os.path.join(current_working_directory, dirname)
    # Create log folder if missing
    if not os.path.exists(current_dir):
            os.mkdir(current_dir)
    return current_dir

def configure_logging(logname):
    """ Configure_logging
    :param logname: log name
    :param loglevel: log level [logging.INFO]
    :param logfoldername: log folder name
    :param logmaxsize: log max size
    :param backupcount: backup count
    :return: logger
    """       
    #===========================
    # Define logger [console,filerotate,trace]
    #===========================
    #Globals
    mode            =     os.environ.get('DRM_LOGGER_MODE')
    logfoldername   =     os.environ.get("LOG_FOLDER_NAME")
    logmaxsize      =     os.environ.get("LOG_MAX_SIZE_MB")
    backupcount     =     os.environ.get("LOG_BACKUP_COUNT")
    level           =     os.environ.get('DRM_LOGGER_LEVEL')
    # Create a logger
    logger = logging.getLogger(logname)
    # Set global logging level
    logger.setLevel(logging.DEBUG)  

    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(CustomFormatter())
    console_handler.setLevel(logging.INFO)  # Only display info and above on console logging.INFO
    
    #Get log directory
    log_dir = get_verify_directory(logfoldername)
    # Specify the rotation size in MB 
    backup_count = int(backupcount)
    # Convert the size to bytes
    max_bytes = int(logmaxsize) * BYTES_PER_MB
    # Create a rotate file handler
    if mode == "0":
        log_r_filename = os.path.join(log_dir ,DRM_INSTALL_LOG_FILE_NAME)
        drm_trace_name = DRM_INSTALL_LOG_FILE_NAME_TRACE
    if mode =="1":
        log_r_filename = os.path.join(log_dir ,DRM_DEPLOY_LOG_FILE_NAME)
        drm_trace_name = DRM_DEPLOY_LOG_FILE_NAME_TRACE
    if mode =="2":
        log_r_filename = os.path.join(log_dir ,DRM_CRYPTO_LOG_FILE_NAME)
        drm_trace_name = DRM_CRYPTO_LOG_FILE_NAME_TRACE
    if mode =="3":
        log_r_filename = os.path.join(log_dir ,DRM_UNINSTALL_LOG_FILE_NAME)
        drm_trace_name = DRM_UNINSTALL_LOG_FILE_NAME_TRACE
    
    file_r_handler = RotatingFileHandler(log_r_filename, mode='a', maxBytes=max_bytes, backupCount=backup_count, encoding=None, delay=False)
    # Define the format for the log messages
    file_log_format = "%(asctime)s - %(levelname)s - %(message)s"
    file_formatter = logging.Formatter(file_log_format)
    file_r_handler.setFormatter(file_formatter)
    file_r_handler.setLevel(logging.INFO)  # Write all levels to the file 
    
    # Create a TimedRotatingFileHandler for Trace
    file_t_handler = None
    if int(level)==logging.DEBUG:
        #Get log directory
        log_dir_trace = get_verify_directory(os.path.join(log_dir,LOG_DIR_TRACE))
        log_filename_trace_format =  datetime.now().strftime("%Y_%m_%d-%H_%M_%S_") + drm_trace_name 
        log_filename_trace_file = os.path.join(log_dir_trace,log_filename_trace_format )

        # Create a file handler
        file_t_handler = logging.FileHandler(log_filename_trace_file)
        file_t_handler.setFormatter(CustomFormatter())
        file_t_handler.setLevel(logging.DEBUG)  # Write all levels to the file
    
        try:
            json_formatter = JSONFormatter()
            file_t_handler.setFormatter(json_formatter)
        except Exception as fmt_err:
            # If JSON formatter fails (e.g., on WSL2), keep CustomFormatter
            pass

    # Add the handler to the logger if not already added
    if not logger.hasHandlers():
        logger.addHandler(console_handler)
        logger.addHandler(file_r_handler)
        if not file_t_handler is None:
             logger.addHandler(file_t_handler)

    return logger

# Masking function
def mask(data):
    """Mask sensitive data.
    :param data: data
    :return: masked data
    """
    if isinstance(data, str):
        # Create a list of values
        values_list = [ "insert into", "update", "delete","connections","server=","create","drop","pragma"]
        # Define the string to check
        input_string = data.lower()
        # Convert the input string to a list of words
        input_list = input_string.split()
        # Check if any value in values_list exists in input_list
        exists = any(value in input_list for value in values_list)
        # Check if it's a  command and mask sensitive information
        if exists :
            return mask_command(data.lower())
        return "****"
    elif isinstance(data, list):
        return ["****" if isinstance(item, str) else item for item in data]
    return data

def mask_command(command):
    """Mask sensitive information in a SQL command.
    :param data: command
    :return: masked command
    """
    # Regex patterns to identify and mask sensitive information
    patterns = [
        (r"(?i)(password\s*=\s*)('[^']*'|[^;,\s]*)", r"\1'****'"),
        (r"(?i)(user\s*id\s*=\s*)('[^']*'|[^;,\s]*)", r"\1'****'"),
        (r"(?i)(server\s*=\s*)('[^']*'|[^;,\s]*)", r"\1'****'"),
        (r"(?i)(connection_string\s*=\s*)('[^']*'|[^;,=\s]*)", r"\1'****'"), 
        (r"(?i)(connection_string\s*:\s*)('[^']*'|[^;,\s]*)", r"\1'****'"),
        # Add more patterns as needed
        
    ]
    for pattern, replacement in patterns:
        command = re.sub(pattern, replacement, command)
    return command

# Define a decorator for logging and exception handling
def log_decorator(logger):
    """ Configure log_decorator
    :param logger: logger
    :return: NULL
    """ 
    #SENSITIVE_PARAMS
    SENSITIVE_PARAMS = ['plaintext','data','password', 'command', 'columns_values', 'host', 'server','connection_string','query','encryption_key','connections']
    def decorator(func):
        """ Configure decorator
        :param func: func
        :return: decorator
        """  
        @wraps(func)  
        def wrapper(*args, **kwargs):
            """ Configure wrapper # Preserve function metadata
            :param args: *args
            :param kwargs: **kwargs
            :return: wrapper
            """ 
            # Log function start with additional information
            func_args = func.__code__.co_varnames[:func.__code__.co_argcount]
            args_dict = dict(zip(func_args, args))
            all_params = {**args_dict, **kwargs}
            
            # Convert parameter names to lowercase
            all_params_lower = {k.lower(): v for k, v in all_params.items()}
            
            # Mask sensitive parameters
            masked_params = {
                k: mask(v) if k in SENSITIVE_PARAMS else v
                for k, v in all_params_lower.items()
            }
            logger.debug(f"{func.__qualname__} start with params={masked_params}")
            #logger.debug(f"{func.__name__} start with args={args}, kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)  # Execute the wrapped function
                return result  # Return the function's result
            except Exception as e:
                # Get exception type and message
                logger.debug(f"Exception in {func.__qualname__}: {e}")
                logger.debug(f"Exception type: {type(e).__name__}")
                logger.debug(f"Exception message: {str(e)}")
                logger.debug(f"Stack trace: {traceback.format_exc()}")
                 
                raise  # Reraise the exception to maintain the original function behavior
            finally:
                # Log function end, regardless of whether an exception occurred
                logger.debug(f"{func.__qualname__} end")
        return wrapper
    return decorator

    # Example usage
    if __name__ == "__main__":
        logger = configure_install_logging("example_logger")
        
        @log_decorator(logger)
        def example_function(param1, param2):
            if param1 == 'password':
                raise ValueError('An error occurred')
            return "Success"
        
        example_function('sensitive data', 'another data')
