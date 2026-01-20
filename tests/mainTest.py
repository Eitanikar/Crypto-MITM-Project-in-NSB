from wallet.wallet import Wallet
import time


def main():
    alice = Wallet(
        owner="Alice",
        initial_balance=0,
        db_path="data/alice_wallet.json"
    )

    print("Initial state:")
    print(alice)

    print("\nSimulating mining rewards...")
    alice.credit(3, reason="mining")
    time.sleep(1)
    alice.credit(5, reason="mining")

    print("\nAfter mining:")
    print(alice)

    print("\nCreating transaction to Bob...")
    tx = alice.create_transaction("Bob", 4)
    print(tx.to_json())

    print("\nFinal state:")
    print(alice)


if __name__ == "__main__":
    main()
