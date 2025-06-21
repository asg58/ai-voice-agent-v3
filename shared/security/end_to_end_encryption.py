from cryptography.fernet import Fernet

class EndToEndEncryption:
    def __init__(self):
        self.key = Fernet.generate_key()
        self.cipher = Fernet(self.key)

    def encrypt(self, data):
        """
        Versleutel data.
        """
        return self.cipher.encrypt(data.encode())

    def decrypt(self, encrypted_data):
        """
        Ontsleutel data.
        """
        return self.cipher.decrypt(encrypted_data).decode()
