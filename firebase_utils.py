import firebase_admin
from firebase_admin import credentials, firestore, storage
import streamlit as st
import requests
import json
import os
from datetime import datetime

# Firebase Web API Key for REST operations (Sign-in, etc.)
FIREBASE_WEB_API_KEY = st.secrets["FIREBASE_WEB_API_KEY"]

@st.cache_resource
def initialize_firebase():
    """Initializes Firebase Admin SDK using credentials from st.secrets"""
    try:
        # Check if already initialized
        firebase_admin.get_app()
    except ValueError:
        # Use credentials from st.secrets
        # Ensure we convert the DotMap/Dict from secrets into a clean dict
        service_account_info = dict(st.secrets["firebase_service_account"])
        
        # Fix newlines in private_key if they are escaped as literal '\n'
        if "\\n" in service_account_info["private_key"]:
            service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")
            
        cred = credentials.Certificate(service_account_info)
        firebase_admin.initialize_app(cred, {
            'storageBucket': f"{service_account_info['project_id']}.firebasestorage.app"
        })
    
    # Use database_id='(default)' explicitly
    return firestore.client(database_id="(default)"), storage.bucket()

# Authentication Methods (REST API)
def sign_in_with_email(email, password):
    """Authenticates user with Firebase Auth REST API"""
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    response = requests.post(url, json=payload)
    return response.json()

def sign_up_with_email(email, password):
    """Registers new user with Firebase Auth REST API"""
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_WEB_API_KEY}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    response = requests.post(url, json=payload)
    return response.json()

# Firestore Methods
def save_diagnosis(user_id, diagnosis_data):
    """Saves diagnosis result to Firestore"""
    db, _ = initialize_firebase()
    diagnosis_data['timestamp'] = datetime.now()
    # Add to 'diagnoses' collection
    db.collection('users').document(user_id).collection('diagnoses').add(diagnosis_data)

def get_diagnosis_history(user_id):
    """Fetches diagnosis history for a specific user"""
    db, _ = initialize_firebase()
    docs = db.collection('users').document(user_id).collection('diagnoses').order_by('timestamp', direction=firestore.Query.DESCENDING).stream()
    
    history = []
    for doc in docs:
        d = doc.to_dict()
        d['id'] = doc.id
        history.append(d)
    return history

# Storage Methods
def upload_medical_scan(user_id, file, filename):
    """Uploads file to Firebase Storage and returns public URL"""
    _, bucket = initialize_firebase()
    
    # Define path in storage
    path = f"scans/{user_id}/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
    blob = bucket.blob(path)
    
    # Upload from byte stream
    blob.upload_from_string(file.read(), content_type=file.type)
    
    # Make public (or return signed URL)
    # For simplicity, we'll use a signed URL valid for 7 days
    url = blob.generate_signed_url(expiration=604800) # 7 days
    return url, path
