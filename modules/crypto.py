import logging
from modules import drm_logger
from base64 import b64encode, b64decode

class Crypto:

    logger = drm_logger.configure_logging("crypto.Crypto")

    @drm_logger.log_decorator(logger) 
    def __init__(self, password = ""):
        self.password = password

    @drm_logger.log_decorator(logger) 
    def xor_encrypt_decrypt(data: str, password: str) -> str:
        """ 
        Encrypt Data using password
        :param data: Data
        :param password: Password
        :return: Encrypted Data (String)
        """       
        # Convert the data and password into byte arrays
        data_bytes = data.encode()
        password_bytes = password.encode()
        
        # Perform XOR operation with the data and password (repeated if necessary)
        encrypted_decrypted_bytes = bytearray()
        for i in range(len(data_bytes)):
            encrypted_decrypted_bytes.append(data_bytes[i] ^ password_bytes[i % len(password_bytes)])
        
        # Convert the resulting bytes back to a string
        encrypted_decrypted_str = encrypted_decrypted_bytes.decode()
        
        return encrypted_decrypted_str

    @drm_logger.log_decorator(logger) 
    def encrypt_string(self, plaintext: str) -> str:
        """ 
        Encrypt text
        :param plaintext: Plain text
        :return: Encryoted Base64 text (String)
        """       
        # Perform XOR encryption and then encode the result in base64
        encrypted = Crypto.xor_encrypt_decrypt(plaintext, self.password)
        encrypted_base64 = b64encode(encrypted.encode()).decode()
        
        return encrypted_base64

    @drm_logger.log_decorator(logger) 
    def decrypt_string(self, encrypted_data: str) -> str:
        """ 
        Decrypt encrypted text
        :param encrypted_data: Encrypted text
        :return: Plain text (String)
        """       
        # Decode the base64 encoded data and then perform XOR decryption
        encrypted = b64decode(encrypted_data).decode()
        decrypted = Crypto.xor_encrypt_decrypt(encrypted, self.password)
        
        return decrypted
