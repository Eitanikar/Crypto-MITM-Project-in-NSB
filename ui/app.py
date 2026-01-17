import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
from wallet.wallet import Wallet

# ---------- Page setup ----------
st.set_page_config(page_title="Crypto Wallet – Mining Demo", layout="centered")

# ---------- Custom CSS ----------
st.markdown("""
<style>
.balance {
    text-align: center;
    font-size: 64px;
    font-weight: bold;
    margin-top: 40px;
}

.mining-container {
    display: flex;
    justify-content: center;
    margin-top: 40px;
}

/* כפתור למרכז, גדול וכתום */
div.stButton > button {

    display: block;
    margin: 0 auto;

    /* רוחב */
    width: 85%;
    max-width: 700px;

    /* צבע */
    background-color: #ff9800;
    color: white;

    /* טקסט */
    font-size: 26px !important;
    font-weight: bold !important;
    white-space: nowrap; 

    /* גובה / צורה */
    border-radius: 12px;
    padding: 12px 150px;
    
    border: none;
    transition: background-color 0.3s;
}

div.stButton > button:hover {
    background-color: #e68900;
    color: white;
    border: none;
}

div.stButton > button:active {
    background-color: #d87f00;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# ---------- Wallet ----------
DB_PATH = "data/ui_alice_wallet.json"

if "wallet" not in st.session_state:
    st.session_state.wallet = Wallet(
        owner="Alice",
        initial_balance=0,
        db_path=DB_PATH
    )

if "mining_active" not in st.session_state:
    st.session_state.mining_active = False

wallet = st.session_state.wallet

# ---------- UI ----------
st.markdown("<h1 style='text-align: center;'>🪙 Crypto Wallet</h1>", unsafe_allow_html=True)
st.markdown(f"<div class='balance'>{wallet.balance}</div>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>COINS</p>", unsafe_allow_html=True)

# ---------- Mining Button ----------
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("START MINING"):
        st.session_state.mining_active = not st.session_state.mining_active
        st.experimental_rerun()


# ---------- Mining State ----------
if st.session_state.mining_active:
    st.success("⛏️ Mining is ACTIVE")
else:
    st.info("⏸️ Mining is STOPPED")

# ---------- History ----------
st.markdown("### 📜 Wallet History")

if wallet.history:
    for event in reversed(wallet.history):
        st.write(f"⛏️ Mined {event['amount']} coins")
else:
    st.write("No activity yet.")
