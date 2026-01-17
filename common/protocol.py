import json
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class Transaction:
    sender: str
    receiver: str
    amount: int
    signature: Optional[str] = None

    def get_payload_string(self) -> str:
        """
        Returns the JSON string of the transaction data (without signature).
        This string is what we sign digitally.
        """
        payload = {
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount
        }
        return json.dumps(payload, sort_keys=True)

    def to_json(self) -> str:
        """Converts the full transaction object to a JSON string"""
        return json.dumps(asdict(self), sort_keys=True)

    @staticmethod
    def from_json(json_str: str):
        """Loads a transaction object from a JSON string"""
        data = json.loads(json_str)
        return Transaction(**data)