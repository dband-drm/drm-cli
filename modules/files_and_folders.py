import os
import json
import logging
import shutil
from modules import drm_logger

class Files:

    logger = drm_logger.configure_logging("files_and_folders.Files")

    @drm_logger.log_decorator(logger) 
    def __init__(self, file_name): 
        self.file_name = file_name     
  
    @drm_logger.log_decorator(logger) 
    def find_file_in_dir(self, dir):
        """ 
        Finds a file in given directory & return first instance
        :param dir: directory to search in
        :return: First file absolute name (String)
        """       
        for root, dirs, files in os.walk(dir):
            if self.file_name in files:
                return os.path.join(root, self.file_name)

    @drm_logger.log_decorator(logger) 
    def check_file_exists(self):
        """ 
        Checks if file exist
        :return: File exists or not (Boolean)
        """       
        if os.path.exists(self.file_name):
            return True
        else:
            return False

    @drm_logger.log_decorator(logger) 
    def open_file(self, file_op):
        """ 
        Open the text file
        :param file_op: File operation ("w", "r", "a")
        :return: file object (File)
        """       
        #===========================
        # if file exists --> open it
        #===========================
        if file_op == 'r' and not Files.check_file_exists(self):
            raise Exception ('File "' + str(self.file_name) + '" not found.' )
        else:
            file = open(self.file_name, file_op)
            return file

    @drm_logger.log_decorator(logger) 
    def close_file(self, file):
        """ 
        Close the text file
        :param file: file object
        :return:
        """       
        #============================
        # if file exists --> close it
        #============================
        if Files.check_file_exists(self):
            file.close()
        else:
            raise Exception ('File "' + self.file_name + '" not found.' )

    @drm_logger.log_decorator(logger) 
    def load_file(self):
        """ 
        Load a JSON file
        :return: JSON text (JSON)
        """       
        error_raised = False
        try:
            #=================
            # Open & Load file
            #=================
            file = Files.open_file(self, file_op = 'r')
            js_text = json.load(file)
        except Exception as e:
            error_raised = True
            error_message = "Reading file failed!!! " + str(e)
        finally:
            Files.close_file(self, file)
            if (error_raised):
                raise Exception (error_message)
            return js_text

    @drm_logger.log_decorator(logger) 
    def read_file(self):
        """ 
        Read the text file
        :return: File text (String)
        """       
        error_raised = False
        try:
            #=================
            # Open & Read file
            #=================
            file = Files.open_file(self, file_op = 'r')
            text = file.read()
        except Exception as e:
            error_raised = True
            error_message = "Reading file failed!!! " + str(e)
        finally:
            Files.close_file(self, file)
            if (error_raised):
                raise Exception (error_message)
            return text

    @drm_logger.log_decorator(logger) 
    def write_file(self, text):
        """ 
        Write the text file
        :return:
        """       
        error_raised = False
        try:
            #=======================
            # Open & Write into file
            #=======================
            file = Files.open_file(self, file_op = 'w')
            file.write(text)
        except Exception as e:
            error_raised = True
            error_message = "Writing file failed!!! " + str(e)
        finally:
            Files.close_file(self, file)
            if (error_raised):
                raise Exception (error_message)

    @drm_logger.log_decorator(logger) 
    def append_file(self, text):
        """ 
        Append a text to an existing file
        :return:
        """       
        error_raised = False
        try:
            #========================
            # Open & Append into file
            #========================
            file = Files.open_file(self, file_op = 'a')
            file.write(text)
        except Exception as e:
            error_raised = True
            error_message = "Appending into file failed!!! " + str(e)
        finally:
            Files.close_file(self, file)
            if (error_raised):
                raise Exception (error_message)

    @drm_logger.log_decorator(logger) 
    def delete_file(self, ignore_file_not_found = False):
        """ 
        Delete a file
        :param ignore_file_not_found: ignores if a file not found
        :return:
        """       
        try:
            #============
            # Delete file
            #============
            if Files.check_file_exists(self):
                os.remove(self.file_name)
            else:
                if not ignore_file_not_found:
                    raise Exception ('File "' + self.file_name + '" not found.' )
        except Exception as e:
            error_message = "File deletion failed!!! " + str(e)

    @drm_logger.log_decorator(logger) 
    def find_text_in_file(self, text_to_find):
        """ 
        Find text in a file
        :param ignore_file_not_found: ignores if a file not found
        :return:
        """       
        error_raised = False
        try:
            #=================
            # Open & Read file
            #=================
            file = Files.open_file(self, file_op = 'r')           
            # read all lines in a list
            lines = file.readlines()
            for line in lines:
                # check if string present on a current line
                if (line.lower()).find(text_to_find.lower()) != -1:
                    return (line, lines.index(line) + 1)
            return (None, None)
        except Exception as e:
            error_raised = True
            error_message = "Find text in file failed!!! " + str(e)
        finally:
            Files.close_file(self, file)
            if (error_raised):
                raise Exception (error_message)

    @drm_logger.log_decorator(logger) 
    def get_line_in_file(self, line_number):
        """ 
        Get line text in a file by line number
        :param line_number: line number
        :return:
        """       
        error_raised = False
        try:          
            #=================
            # Open & Read file
            #=================
            file = Files.open_file(self, file_op = 'r')           
            # read all lines in a list
            for current_line_number, line in enumerate(file, start=1):
                # check if string present on a current line
                if current_line_number == line_number:
                    return (line.strip())

        except Exception as e:
            error_raised = True
            error_message = "Find text in file failed!!! " + str(e)
        finally:
            Files.close_file(self, file)
            if (error_raised):
                raise Exception (error_message)


