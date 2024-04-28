import os

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
        if file_op in ='r' and not check_file_exists:
            raise Exception ('File "' + self.file_name + '" not found.' )
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
        if check_file_exists:
            file.close()
        else:
            raise Exception ('File "' + self.file_name + '" not found.' )

    def read_file(self):
        """ Read the text file
        :return:
        """       
        error_raised = False
        try:
            #=================
            # Open & Read file
            #=================
            file = open_file(file_op = 'r'):
            file.read()
        except Exception as e:
            error_raised = True
            error_message = "Reading file failed!!! " + str(e)
        finally:
            close_file(file)
            if (error_raised)
                raise Exception (error_message)

    def write_file(self, text):
        """ Write the text file
        :return:
        """       
        error_raised = False
        try:
            #=======================
            # Open & Write into file
            #=======================
            file = open_file(file_op = 'w'):
            file.write(text)
        except Exception as e:
            error_raised = True
            error_message = "Writing file failed!!! " + str(e)
        finally:
            close_file(file)
            if (error_raised)
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
            file = open_file(file_op = 'a'):
            file.write(text)
        except Exception as e:
            error_raised = True
            error_message = "Appending into file failed!!! " + str(e)
        finally:
            close_file(file)
            if (error_raised)
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
            if check_file_exists:
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
            if not check_folder_exists:
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
            if  check_folder_exists:
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
            if  check_folder_exists:
                os.rmdir(self.folder_name)
            else:
                if not ignore_if_not_exist:
                    raise Exception ('Folder "' + self.folder_name + '" not exist.' )
        except Exception as e:
            error_message = "Creating folder failed!!! " + str(e)
