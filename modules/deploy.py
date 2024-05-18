import sqlite3
import logging
from sqlite3 import Error
from modules import drm_logger, files_and_folders

class MsSql:

    logger = drm_logger.configure_logging("deploy.MsSql")

    @drm_logger.log_decorator(logger) 
    def __init__(self, deploy_config): 

        # Get SqlPackage from configuration
        if hasattr(deploy_config, 'sqlpackage_dir'):
            self.file_name = deploy_config.sqlpackage_dir
        else:
            f = files_and_folders.Files("sqlpackage")
            self.file_name = f.find_file_in_dir("/")


class Deploy:

    logger = drm_logger.configure_logging("deploy.Deploy")

    @drm_logger.log_decorator(logger) 
    def __init__(self, deploy_config): 
        self.deploy_config = deploy_config
