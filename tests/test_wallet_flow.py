import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from wallet.wallet import Wallet
import os
import time

DB_PATH = "data/test_wallet.json"

# ניקוי מצב קודם
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

print("=== Creating wallet ===")
alice = Wallet(owner="Alice", initial_balance=0, db_path=DB_PATH)
print(alice)

print("\n=== Mining simulation ===")
alice.credit(5, reason="mining")
time.sleep(1)
alice.credit(7, reason="mining")
print(alice)

print("\n=== Reload wallet from disk ===")
alice_reloaded = Wallet(owner="Alice", db_path=DB_PATH)
print(alice_reloaded)

print("\n=== Creating transaction ===")
tx = alice_reloaded.create_transaction("Bob", 6)
print(tx)

print("\n=== Final wallet state ===")
print(alice_reloaded)

print("\n=== Wallet history ===")
for event in alice_reloaded.history:
    print(event)
