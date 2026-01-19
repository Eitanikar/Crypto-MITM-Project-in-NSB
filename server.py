from flask import Flask, request, jsonify
from common.encryption import SecureChannel
import time
import ecdsa
import binascii
import json
import os

#אתחל את הערוץ 
secure_channel = SecureChannel()

# ייבוא המחלקות שלך
from wallet.wallet import Wallet
from common.protocol import Transaction

app = Flask(__name__)

# === אתחול ה-Ledger של הבנק ===
server_ledger = Wallet(owner="Network_Ledger", db_path="./data/server_ledger.json")

# --- פונקציית עזר לשמירה בקבצים אישיים ---
def save_to_personal_file(address, record):
    """
    שומר רשומה לקובץ JSON ייחודי לפי כתובת הארנק.
    שם הקובץ יהיה הכתובת עצמה (למשל: data/3a4f...json).
    """
    if not address:
        return

    filename = f"./data/{address}.json"
    personal_history = []

    # מנסים לטעון היסטוריה קיימת אם הקובץ קיים
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f:
                personal_history = json.load(f)
        except:
            pass 
            
    # הוספת הרשומה החדשה
    personal_history.append(record)
    
    # שמירה לקובץ
    with open(filename, "w") as f:
        json.dump(personal_history, f, indent=4)


def verify_signature(tx: Transaction):
    """בדיקת חתימה קריפטוגרפית"""
    try:
        public_key_bytes = binascii.unhexlify(tx.sender)
        vk = ecdsa.VerifyingKey.from_string(public_key_bytes, curve=ecdsa.SECP256k1)
        message = tx.get_payload_string().encode()
        signature_bytes = binascii.unhexlify(tx.signature)
        return vk.verify(signature_bytes, message)
    except Exception as e:
        print(f"Signature verification failed: {e}")
        return False

@app.route('/balance', methods=['GET'])
def get_balance():
    return jsonify({
        "address": server_ledger.address,
        "balance": server_ledger.balance,
        "history": server_ledger.history
    }), 200

@app.route('/mine', methods=['POST'])
def mine():
    data = request.json
    miner_address = data.get("miner_address")
    BLOCK_REWARD = 50
    
    print(f"\n[⛏️] Mining Request from: {miner_address[:10]}...")
    
    try:
        # 1. עדכון היתרה הכללית
        server_ledger.balance += BLOCK_REWARD
        
        # 2. יצירת הרשומה (הגדרה לפני שימוש!)
        mining_record = {
            "type": "mining_reward",
            "sender": "Network_Reward",
            "receiver": miner_address,
            "amount": BLOCK_REWARD,
            "timestamp": int(time.time())
        }
        
        # 3. שמירה ל-Ledger הראשי
        server_ledger.history.append(mining_record)
        server_ledger.save()
        
        # 4. שמירה לקובץ האישי (עכשיו המשתמש מוגדר)
        save_to_personal_file(miner_address, mining_record)
            
        # חישוב יתרה אישית להחזרה למשתמש
        current_user_balance = 0
        for record in server_ledger.history:
            if record.get("receiver") == miner_address:
                current_user_balance += record["amount"]
            if record.get("sender") == miner_address:
                current_user_balance -= record["amount"]

        print(f"    [V] Block Mined! User Balance: {current_user_balance}")
        
        return jsonify({
            "status": "success", 
            "msg": f"Block Mined! You earned {BLOCK_REWARD} coins.",
            "new_balance": current_user_balance
        }), 200
        
    except Exception as e:
        print(f"    [X] Mining Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/transact', methods=['POST'])
def transact():
    try:
        tx = Transaction.from_json(request.data)
        
        print(f"\n[+] New Transaction Received:")
        print(f"    From: {tx.sender[:10]}...")
        print(f"    To:   {tx.receiver}")
        print(f"    Amt:  {tx.amount}")

        is_secure = request.args.get('secure') != 'false' 

        if is_secure:
            if not tx.signature:
                 return jsonify({"status": "error", "msg": "Missing Signature"}), 400
            if not verify_signature(tx):
                return jsonify({"status": "error", "msg": "Invalid Signature"}), 403
        
        # === שלב קריטי: יצירת המשתמש transaction_record כאן ===
        transaction_record = {
            "type": "transaction",
            "sender": tx.sender,
            "receiver": tx.receiver,
            "amount": tx.amount,
            "signature": tx.signature,
            "timestamp": int(time.time())
        }
        
        # שמירה ל-Ledger הראשי
        server_ledger.history.append(transaction_record)
        server_ledger.save()
        
        # === שמירה לקבצים האישיים (עכשיו זה יעבוד כי המשתמש קיים) ===
        save_to_personal_file(tx.sender, transaction_record)   # תיעוד אצל השולח
        save_to_personal_file(tx.receiver, transaction_record) # תיעוד אצל המקבל
            
        print("    [V] Transaction Verified & Recorded.")
        return jsonify({"status": "success", "msg": "Transaction Recorded"}), 200

    except Exception as e:
        print(f"Error processing transaction: {e}")
        return jsonify({"error": str(e)}), 400


@app.route('/transact_secure', methods=['POST'])
def transact_secure():
    """
    נתיב שמקבל רק מידע מוצפן, מפענח אותו, ואז מבצע את הטרנזקציה.
    זה מדמה תקשורת P2P מוצפנת או TLS.
    """
    try:
        # 1. קבלת המידע המוצפן
        data = request.json
        encrypted_content = data.get("data")

        print(f"\n[🔒] Encrypted Request Received: {encrypted_content[:15]}...")

        # 2. פענוח ההצפנה (השרת משתמש במפתח הסודי)
        decrypted_json_str = secure_channel.decrypt_data(encrypted_content)
        print(f"    [🔓] Decrypted successfully! Content: {decrypted_json_str}")

        # 3. המרה חזרה לאובייקט Transaction
        # מכאן והלאה - זה בדיוק כמו טרנזקציה רגילה!
        tx = Transaction.from_json(decrypted_json_str)

        # --- בדיקות אבטחה רגילות (חתימה) ---
        if not tx.signature:
             return jsonify({"status": "error", "msg": "Missing Signature"}), 400

        if not verify_signature(tx):
            print("    [X] Invalid Signature inside encrypted packet!")
            return jsonify({"status": "error", "msg": "Invalid Signature"}), 403

        # --- שמירה ל-Ledger (כמו קודם) ---
        transaction_record = {
            "type": "transaction",
            "sender": tx.sender,
            "receiver": tx.receiver,
            "amount": tx.amount,
            "signature": tx.signature,
            "timestamp": int(time.time())
        }

        server_ledger.history.append(transaction_record)
        server_ledger.save()
        save_to_personal_file(tx.sender, transaction_record)
        save_to_personal_file(tx.receiver, transaction_record)

        print("    [V] Secure Transaction Recorded.")
        return jsonify({"status": "success", "msg": "Secure Transaction Recorded"}), 200

    except Exception as e:
        print(f"    [X] Decryption/Processing Error: {e}")
        return jsonify({"error": "Failed to process secure transaction"}), 400
    
if __name__ == '__main__':
    print("Server running on port 5000...")
    app.run(host='0.0.0.0', port=5000)