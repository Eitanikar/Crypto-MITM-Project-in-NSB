from common.protocol import Transaction

tx = Transaction(
    sender="Alice",
    receiver="Bob",
    amount=10
)

print(tx)
print()
print(tx.to_json())
