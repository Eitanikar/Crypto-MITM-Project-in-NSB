import sys
import os
import streamlit as st
import requests
import time
import json

# הוספת התיקייה הראשית לנתיב החיפוש
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from wallet.wallet import Wallet
from common.protocol import Transaction
from common.encryption import SecureChannel

# ==========================================
# 🔧 הגדרות רשת
# ==========================================
# כרגע אנחנו בבדיקה מקומית, אז נשתמש ב-Localhost
# כשתחזור ל-Kali, תחליף את זה ל-IP של השרת
SERVER_URL = "http://127.0.0.1:5000"

# ==========================================
# 👛 אתחול ארנק והצפנה
# ==========================================
if 'alice_wallet' not in st.session_state:
    st.session_state['alice_wallet'] = Wallet(owner="Alice", db_path="./data/ui_alice_wallet.json")

alice_wallet = st.session_state['alice_wallet']
secure_channel = SecureChannel()

# ==========================================
# 🖥️ ממשק משתמש (UI Layout)
# ==========================================
st.set_page_config(page_title="Crypto Wallet Demo", page_icon="🛡️", layout="wide")
st.title("🛡️ Secure Crypto Wallet (MITM Demo)")

# --- צד ימין: סטטוס וכתובת (מתוקן!) ---
st.sidebar.header("📡 Network Status")

# בדיקת חיבור לשרת
network_status = st.sidebar.empty()
balance_display = st.sidebar.empty()

try:
    response = requests.get(f"{SERVER_URL}/balance", timeout=2)
    if response.status_code == 200:
        data = response.json()
        server_balance = data.get("balance", 0)
        network_status.success("Connected ✅")
        balance_display.metric("Global Balance", f"{server_balance} COINS")
    else:
        network_status.warning("Server Error ⚠️")
except:
    network_status.error("Offline ❌")

st.sidebar.markdown("---")
st.sidebar.write("### 🔑 My Wallet Address")
# התיקון: שימוש ב-code מאפשר העתקה נוחה של כל הכתובת!
st.sidebar.code(alice_wallet.address, language="text")


# --- אזור כרייה (Mining Zone) ---
with st.expander("⛏️ Miner Zone (Click to earn coins)", expanded=True):
    st.write("Simulate Proof-of-Work to earn coins from the network.")
    
    if st.button("🔨 Mine New Block"):
        # האפקט הוויזואלי היפה שלך
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
                "miner_address": alice_wallet.address,
                "miner_name": "Alice"
            }
            res = requests.post(f"{SERVER_URL}/mine", json=payload, timeout=5)
            
            if res.status_code == 200:
                reward_msg = res.json().get('msg')
                st.success(f"🎉 {reward_msg}")
                st.balloons()
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
    amount = st.number_input("Amount to Send", min_value=1, value=10)

with col2:
    st.write("### 🔒 Security Level")
    
    # בורר מצבים (החלק החשוב להדגמה)
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
        tx = alice_wallet.create_transaction(receiver, int(amount))
        
        payload_to_sign = tx.get_payload_string()
        signature = alice_wallet.sign_transaction(payload_to_sign)
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