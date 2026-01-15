# common/protocol.py

import json
from dataclasses import dataclass


@dataclass
class Transaction:
    sender: str
    receiver: str
    amount: int

    def to_json(self) -> str:
        """
        Convert the transaction to a JSON string.
        """
        data = {
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount
        }
        return json.dumps(data)
