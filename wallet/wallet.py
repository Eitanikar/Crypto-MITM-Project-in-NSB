import json
import os
import time
import ecdsa
import binascii
from common.protocol import Transaction

class Wallet:
    def __init__(self, owner: str, initial_balance: int = 0, db_path=None):
        self.owner = owner
        self.balance = initial_balance
        self.history = []
        self.db_path = db_path
        
        # משתנים למפתחות - יאתחלו ב-load או ייצרו חדשים
        self.private_key = None
        self.public_key = None
        self.address = None

        if self.db_path and os.path.exists(self.db_path):
            self._load_or_init()
        else:
            # אם אין קובץ, ניצור מפתחות חדשים
            self._generate_keys()
            if self.db_path:
                self.save()

    def _generate_keys(self):
        """מייצר מפתחות חדשים אם אין בקובץ"""
        self.private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        self.public_key = self.private_key.get_verifying_key()
        self.address = binascii.hexlify(self.public_key.to_string()).decode()

    def sign_transaction(self, transaction_data_string):
        """חתימה על המחרוזת של הטרנזקציה באמצעות המפתח הפרטי"""
        if not self.private_key:
            raise ValueError("No private key loaded!")
        
        # החתימה עצמה
        signature = self.private_key.sign(transaction_data_string.encode())
        return binascii.hexlify(signature).decode()

    # ---------- Persistence ----------

    def _load_or_init(self):
        if os.path.exists(self.db_path):
            self.load()
        else:
            self.save()

    def save(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # המרה של המפתח הפרטי למחרוזת כדי לשמור ב-JSON
        priv_key_str = binascii.hexlify(self.private_key.to_string()).decode() if self.private_key else None

        data = {
            "owner": self.owner,
            "balance": self.balance,
            "history": self.history,
            "private_key": priv_key_str  # שומרים את המפתח הפרטי!
        }
        with open(self.db_path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self):
        with open(self.db_path, "r") as f:
            data = json.load(f)

        self.balance = data.get("balance", 0)
        self.history = data.get("history", [])
        
        # טעינה ושחזור המפתח הפרטי מהקובץ
        priv_key_str = data.get("private_key")
        if priv_key_str:
            self.private_key = ecdsa.SigningKey.from_string(binascii.unhexlify(priv_key_str), curve=ecdsa.SECP256k1)
            self.public_key = self.private_key.get_verifying_key()
            self.address = binascii.hexlify(self.public_key.to_string()).decode()
        else:
            # Fallback למקרה שיש קובץ ישן בלי מפתחות
            self._generate_keys()

    # ---------- Wallet actions ----------

    def credit(self, amount: int, reason: str = "credit"):
        if amount <= 0:
            raise ValueError("Amount must be positive")

        self.balance += amount
        self.history.append({
            "type": reason,
            "amount": amount,
            "timestamp": int(time.time())
        })

        if self.db_path:
            self.save()

    def create_transaction(self, receiver: str, amount: int) -> Transaction:
        # כאן אנחנו רק יוצרים את האובייקט, החתימה תתבצע בנפרד או כחלק מהפרוטוקול
        if amount <= 0:
            raise ValueError("Amount must be positive")

        if amount > self.balance:
            raise ValueError("Insufficient balance")

        tx = Transaction(
            sender=self.address, # שים לב: השולח הוא הכתובת (Public Key) ולא השם סתם
            receiver=receiver,
            amount=amount
        )
        
        # עדכון לוקאלי - יתבצע רק אם השרת יאשר (אבל כרגע נשאיר לוקאלי לדמו)
        self.balance -= amount
        self.history.append({
            "type": "tx_sent",
            "to": receiver,
            "amount": amount,
            "timestamp": int(time.time())
        })

        if self.db_path:
            self.save()

        return tx

    def __str__(self):
        return f"Wallet(owner={self.owner}, balance={self.balance}, addr={self.address[:6]}...)"