import json
import os
import time
from common.protocol import Transaction


class Wallet:
    def __init__(self, owner: str, initial_balance: int = 0, db_path=None):
        self.owner = owner
        self.balance = initial_balance
        self.history = []
        self.db_path = db_path

        if self.db_path:
            self._load_or_init()

    # ---------- Persistence ----------

    def _load_or_init(self):
        if os.path.exists(self.db_path):
            self.load()
        else:
            self.save()

    def save(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        data = {
            "owner": self.owner,
            "balance": self.balance,
            "history": self.history
        }
        with open(self.db_path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self):
        with open(self.db_path, "r") as f:
            data = json.load(f)

        self.balance = data.get("balance", 0)
        self.history = data.get("history", [])

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
        if amount <= 0:
            raise ValueError("Amount must be positive")

        if amount > self.balance:
            raise ValueError("Insufficient balance")

        tx = Transaction(
            sender=self.owner,
            receiver=receiver,
            amount=amount
        )

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

    def apply_transaction(self, tx: Transaction):
        if tx.receiver != self.owner:
            return

        self.balance += tx.amount
        self.history.append({
            "type": "tx_received",
            "from": tx.sender,
            "amount": tx.amount,
            "timestamp": int(time.time())
        })

        if self.db_path:
            self.save()

    def __str__(self):
        return f"Wallet(owner={self.owner}, balance={self.balance})"
