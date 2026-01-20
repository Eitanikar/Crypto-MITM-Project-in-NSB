from flask import Flask, request, jsonify
from common.encryption import SecureChannel
import time
import ecdsa
import binascii
import json
import os

# אתחל את הערוץ 
secure_channel = SecureChannel()

# ייבוא המחלקות שלך
from wallet.wallet import Wallet
from common.protocol import Transaction

app = Flask(__name__)

# === אתחול ה-Ledger של הבנק ===
Blockchain_history = Wallet(owner="Network_Ledger", db_path="./data/Blockchain_history.json")

# 1. הנתיב לקובץ הפיזי בדיסק (המחברת)
MAPPING_FILE = "./data/ip_mapping.json"

# מילון שממפה בין כתובת ארנק לכתובת IP
# דוגמה: {'fd39c...': '192.168.1.15'}
wallet_to_ip_map = {}

# --- פונקציית עזר לשמירה בקבצים אישיים ---
def save_to_personal_file(address, record):
    """
    שומר רשומה לקובץ JSON תוך שימוש במחלקת Wallet הקיימת.
    הקובץ ייקרא על שם ה-IP של המשתמש (אם קיים), והיתרה תחושב מחדש לפי ההיסטוריה.
    """
    if not address:
        return
    
    # 1. מציאת שם הקובץ (שהוא ה-IP)
    # -------------------------------------------
    file_identifier = None

    # בדיקה בזיכרון (RAM)
    if address in wallet_to_ip_map:
        file_identifier = wallet_to_ip_map[address]
    else:
        # בדיקה בדיסק (MAPPING_FILE) למקרה שהשרת אותחל
        if os.path.exists(MAPPING_FILE):
            try:
                with open(MAPPING_FILE, "r") as f:
                    saved_map = json.load(f)
                    if address in saved_map:
                        file_identifier = saved_map[address]
                        # עדכון הזיכרון לפעם הבאה
                        wallet_to_ip_map[address] = file_identifier
            except:
                pass
    
    # אם עדיין לא מצאנו IP, נשתמש בכתובת הארנק כברירת מחדל כדי שהמידע לא יאבד
    if not file_identifier:
        file_identifier = address

        # 2. שימוש במחלקת Wallet לניהול הקובץ
    # -------------------------------------------
    filepath = f"./data/{file_identifier}.json"
    # הבנאי של המחלקה שלך חכם: אם נספק לו db_path, הוא ינסה לטעון משם לבד!
    # ה-owner יהיה ה-IP (או הכתובת אם לא מצאנו IP)
    user_wallet = Wallet(owner=file_identifier, db_path=filepath)

    # 3. הוספת העסקה החדשה להיסטוריה
    # -------------------------------------------
    # שימוש ב-.append() הרגיל של הרשימה בתוך האובייקט
    user_wallet.history.append(record)

    # 4. חישוב יתרה מחדש (Balance Recalculation)
    # -------------------------------------------
    # אנחנו לא סומכים על ה-balance הקיים, אלא מחשבים אותו מאפס לפי ההיסטוריה המעודכנת
    new_balance = 0

    for tx in user_wallet.history:
        amount = float(tx.get("amount", 0))
        receiver = tx.get("receiver") or tx.get("recipient")
        sender = tx.get("sender")
        
        # האם הכסף נכנס לארנק הזה? (בודקים מול הכתובת המקורית שהגיעה לפונקציה)
        if receiver == address:
            new_balance += amount
            
        # האם זה תגמול כרייה עבור הארנק הזה?
        elif tx.get("type") == "mining_reward" and tx.get("miner_address") == address:
            new_balance += amount
        
        # האם הכסף יצא מהארנק הזה?
        if sender == address:
            new_balance -= amount

    # עדכון השדה באובייקט
    user_wallet.balance = new_balance

    # 5. שמירה לדיסק
    # -------------------------------------------
    # הפונקציה save() במחלקה שלך כבר יודעת להשתמש ב-self.db_path שהגדרנו בבנאי
    user_wallet.save()
    
    print(f"[💾] Saved wallet for {file_identifier} with balance: {new_balance}")
   

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
def get_Blockchain_balance():
    return jsonify({
        "address": Blockchain_history.address,
        "balance": Blockchain_history.balance,
        "history": Blockchain_history.history
    }), 200

@app.route('/get_user_wallet_balance', methods=['GET'])
def get_user_wallet_balance():
    # 1. קליטת פרמטרים
    address = request.args.get('address')
    client_ip = request.args.get('ip')
    
    target_filename = address
    if address in wallet_to_ip_map:
        target_filename = wallet_to_ip_map[address]
    elif client_ip:
         target_filename = client_ip
    
    filepath = f"./data/{target_filename}.json"

 # 2. אם הקובץ קיים, שולחים את כולו
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            return jsonify(data) # שולח גם balance, גם history, הכל!
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return jsonify({"error": "Wallet not found"}), 404

