import os
import json

class Files:
    def __init__(self, file_name): 
        self.file_name = file_name     
  
    def check_file_exists(self):
        """ Checks if file exist
        :return: boolean
        """       
        if os.path.exists(self.file_name):
            return True
        else:
            return False

    def open_file(self, file_op):
        """ Open the text file
        :param file_op: File operation ("w", "r", "a")
        :return: file object
        """       
        #===========================
        # if file exists --> open it
        #===========================
        if file_op == 'r' and not Files.check_file_exists(self):
            raise Exception ('File "' + str(self.file_name) + '" not found.' )
        else:
            file = open(self.file_name, file_op)
            return file

    def close_file(self, file):
        """ Close the text file
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

    def load_file(self):
        """ Load the JSON file
        :return: JSON text
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

    def read_file(self):
        """ Read the text file
        :return: text
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

    def write_file(self, text):
        """ Write the text file
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

    def append_file(self, text):
        """ Append the text to an existing file
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

    def delete_file(self, ignore_file_not_found = False):
        """ Delete a file
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
            error_message = "Deleting file failed!!! " + str(e)


class Folders:
    def __init__(self, folder_name): 
        self.folder_name = folder_name     
  
    def check_folder_exists(self):
        """ Checks if folder exists
        :return: boolean
        """       
        if os.path.exists(self.folder_name):
            return True
        else:
            return False

    def create_folder(self, ignore_if_already_exist = True):
        """ Create a folder
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

    def delete_folder(self, ignore_if_not_exist = True):
        """ Delete a folder
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
            error_message = "Creating folder failed!!! " + str(e)

    def delete_folder(self, ignore_if_not_exist = True):
        """ Delete a folder
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
            error_message = "Creating folder failed!!! " + str(e)