class Folders:

    logger = drm_logger.configure_logging("files_and_folders.Folders")

    @drm_logger.log_decorator(logger) 
    def __init__(self, folder_name): 
        self.folder_name = folder_name     
  
    @drm_logger.log_decorator(logger) 
    def is_folder_empty(folder_path):
        """ 
        Checks if folder is empty
        :return: Folder is empty or not (Boolean)
        """     
        return not os.listdir(folder_path)

    @drm_logger.log_decorator(logger) 
    def check_folder_exists(self):
        """ 
        Checks if folder exists
        :return: Folder exists or not (Boolean)
        """       
        if os.path.exists(self.folder_name):
            return True
        else:
            return False

    @drm_logger.log_decorator(logger) 
    def create_folder(self, ignore_if_already_exist = True):
        """ 
        Create a folder
        :param ignore_if_already_exists: ignores if a folder already exist
        :return:
        """       
        try:
            #==============
            # Create folder
            #==============
            if not Folders.check_folder_exists(self):
                os.mkdir(self.folder_name)
            else:
                if not ignore_if_already_exist:
                    raise Exception ('Folder "' + self.folder_name + '" already exists.' )
        except Exception as e:
            error_message = "Creating folder failed!!! " + str(e)

    @drm_logger.log_decorator(logger) 
    def delete_folder(self, ignore_if_not_exist = True):
        """ 
        Delete a folder
        :param ignore_if_not_exist: ignores if a folder not exist
        :return:
        """       
        try:
            #==============
            # Delete folder
            #==============
            if  Folders.check_folder_exists(self):
                os.rmdir(self.folder_name)
            else:
                if not ignore_if_not_exist:
                    raise Exception ('Folder "' + self.folder_name + '" not exist.' )
        except Exception as e:
            error_message = "Folder deletion failed!!! " + str(e)

    @drm_logger.log_decorator(logger) 
    def delete_folder_content(self, ignore_if_not_exist = True):
        """ 
        Delete folder content recursive
        :param ignore_if_not_exist: ignores if a folder not exist
        :return:
        """       
        try:
            #==============
            # Delete folder
            #==============
            if  Folders.check_folder_exists(self):
                # Iterate over all the items in the folder
                for item in os.listdir(self.folder_name):
                    item_path = os.path.join(self.folder_name, item)

                    # Check if the item is a file
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.unlink(item_path)  # Delete the file or link
 
                    # Check if the item is a directory
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)  # Delete the directory and all its contents

            else:
                if not ignore_if_not_exist:
                    raise Exception ('Folder "' + self.folder_name + '" not exist.' )
        except Exception as e:
            error_message = "Folder deletion failed!!! " + str(e)