@app.route('/mine', methods=['POST'])
def mine():
    # 1. קריאת הנתונים
    data = request.get_json()
    miner_address = data.get('miner_address', "Network_Ledger")
    capture_client_ip(miner_address)
    
    reward_amount = 50
    
    # 2. יצירת רשומת הטרנזקציה (פרס כרייה)
    transaction = {
        "type": "mining_reward",
        "sender": "Network_Mining_Reward",
        "receiver": miner_address,
        "amount": reward_amount,
        "timestamp": time.time()
    }
    
    # 3. שמירה ל-Ledger הראשי של השרת
    Blockchain_history.history.append(transaction)
    Blockchain_history.save()
    
    if miner_address != "Network_Ledger":
        save_to_personal_file(miner_address, transaction)

    print(f"[+] Block Mined! Reward sent to: {miner_address[:10]}...")

    return jsonify({
        "msg": f"Block mined successfully! Reward sent to {miner_address[:10]}...",
        "amount": reward_amount
    }), 200

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
        
        # === דילוג על בדיקת יתרה (Bypass) ===
        # כאן הייתה הבדיקה if balance < amount. מחקנו אותה כדי לאפשר את התקיפה.
        
        transaction_record = {
            "type": "transaction",
            "sender": tx.sender,
            "receiver": tx.receiver,
            "amount": tx.amount,
            "signature": tx.signature,
            "timestamp": int(time.time())
        }
        
        # שמירה ל-Ledger הראשי
        Blockchain_history.history.append(transaction_record)
        Blockchain_history.save()
        
        # שמירה לקבצים האישיים
        save_to_personal_file(tx.sender, transaction_record)
        save_to_personal_file(tx.receiver, transaction_record)
            
        print("    [V] Transaction Verified & Recorded.")
        return jsonify({"status": "success", "msg": "Transaction Recorded"}), 200

    except Exception as e:
        print(f"Error processing transaction: {e}")
        return jsonify({"error": str(e)}), 400


@app.route('/transact_secure', methods=['POST'])
def transact_secure():
    try:
        # 1. קבלת המידע המוצפן
        data = request.json
        encrypted_content = data.get("data")

        print(f"\n[🔒] Encrypted Request Received: {encrypted_content[:15]}...")

        # 2. פענוח ההצפנה
        decrypted_json_str = secure_channel.decrypt_data(encrypted_content)
        print(f"    [🔓] Decrypted successfully! Content: {decrypted_json_str}")

        # 3. המרה חזרה לאובייקט Transaction
        tx = Transaction.from_json(decrypted_json_str)

        if not tx.signature:
             return jsonify({"status": "error", "msg": "Missing Signature"}), 400

        if not verify_signature(tx):
            print("    [X] Invalid Signature inside encrypted packet!")
            return jsonify({"status": "error", "msg": "Invalid Signature"}), 403

        # שמירה
        transaction_record = {
            "type": "transaction",
            "sender": tx.sender,
            "receiver": tx.receiver,
            "amount": tx.amount,
            "signature": tx.signature,
            "timestamp": int(time.time())
        }

        Blockchain_history.history.append(transaction_record)
        Blockchain_history.save()
        save_to_personal_file(tx.sender, transaction_record)
        save_to_personal_file(tx.receiver, transaction_record)

        print("    [V] Secure Transaction Recorded.")
        return jsonify({"status": "success", "msg": "Secure Transaction Recorded"}), 200

    except Exception as e:
        print(f"    [X] Decryption/Processing Error: {e}")
        return jsonify({"error": "Failed to process secure transaction"}), 400
    
def capture_client_ip(wallet_address):
    if not wallet_address:
        return

    client_ip = request.remote_addr
    
    # 1. בדיקה מהירה בזיכרון: האם משהו השתנה?
    # אם הכתובת כבר מוכרת וה-IP הוא אותו IP בדיוק - אל תעשה כלום!
    if wallet_to_ip_map.get(wallet_address) == client_ip:
        return 

    # --- אם הגענו לפה, סימן שמשהו חדש קרה! ---
    
    # עדכון בזיכרון
    wallet_to_ip_map[wallet_address] = client_ip
    
    # שמירה לקובץ (רק כשצריך באמת)
    try:
        current_data = {}
        if os.path.exists(MAPPING_FILE):
            with open(MAPPING_FILE, "r") as f:
                try:
                    current_data = json.load(f)
                except:
                    pass
        
        current_data[wallet_address] = client_ip
        
        with open(MAPPING_FILE, "w") as f:
            json.dump(current_data, f, indent=4)
            
        print(f"[📝] NEW IP DETECTED! Saved: {wallet_address[:6]}... -> {client_ip}")

    except Exception as e:
        print(f"[!] Error saving map: {e}")

if __name__ == '__main__':
    print("Server running on port 5000...")
    # host='0.0.0.0' מאפשר חיבורים חיצוניים (מה-Kali ומהטלפון)
    app.run(host='0.0.0.0', port=5000)