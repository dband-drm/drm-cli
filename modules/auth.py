import re
import os
from pathlib import Path
import logging
from modules import drm_logger

current_working_directory = Path(__file__).parent.resolve()

#================
# Printing colors
#================
class style():
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

class Auth:

    logger = drm_logger.configure_logging("Auth.Authenticate")

    @drm_logger.log_decorator(logger) 
    def __init__(self):
        self = self

    @drm_logger.log_decorator(logger) 
    def validate_password_policy(self, password: str) -> bool:
        """ 
        Set  password
        :param password: Password
        :return:  Password Valid(Bool)
        """       
        # Verify key policy
        if(password != None and password != "" ):
            if (len(password) <= 8):
                flag = False
            elif not re.search("[a-z]", password):
                flag = False
            elif not re.search("[A-Z]", password):
                flag = False
            elif not re.search("[0-9]", password):
                flag = False
            #elif not re.search("[~`!@#$%^&*()-_=+,<.>/?;:]" , password):
            elif not re.search(r"[~`!@#$%^&*()\-=+\[\]{};:'\",.<>?/]", password):
                flag = False
            else:
                flag = True
        else:
            flag = True

        if (flag==False):
            self.logger.debug("{password} ,The encryption key does not meet with validation policy!".format(password = password))
            self.logger.warning("The encryption key does not meet with validation policy!")
        else:
            self.logger.info("The encryption meet with validation policy!")
        return flag

    @drm_logger.log_decorator(logger) 
    def validate_password(self, password: str,security_text_config:str) -> bool:
        """ 
        Set  password
        :param password: Password
        :param security_string: security_string
        :return:  Password Valid Verification(Bool)
        

        """   
        security_text = "This drm cli was developed by d-band and it is amazing!!!"
        from modules import crypto
        if(password!=None):
            crpt = crypto.Crypto(password)
            encrypted_text = crpt.encrypt_string(security_text)
            if (encrypted_text != security_text_config):
                return False
            else:
                return True
        else:
            return (security_text == security_text_config)
          
    @drm_logger.log_decorator(logger) 
    def set_password(self) -> str:
        """ 
        Set  password
        :param password: Password
        :return:  Password (String)
        """    
        password = None
        encryption_key = input("Enter encryption key (Default, empty is not encrypted): ")        
        if (encryption_key == None or encryption_key == ""):
            user_choice = input(style.YELLOW + "Are you sure you want to keep sensitive Data as clear text? Enter [Y]/N to keep unsecured Data: " + style.RESET)
            if (user_choice.lower() == "n"):
                self.set_password(self)
            else:
                password = None
        else:
            validate_policy =False
            validate_policy  = self.validate_password_policy(password=encryption_key)
            #5 valid option to chouse password
            valid_counter = 4
            while validate_policy == False and valid_counter > 0:
                
                #=====================
                # Enter encryption key
                #=====================
                self.logger.info("1. Minimum 8 characters.")
                self.logger.info("2. The alphabet must be between [a-z]")
                self.logger.info("3. At least one alphabet should be of Upper Case [A-Z]")
                self.logger.info("4. At least 1 number or digit between [0-9].")
                self.logger.info("5. At least 1 special character suc as !@#...")
                encryption_key = input("Enter encryption key: ")
                validate_policy  = self.validate_password_policy(self,encryption_key)
                valid_counter -= 1

            if(validate_policy ==True):
                password = encryption_key
                if(password==""):
                    password =None
            else:
                #self.logger.warning('The encryption key does not meet with validation policy!')
                self.logger.debug('{key}: The encryption key does not meet with validation policy!'.format(key=encryption_key))
                raise ValueError('The encryption key does not meet with validation policy!,after all tries')

        return password
 