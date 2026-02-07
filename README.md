# Blockchain Security Simulation: ECDSA and Replay Attack

## Project Overview
This project demonstrates a functional Blockchain environment implemented in Python, focusing on the implementation of digital signatures and the identification of protocol vulnerabilities. The system utilizes Elliptic Curve Digital Signature Algorithm (ECDSA) to secure transactions but remains intentionally vulnerable to a Replay Attack to highlight critical security gaps in basic protocol designs.

---

## Technical Specifications

| Component | Technology |
| :--- | :--- |
| **Backend** | Python 3, Flask |
| **Cryptography** | ECDSA (Curve: SECP256k1) |
| **Frontend** | JavaScript (ES6+), HTML5, CSS3 |
| **Environment** | Windows / WSL2 (Ubuntu) |

---

## Cryptographic Implementation

The project implements the **secp256k1** elliptic curve for all wallet operations. This specific curve was selected due to its industry-standard status in major cryptocurrencies like Bitcoin.



* **Private Key**: A 256-bit random integer used for signing transactions.
* **Public Key**: A point on the curve derived from the private key, used for signature verification.
* **Signing Process**: Transactions are hashed and signed using the `ecdsa` library, producing `r` and `s` values that comprise the digital signature.

---

## Security Analysis: Replay Attack Demonstration

The primary objective of this project is to demonstrate how valid cryptographic signatures can be misused if the protocol lacks state management.

### Vulnerability Description
The server validates the mathematical integrity of the signature but does not track if a specific signature has been used previously. This allows an attacker to capture a legitimate transaction and re-submit it to the network.



### Attack Workflow
1. **Interception**: Using the `sniffer.py` script, the attacker captures the JSON payload of a valid transaction.
2. **Repetition**: The `replay_attack.py` script resubmits the exact same payload multiple times to the `/transact` endpoint.
3. **Exploitation**: The server accepts each duplicate as a new, valid transaction, leading to unauthorized balance depletion.

---

## Implementation Details

### Setup and Installation
To install the necessary dependencies, run the following command:
```bash
pip install flask requests ecdsa flask-cors
```
### Execution Instructions
1. **Initialize Blockchain Server:**
```bash
python server.py
```
2. **Access Wallet Interfac:** Open `index.html` in a web browser. Ensure the connection is set to `localhost:5000`. 
3. **Execute Security Attack:** Navigate to the `attacks/` directory in a WSL terminal and run:
```bash
python3 replay_attack.py
```
### python3 replay_attack.py
To secure the protocol against the demonstrated attacks, the following mechanisms are recommended for implementation:

1. **Transaction Nonce:** A unique, incremental counter for each address to ensure signature uniqueness.

2. **Timestamp Validation:** Enforcing expiration windows for signed transaction requests.

3. **TLS/SSL Encryption:** Protecting the transport layer to prevent initial packet interception.


