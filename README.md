***Crypto-Blockchain Project: Security & Mitigation***
A simulation of a Blockchain environment using ECDSA signatures and a demonstrated Replay Attack.

📌 Overview
This project explores the intersection of cryptography and protocol security. It features a simplified Blockchain server where transactions are signed using Elliptic Curve Cryptography (ECC), specifically the secp256k1 curve (the same one used by Bitcoin).

The core of the project is demonstrating a Replay Attack vulnerability: showing how a valid, signed transaction can be captured and "replayed" to manipulate account balances, highlighting why signatures alone are not enough for secure protocols.

🚀 Key Features
Blockchain Server: Built with Python & Flask to manage ledgers and balances.

Cryptographic Wallets: Using the ecdsa library to generate private/public keys and sign transactions.

Real-time UI: A frontend dashboard to visualize the blockchain, account history, and live balances.

Security Research: A dedicated attacks/ directory containing scripts for Sniffing and Replay Attacks.

🏗️ Technical Architecture
Backend: Python (Flask, Requests, ECDSA)

Frontend: HTML, CSS, JavaScript (Fetch API)

Environment: Developed and tested on Windows & WSL2 (Ubuntu).

⚔️ The Replay Attack Demonstration
The project includes a documented attack scenario:

Capture: A transaction is sent from the wallet to the server over an insecure channel (HTTP).

Intercept: Using a Sniffer script to capture the valid JSON payload (including the signature).

Exploit: Using the replay_attack.py script to resend the exact same signed data multiple times.

Result: The server accepts the duplicated transactions as "valid" because the signature matches the data, leading to unauthorized fund depletion.

🛠️ Installation & Usage
Prerequisites
Bash
pip install flask requests ecdsa flask-cors
Running the Project
Start the Server:

Bash
python server.py
Launch the Wallet UI: Open index.html in your browser.

Execute Attack (WSL/Linux):

Bash
cd attacks
python3 replay_attack.py
🛡️ Future Mitigations
To prevent this vulnerability, future iterations will include:

Nonces: Unique transaction counters per address.

Timestamps: Expiration windows for signed messages.

HTTPS: Encrypting the transport layer to prevent initial sniffing.
