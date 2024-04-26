import logging
from logging.handlers import TimedRotatingFileHandler
import os
import getpass
import socket
import json
from datetime import datetime

# Custom Formatter to include user and host name
class UserHostFormatter(logging.Formatter):
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
    def format(self, record):
        timestamp = datetime.fromtimestamp(record.created).isoformat()
        # Create a dictionary with log details
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
    # Return the JSON string
        return json.dumps(log_record)
# Configure the logging system
def configure_logging(logname,loglevel):
    # Create a logger
    logger = logging.getLogger(logname)
    logger.setLevel(loglevel)  # Set global logging level
    #logger.setLevel(logging.DEBUG)  # Set global logging level

    # Define the format for the log messages
     
    log_format = "%(asctime)s  - %(name)s - %(user)s@%(host)s - %(levelname)s - %(message)s"
    formatter = UserHostFormatter(fmt=log_format)

    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)  # Only display info and above on console logging.INFO
    logger.addHandler(console_handler)
    # Create a file handler
    if not os.path.exists("./logs"):
        os.mkdir("./logs")
    log_filename = "./logs/app.log"
    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(loglevel)  # Write all levels to the file
    logger.addHandler(file_handler)
    
# Create a TimedRotatingFileHandler that rotates every Monday at midnight
    #TimedRotatingFileHandler
    # Define the log filename
    log_filename ="./logs/app_daily.json"

    timed_rotating_file_handler = TimedRotatingFileHandler(
    log_filename,
    when='d',  # 'w0' means every Monday
    interval=1,  # Every week
    backupCount=3,  # Keep last 3 backups
    atTime=None  # Default is midnight
)
    json_formatter = JSONFormatter()
    timed_rotating_file_handler.setFormatter(json_formatter)
    #timed_rotating_file_handler.setFormatter(formatter)
    timed_rotating_file_handler.setLevel(logging.DEBUG)  # Write all levels to the file
    # Add handlers to the logger    
    logger.addHandler(timed_rotating_file_handler)

    return logger
