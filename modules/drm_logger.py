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

current_working_directory = Path(__file__).parent.parent.resolve()

BYTES_PER_MB = 1024 * 1024

LOG_DIR = "log"
LOG_DIR_TRACE = "trace"

INSTALL_LOG_FILE_NAME = "install.log"
DRM_DEPLOY_LOG_FILE_NAME = "drm_deploy.log"
DRM_DEPLOY_LOG_FILE_NAME_TRACE = "drm_deploy_trace.log"

#Log Level: The level of the log (DEBUG, INFO, WARNING, ERROR, CRITICAL).

# Extend the log record 
class UserHostFormatter(logging.Formatter):
    """Custom formatter to convert log records to include user and host name
    """
    def format(self, record):
        # Get the current user
        user = getpass.getuser()
        # Get the host name
        host = socket.gethostname()
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
            "user": getpass.getuser(),
            "host": socket.gethostname()
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

def configure_install_logging(logname,loglevel=logging.INFO):
    """ Configure_install logging
    :param logname: log name
    :param loglevel: log level [logging.INFO]
    :return: logger
    """
    #===========================
    # Define logger [console,file]
    #===========================
    # Create a logger
    logger = logging.getLogger(logname)
    logger.setLevel(loglevel)  # Set global logging level
    
    # Define the format for the log messages
    #log_format = "%(asctime)s - %(levelname)s - %(message)s"
    #formatter = logging.Formatter(log_format)

    #logger.setFormatter(CustomFormatter())

    # Create a console handler
    console_handler = logging.StreamHandler()
    #console_handler.setFormatter(formatter)
    console_handler.setFormatter(CustomFormatter())
    console_handler.setLevel(logging.INFO)  # Only display info and above on console logging.INFO
    #Get log directory
    log_dir = get_verify_directory(LOG_DIR)
    # Create a file handler
    log_filename = os.path.join(log_dir, INSTALL_LOG_FILE_NAME)
    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(CustomFormatter())
    file_handler.setLevel(loglevel)  # Write all levels to the file
    
    # Add the handler to the logger if not already added
    if not logger.hasHandlers():
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger

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
    # Define the format for the log messages
        #"%(asctime)s  - %(name)s - %(user)s@%(host)s - %(levelname)s - %(message)s"
        #formatter = UserHostFormatter(fmt=log_format)
    #log_format = "%(asctime)s - %(levelname)s - %(message)s"
    #formatter = logging.Formatter(log_format)
    #moved to cust format

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
        log_r_filename = os.path.join(log_dir ,INSTALL_LOG_FILE_NAME)
    else:
        log_r_filename = os.path.join(log_dir ,DRM_DEPLOY_LOG_FILE_NAME)
    
    file_r_handler = RotatingFileHandler(log_r_filename, mode='a', maxBytes=max_bytes, backupCount=backup_count, encoding=None, delay=False, errors=None)
    # Define the format for the log messages
    file_log_format = "%(asctime)s - %(levelname)s - %(message)s"
    file_formatter = logging.Formatter(file_log_format)
    file_r_handler.setFormatter(file_formatter)
    file_r_handler.setLevel(logging.INFO)  # Write all levels to the file 
    
    #logger = drm_logger.configure_install_logging(__name__,int(level))
    # Create a TimedRotatingFileHandler for Trace
    file_t_handler = None
    if int(level)==logging.DEBUG:
        #Get log directory
        log_dir_trace = get_verify_directory(os.path.join(log_dir,LOG_DIR_TRACE))

        log_filename_trace_format =  datetime.now().strftime("%Y_%m_%d-%H_%M_%S") + DRM_DEPLOY_LOG_FILE_NAME_TRACE 
        log_filename_trace_file = os.path.join(log_dir_trace,log_filename_trace_format )

        # Create a file handler
        file_t_handler = logging.FileHandler(log_filename_trace_file)
        file_t_handler.setFormatter(CustomFormatter())
        file_t_handler.setLevel(logging.DEBUG)  # Write all levels to the file
    
        json_formatter = JSONFormatter()
        file_t_handler.setFormatter(json_formatter)


        """"
        timed_rotating_file_handler = TimedRotatingFileHandler(
        log_filename_trace,
        when='d',  # 'w0' means every Monday
        interval=1,  # Every day
        backupCount=3,  # Keep last 3 backups
        atTime=None  # Default is midnight
        )
       
        timed_rotating_file_handler.setLevel(loglevel)  # Write all levels to the file
        """

    # Add the handler to the logger if not already added
    if not logger.hasHandlers():
        logger.addHandler(console_handler)
        logger.addHandler(file_r_handler)
        if not file_t_handler is None:
             logger.addHandler(file_t_handler)

    return logger

# Define a decorator for logging and exception handling
def log_decorator(logger):
    """ Configure log_decorator
    :param logger: logger
    :return: NULL
    """  
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
            
            logger.debug(f"{func.__name__} start with args={args}, kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)  # Execute the wrapped function
                return result  # Return the function's result
            except Exception as e:
                # Get exception type and message
                exception_type = type(e).__name__
                exception_message = str(e)
                
                # Get stack trace
                stack_trace = traceback.format_exc()  # Full stack trace as a string
                
                
                # Output the exception information for debugging
                logger.debug(f"Exception in {func.__name__}: {e}")
                logger.debug(f"Exception type: {exception_type}")
                logger.debug(f"Exception message: {exception_message}")
                logger.debug(f"Stack trace:   {stack_trace}")
                 
                raise  # Reraise the exception to maintain the original function behavior
            finally:
                # Log function end, regardless of whether an exception occurred
                logger.debug(f"{func.__name__} end")
        return wrapper
    return decorator