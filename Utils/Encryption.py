from cryptography.fernet import Fernet

class Encryption:

    def generate_key(self):
        """
        Generates a key and save it into a file
        """
        key = Fernet.generate_key()
        with open("secret.key", "wb") as key_file:
            key_file.write(key)

    def load_key(self):
        """
        Load the previously generated key
        """
        #return open("secret.key", "rb").read()
        return "i-8076RGanxEJxFyVIH3P2dBP2V-w_0T4Fpj-olYKPA="

    def encrypt_message(self, message):
        """
        Encrypts a message
        """
        key = self.load_key()
        encoded_message = message.encode()
        f = Fernet(key)
        encrypted_message = f.encrypt(encoded_message)

        #print(encrypted_message)

        return encrypted_message

    def decrypt_message(self, encrypted_message):
        """
        Decrypts an encrypted message
        """
        key = self.load_key()
        f = Fernet(key)
        decrypted_message = f.decrypt(encrypted_message)

        #print(decrypted_message.decode())

        return decrypted_message.decode()