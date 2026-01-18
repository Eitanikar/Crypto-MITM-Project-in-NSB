from flask import Flask, request, jsonify
from wallet.wallet import Wallet
from common.protocol import Transaction
import ecdsa
import binascii

app = Flask(__name__)

# יצירת ארנק "בנק" לשרת שישמור את ההיסטוריה
# נשמור אותו בנתיב נפרד כדי לא לדרוס את הארנק של אליס אם קיים שם
server_ledger = Wallet(owner="Network_Ledger", db_path="./data/server_ledger.json")

def verify_signature(tx: Transaction):
    """בודק אם החתימה תואמת לתוכן העסקה ולשולח"""
    if not tx.signature:
        return False

    try:
        # המרת המפתח הציבורי מ-Hex לאובייקט
        public_key_bytes = binascii.unhexlify(tx.sender)
        verifying_key = ecdsa.VerifyingKey.from_string(public_key_bytes, curve=ecdsa.SECP256k1)
        
        # שחזור המידע המקורי (Payload) לבדיקה
        payload_str = tx.get_payload_string()
        
        return verifying_key.verify(binascii.unhexlify(tx.signature), payload_str.encode())
    except Exception as e:
        print(f"Signature Error: {e}")
        return False

@app.route('/balance', methods=['GET'])
def get_balance():
    return jsonify({
        "balance": server_ledger.balance,
        "history": server_ledger.history
    })

@app.route('/transact', methods=['POST'])
def transact():
    data = request.json
    try:
        # בניית אובייקט טרנזקציה מהמידע שהתקבל
        tx = Transaction(**data)
        
        print(f"\n[+] New Transaction Received:")
        print(f"    From: {tx.sender[:10]}...")
        print(f"    To:   {tx.receiver}")
        print(f"    Amt:  {tx.amount}")

        # בדיקה האם הבקשה סומנה כ"מאובטחת"
        is_secure = request.args.get('secure') == 'true'

        if is_secure:
            print("    [?] Security Mode ON. Verifying signature...")
            if verify_signature(tx):
                print("    [V] Signature VALID.")
                return jsonify({"status": "success", "msg": "Transaction Verified & Approved"}), 200
            else:
                print("    [X] Signature INVALID! Blocking transaction.")
                return jsonify({"status": "error", "msg": "Invalid Signature - Possible Attack!"}), 403
        else:
            print("    [!] Security Mode OFF. Accepting blindly.")
            return jsonify({"status": "success", "msg": "Transaction Accepted (Unverified)"}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 400

@app.route('/mine', methods=['POST'])
def mine():
    data = request.json
    miner_address = data.get("miner_address")
    
    # סכום הפרס על כריית בלוק
    BLOCK_REWARD = 50
    
    print(f"\n[⛏️] Mining Request from: {miner_address[:10]}...")
    
    try:
        server_ledger.credit(BLOCK_REWARD, reason="mining_reward")
        print(f"    [V] Block Mined! Reward credited. New Balance: {server_ledger.balance}")
        
        return jsonify({
            "status": "success", 
            "msg": f"Block Mined! You earned {BLOCK_REWARD} coins.",
            "new_balance": server_ledger.balance
        }), 200
        
    except Exception as e:
        print(f"    [X] Mining Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
        # מריץ על 0.0.0.0 כדי לאפשר גישה מבחוץ (מה-Windows)
    print("Server running on port 5000...")
    app.run(host='0.0.0.0', port=5000)