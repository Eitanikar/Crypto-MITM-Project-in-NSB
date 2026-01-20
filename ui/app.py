import sys
import os
import streamlit as st
import requests
import time
import json
import socket

# הוספת התיקייה הראשית לנתיב החיפוש
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from wallet.wallet import Wallet
from common.protocol import Transaction
from common.encryption import SecureChannel

# ==========================================
# ⚙️ הגדרות
# ==========================================

# כתובת השרת (כשאתה בקאלי, שנה ל-IP של הווינדוס!)
SERVER_URL = "http://127.0.0.1:5000"

# שם הקובץ הקבוע - פשוט ולעניין
WALLET_FILE = "./data/my_wallet.json"

def get_local_ip():
    """טריק למציאת ה-IP האמיתי של המחשב ברשת"""
    try:
        # אנחנו יוצרים חיבור "דמה" לשרת של גוגל (לא באמת שולחים כלום)
        # רק כדי שהמחשב יגיד לנו באיזה כרטיס רשת הוא משתמש
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# ==========================================
# 🔑 ניהול הארנק (טעינה/יצירה)
# ==========================================
# מנסה לטעון ארנק קיים, או יוצר חדש אם אין
current_ip = get_local_ip() # משיג את ה-IP (למשל 192.168.1.15)

if 'my_wallet' not in st.session_state:
    st.session_state['my_wallet'] = Wallet(owner=current_ip, db_path=WALLET_FILE)
my_wallet = st.session_state['my_wallet']

secure_channel = SecureChannel();

# ==========================================
# 🖥️ ממשק משתמש (UI Layout)
# ==========================================
st.set_page_config(page_title="Crypto Wallet Demo", page_icon="💰", layout="wide")
st.title(" 💰Crypto Wallet")

# --- צד ימין: סטטוס וכתובת (מתוקן!) ---
st.sidebar.header("📡 Network Status")

# ==========================================
# 📡 פונקציות תקשורת
# ==========================================

# בדיקת חיבור לשרת
network_status = st.sidebar.empty()
balance_display = st.sidebar.empty()

def get_my_balance_from_server():
    """
    מושך את כל נתוני הארנק מהשרת (יתרה + היסטוריה) ומעדכן את הקובץ המקומי
    """
    try:
        response = requests.get(
            f"{SERVER_URL}/get_user_wallet_balance", 
            params={"address": my_wallet.address,"ip": current_ip} ,
            timeout=2
        )
        if response.status_code == 200:
            server_data = response.json()
            # 1. עדכון היתרה
            my_wallet.balance = server_data.get("balance", 0)
            # 2. עדכון ההיסטוריה! (זה החלק שהיה חסר לך)
            my_wallet.history = server_data.get("history", [])

            # 3. שמירה לקובץ המקומי
            my_wallet.save()
            
         # עדכון האלמנטים הגרפיים (אם הם מוגדרים מחוץ לפונקציה)
        if 'network_status' in globals():
                network_status.success("Connected ✅")
        if 'balance_display' in globals():
                balance_display.metric("Global Balance", f"{my_wallet.balance} COINS")
                return my_wallet.balance
        else:
            network_status.warning("Server Error ⚠️")
            return 0
    except:
        network_status.error("Offline ❌")
        return 0
    
# 1. הפעלת הפונקציה וקבלת המספר העדכני
current_balance = get_my_balance_from_server()
# 2. עדכון הזיכרון של האובייקט
my_wallet.balance = current_balance
# 3. כתיבה פיזית לקובץ my_wallet.json
my_wallet.save()


st.sidebar.markdown("---")
st.sidebar.write("### 🔑 My Wallet Address")
# התיקון: שימוש ב-code מאפשר העתקה נוחה של כל הכתובת!
st.sidebar.code(my_wallet.address, language="text")


