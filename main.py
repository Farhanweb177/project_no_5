import streamlit as st
import sqlite3
import hashlib
import os
from cryptography.fernet import Fernet

KEY_FILE = "simple_secret.key"

def load_key():
    """Load the secret key from the current directory."""
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as F:
            F.write(key)

    else:
        with open(KEY_FILE, "rb") as F:
            key = F.read()
    return key

cipher = Fernet(load_key())

def init_db():
    conn = sqlite3.connect("simple_data.db")
    c = conn.cursor()
    c.execute("""
         CREATE TABLE IF NOT EXISTS vault (
              label TEXT PRIMARY KEY,
              encrypted_text TEXT,
              passkey TEXT
              )
              """)
    conn.commit()
    conn.close()

init_db()

def hash_passkey(passkey):
    return hashlib.sha256(passkey.encode()).hexdigest()

def encrypt(text):
    return cipher.encrypt(text.encode()).decode()

def decrypt_text(encrypted_text):
    return cipher.decrypt(encrypted_text.encode()).decode()

st.title("Secure Data Encryption App")
menu = ["Store Secret", "Retrieve Secret"]
choice = st.sidebar.selectbox("Choose Option", menu)

if choice == "Store Secret":
    st.header("Store a New Secret")

    label = st.text_input("Label (Unique Identifier): ")
    secret = st.text_area("Your Secret Text")
    passkey = st.text_input("Passkey (to Protectect it): ", type="password")

    if st.button("Encrypt and save"):
        if label and secret and passkey:
            conn = sqlite3.connect("simple_data.db")
            c = conn.cursor()

            encrypted = encrypt(secret)
            hashed_passkey = hash_passkey(passkey)

            try:
                c.execute("INSERT INTO vault (label, encrypted_text, passkey) VALUES (?, ?, ?)",
                          (label, encrypted, hashed_passkey))
                conn.commit()
                st.success("Secret saved successfully!")
            except sqlite3.IntegrityError:
                st.error("Label already exists. Please use a different label.")
                conn.close()
        else:
            st.warning("Please fill all fields.")

elif choice == "Retrieve Secret":
    st.header("Retrieve Your Secret")

    label = st.text_input("Enter Label: ")
    passkey = st.text_input("Enter Passkey: ", type="password")

    if st.button("Decrypt"):
        conn = sqlite3.connect("simple_data.db")
        c = conn.cursor()
        c.execute("SELECT encrypted_text, passkey FROM vault WHERE label=?", (label,))
        result = c.fetchone()
        conn.close()

        if result:
            encrypted_text , stored_hash = result
            if hash_passkey(passkey) == stored_hash:
                decrypted = decrypt_text(encrypted_text)
                st.success("Here is your secret:")
                st.code(decrypted)
            else:
                st.error("Incorrect passkey.")
        else:
            st.warning("Label not found. Please check the label and try again.")