from cryptography.fernet import Fernet

# מפתח קבוע להדגמה (במציאות מחליפים מפתחות בצורה מאובטחת, כאן אנחנו מדמים שזה כבר קרה)
# המפתח הזה חייב להיות זהה אצל כולם!
DEMO_KEY = b'H0bD_uH5y5gq7x9z3v1k2j4n5m6l7p8o9i0u1y2t3r4=' 

class SecureChannel:
    def __init__(self):
        # יצירת מופע של מנגנון ההצפנה עם המפתח שלנו
        self.cipher = Fernet(DEMO_KEY)

    def encrypt_data(self, data_string):
        """מקבל מחרוזת (למשל JSON) ומחזיר ג'יבריש מוצפן ב-bytes"""
        if isinstance(data_string, str):
            data_string = data_string.encode()
        return self.cipher.encrypt(data_string).decode() # מחזיר מחרוזת מוצפנת

    def decrypt_data(self, encrypted_string):
        """מקבל ג'יבריש ומחזיר את המחרוזת המקורית"""
        if isinstance(encrypted_string, str):
            encrypted_string = encrypted_string.encode()
        return self.cipher.decrypt(encrypted_string).decode()