# --- אזור כרייה (Mining Zone) ---
with st.expander("⛏️ Miner Zone (Click to earn coins)", expanded=True):
    st.write("Simulate Proof-of-Work to earn coins from the network.")
    
    if st.button("🔨 Mine New Block"):
        progress_text = "Solving cryptographic puzzle..."
        my_bar = st.progress(0, text=progress_text)
        
        for percent_complete in range(100):
            time.sleep(0.01) 
            my_bar.progress(percent_complete + 1, text=progress_text)
        
        time.sleep(0.2)
        my_bar.empty()
        
        # שליחה לשרת
        try:
            payload = {
                "miner_address": my_wallet.address,
                "client_ip": current_ip
            }
            res = requests.post(f"{SERVER_URL}/mine", json=payload, timeout=5)
            
            if res.status_code == 200:
                reward_msg = res.json().get('msg')
                st.success(f"🎉 {reward_msg}")
                new_balance = 50 + get_my_balance_from_server() 
                # ב. מעדכנים את הקובץ המקומי
                my_wallet.balance = new_balance
                my_wallet.save()
                #st.balloons()
                time.sleep(1)
                st.rerun()
            else:
                st.error("Mining rejected by server.")
                
        except Exception as e:
            st.error(f"Connection Error: {e}")

st.markdown("---")

# --- אזור ביצוע טרנזקציות (החדש והמשולב) ---
st.subheader("💸 Send Transaction")

col1, col2 = st.columns([2, 1])

with col1:
    receiver = st.text_input("Receiver Address", value="Bob_Wallet_Address")
    amount_of_transaction = st.number_input("Amount to Send", min_value=1, value=50)

# בורר מצבים (החלק החשוב להדגמה)
with col2:
    st.write("### 🔒 Security Level")
    
    security_level = st.radio(
        "Select Protocol:",
        ("1. Unsafe (HTTP)", "2. Signed (Integrity)", "3. Encrypted (Confidentiality)"),
        index=1
    )

    if "Unsafe" in security_level:
        st.error("⚠️ VULNERABLE! \nExposed to Sniffing & MITM.")
    elif "Signed" in security_level:
        st.warning("🛡️ INTEGRITY OK. \nData visible, cannot be changed.")
    else:
        st.success("🔒 FULLY SECURE. \nData is encrypted.")

# --- כפתור השליחה (הלוגיקה המאוחדת) ---
if st.button("🚀 Send Transaction"):
    try:
        # 1. יצירת הטרנזקציה וחתימה (תמיד חותמים, השרת מחליט מה לעשות עם זה)
        tx = my_wallet.create_transaction(receiver, int(amount_of_transaction))
        
        payload_to_sign = tx.get_payload_string()
        signature = my_wallet.sign_transaction(payload_to_sign)
        tx.signature = signature
        
        # המרה למילון לשימוש ב-requests
        tx_dict = json.loads(tx.to_json())

        # 2. שליחה לפי רמת האבטחה שנבחרה
        
        # מצב 3: הצפנה מלאה
        if "Encrypted" in security_level:
            with st.spinner("🔒 Encrypting payload..."):
                encrypted_payload = secure_channel.encrypt_data(tx.to_json())
                response = requests.post(f"{SERVER_URL}/transact_secure", json={"data": encrypted_payload})
                
        # מצב 2: חתימה בלבד (רגיל)
        elif "Signed" in security_level:
            with st.spinner("🛡️ Sending signed transaction..."):
                response = requests.post(f"{SERVER_URL}/transact?secure=true", json=tx_dict)

        # מצב 1: לא בטוח (פרוץ)
        else:
            with st.spinner("⚠️ Sending UNSAFE transaction..."):
                response = requests.post(f"{SERVER_URL}/transact?secure=false", json=tx_dict)

        # 3. טיפול בתשובה
        if response.status_code == 200:
            st.success(f"✅ Transaction Successful!")
            st.json(response.json())
            st.balloons()
        else:
            st.error(f"❌ Transaction Failed!")
            st.write(f"Server Response: {response.text}")

    except Exception as e:
        st.error(f"❌ Error: {e}")