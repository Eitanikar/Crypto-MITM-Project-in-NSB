from common.protocol import Transaction


class Wallet:
    def __init__(self, owner: str, initial_balance: int = 0):
        self.owner = owner
        self.balance = initial_balance
        self.history = []

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
        self.history.append(tx)
        return tx

    def apply_transaction(self, tx: Transaction):
        if tx.receiver != self.owner:
            return

        self.balance += tx.amount
        self.history.append(tx)

    def __str__(self):
        return f"Wallet(owner={self.owner}, balance={self.balance})"
