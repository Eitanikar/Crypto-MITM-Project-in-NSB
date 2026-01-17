# common/protocol.py

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
        מחזירה את המחרוזת המייצגת את תוכן העסקה בלבד (ללא החתימה).
        על המחרוזת הזו אנחנו חותמים.
        """
        payload = {
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount
        }
        # sort_keys=True חשוב מאוד! כדי שהסדר תמיד יהיה זהה בחתימה ובאימות
        return json.dumps(payload, sort_keys=True) 

    def to_json(self) -> str:"""
        ממיר את כל האובייקט (כולל החתימה אם יש) ל-JSON למשלוח ברשת
        """
        return json.dumps(asdict(self), sort_keys=True)

    @staticmethod
    def from_json(json_str: str):
        data = json.loads(json_str)
        return Transaction(**data)  