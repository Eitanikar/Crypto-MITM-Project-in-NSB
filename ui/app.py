import sys
import os

# הוספת התיקייה הראשית (Parent Directory) לנתיב החיפוש של פייתון
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import streamlit as st
import requests
import time
import json
from wallet.wallet import Wallet
from common.protocol import Transaction

# ==========================================
# 🔧 הגדרות רשת - כאן מעדכנים את ה-IP
# ==========================================
# שים לב: זה ה-IP של מכונת ה-Kali שלך שראינו בתמונה
SERVER_IP = "172.20.10.2"
SERVER_PORT = "5000"
SERVER_URL = f"http://{SERVER_IP}:{SERVER_PORT}"

# ==========================================
# 👛 אתחול ארנק מקומי
# ==========================================
# הארנק הזה משמש כרגע בעיקר לשמירת המפתחות (Private Key)
# היתרה האמיתית מגיעה מהשרת
alice_wallet = Wallet(owner="Alice", db_path="./data/ui_alice_wallet.json")

# ==========================================
# 🖥️ ממשק משתמש (UI Layout)
# ==========================================
st.set_page_config(page_title="Crypto Wallet Demo", page_icon="🛡️", layout="wide")
st.title("🛡️ Secure Crypto Wallet (MITM Demo)")

# --- אזור כרייה (Mining Zone) ---
with st.expander("⛏️ Miner Zone (Click to earn coins)", expanded=True):
    st.write("Simulate Proof-of-Work to earn coins from the network.")
    
    if st.button("🔨 Mine New Block"):
        # 1. סימולציה של "עבודה קשה" (חישוב האש)
        progress_text = "Solving cryptographic puzzle..."
        my_bar = st.progress(0, text=progress_text)
        
        for percent_complete in range(100):
            time.sleep(0.02) # השהייה מלאכותית
            my_bar.progress(percent_complete + 1, text=progress_text)
            
        time.sleep(0.5)
        my_bar.empty() # ניקוי הבר
        
        # 2. שליחת הבקשה לשרת
        try:
            payload = {"miner_address": alice_wallet.address}
            res = requests.post(f"{SERVER_URL}/mine", json=payload, timeout=5)
            
            if res.status_code == 200:
                reward_msg = res.json().get('msg')
                st.success(f"🎉 {reward_msg}")
                time.sleep(1.5)
                st.rerun() # רענון הדף כדי לראות את היתרה החדשה
            else:
                st.error("Mining rejected by server.")
                
        except Exception as e:
            st.error(f"Connection Error: {e}")

st.markdown("---") # קו מפריד

# --- צד ימין: סטטוס חיבור לרשת ---
st.sidebar.header("📡 Network Status")
st.sidebar.text(f"Server: {SERVER_IP}")

network_status = st.sidebar.empty()
balance_display = st.sidebar.empty()

# ניסיון התחברות לשרת לקבלת יתרה
try:
    response = requests.get(f"{SERVER_URL}/balance", timeout=2)
    if response.status_code == 200:
        data = response.json()
        server_balance = data.get("balance", 0)
        
        network_status.success("Connected ✅")
        balance_display.metric("Global Ledger Balance", f"{server_balance} COINS")
    else:
        network_status.warning("Server Error ⚠️")
except requests.exceptions.ConnectionError:
    network_status.error("Offline ❌")
    st.sidebar.error("Cannot reach server. Is it running?")

st.sidebar.markdown("---")
st.sidebar.info(f"**Local Wallet:**\n\nAddr: `{alice_wallet.address[:10]}...`")


# --- אזור ביצוע טרנזקציות ---
st.subheader("💸 Send Transaction")

col1, col2 = st.columns([2, 1])

with col1:
    receiver = st.text_input("Receiver Address", value="Bob_Wallet_Address")
    amount = st.number_input("Amount to Send", min_value=1, value=10)

with col2:
    st.write("### 🔒 Security")
    # זה הכפתור שיקבע אם אנחנו מוגנים או חשופים לתקיפה
    secure_mode = st.checkbox("Enable Digital Signature", value=False)
    
    if secure_mode:
        st.success("Mode: SECURE\n\nTransaction is signed with Private Key.")
    else:
        st.error("Mode: VULNERABLE\n\nSending plain JSON. Susceptible to MITM!")

# --- כפתור השליחה ---
if st.button("🚀 Send Transaction", use_container_width=True):
    
    # 1. יצירת האובייקט הבסיסי
    tx = Transaction(sender=alice_wallet.address, receiver=receiver, amount=amount)

    # 2. חתימה (אם המצב המאובטח פעיל)
    if secure_mode:
        payload_to_sign = tx.get_payload_string()
        tx.signature = alice_wallet.sign_transaction(payload_to_sign)
        st.caption(f"🔏 Generated Signature: `{tx.signature[:30]}...`")

    # 3. שליחה לרשת
    with st.spinner("Broadcasting to network..."):
        try:
            # המרה ל-dict כדי ש-requests ידע לשלוח כ-JSON
            tx_data = json.loads(tx.to_json())
            
            # שליחה לשרת עם פרמטר שמציין אם אנחנו במצב מאובטח
            res = requests.post(
                f"{SERVER_URL}/transact?secure={str(secure_mode).lower()}",
                json=tx_data,
                timeout=5
            )

            if res.status_code == 200:
                st.balloons()
                st.success(f"✅ Transaction Sent! Server Response: {res.json().get('msg')}")
                time.sleep(2)
                st.rerun() # רענון הדף כדי לעדכן יתרה
            else:
                st.error(f"❌ Transaction Rejected: {res.json().get('msg')}")

        except Exception as e:
            st.error(f"🚨 Connection Failed: {e}")