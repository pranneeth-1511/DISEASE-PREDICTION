import streamlit as st
from appwrite.client import Client
from appwrite.services.account import Account
from appwrite.services.databases import Databases
from appwrite.services.storage import Storage
from appwrite.id import ID
from appwrite.query import Query
from appwrite.input_file import InputFile
from datetime import datetime
import hmac
import hashlib

# Load Config
ENDPOINT = st.secrets["APPWRITE_ENDPOINT"]
PROJECT_ID = st.secrets["APPWRITE_PROJECT_ID"]
API_KEY = st.secrets["APPWRITE_API_KEY"]
DB_ID = st.secrets["APPWRITE_DB_ID"]
COL_ID = st.secrets["APPWRITE_COL_ID"]
BUCKET_ID = st.secrets["APPWRITE_BUCKET_ID"]

@st.cache_resource
def get_server_client():
    client = Client()
    client.set_endpoint(ENDPOINT)
    client.set_project(PROJECT_ID)
    client.set_key(API_KEY)
    return client

def get_auth_client():
    client = Client()
    client.set_endpoint(ENDPOINT)
    client.set_project(PROJECT_ID)
    return client

# Authentication Methods
def sign_in_with_email(email, password):
    client = get_auth_client()
    account = Account(client)
    try:
        session = account.create_email_password_session(email=email, password=password)
        profile = ensure_user_profile(session.userid, email)
        signature = generate_session_signature(session.userid)
        
        return {
            "localId": session.userid, 
            "email": email, 
            "stoken": signature, # Secure Token
            "role": profile.get('role', 'user')
        }
    except Exception as e:
        print(f"Login Error Detail: {e}")
        return {"error": {"message": str(e)}}

def sign_up_with_email(email, password):
    client = get_auth_client()
    account = Account(client)
    try:
        user = account.create(user_id=ID.unique(), email=email, password=password)
        session = account.create_email_password_session(email=email, password=password)
        
        profile = ensure_user_profile(session.userid, email)
        signature = generate_session_signature(session.userid)
        
        return {
            "localId": session.userid, 
            "email": email, 
            "stoken": signature,
            "role": profile.get('role', 'user')
        }
    except Exception as e:
        print(f"Signup Error Detail: {e}")
        return {"error": {"message": str(e)}}

def ensure_user_profile(user_id, email):
    """
    Checks if a user profile exists. If not, creates one.
    Automatically assigns 'admin' role to the first user in the system.
    """
    databases = Databases(get_server_client())
    try:
        # 1. Check for existing profile
        profiles = databases.list_documents(DB_ID, 'profiles', queries=[Query.equal('userid', user_id)])
        if len(profiles.documents) > 0:
            d = profiles.documents[0].to_dict()
            if 'data' in d and isinstance(d['data'], dict): d.update(d['data'])
            return {"userid": user_id, "email": d.get('email', ''), "role": d.get('role', 'user')}
        
        # 2. If not found, create it
        # Count all profiles to determine if this is the first user
        total_profiles = databases.list_documents(DB_ID, 'profiles', queries=[Query.limit(1)])
        role = 'admin' if total_profiles.total == 0 else 'user'
        
        databases.create_document(DB_ID, 'profiles', ID.unique(), {
            'userid': user_id,
            'email': email,
            'role': role
        })
        
        return {"userid": user_id, "email": email, "role": role}
    except Exception as e:
        print(f"Profile Provisioning Error: {e}")
        return {"userid": user_id, "email": email, "role": "user"}

def generate_session_signature(user_id):
    """
    Generates a cryptographically secure HMAC signature for the user ID 
    using the APPWRITE_API_KEY as the secret.
    """
    return hmac.new(API_KEY.encode(), user_id.encode(), hashlib.sha256).hexdigest()

def verify_session_signature(user_id, signature):
    """
    Verifies that the provided signature matches the user_id.
    """
    if not user_id or not signature:
        return False
    expected = generate_session_signature(user_id)
    return hmac.compare_digest(expected, signature)

def verify_session_jwt(jwt_token):
    # Keeping the signature for compatibility but it's no longer used
    return {"valid": False}

def get_user_profile(user_id):
    """Fetch user profile metadata securely from the profiles database."""
    databases = Databases(get_server_client())
    try:
        profiles = databases.list_documents(DB_ID, 'profiles', queries=[Query.equal('userid', user_id)])
        if len(profiles.documents) > 0:
            d = profiles.documents[0].to_dict()
            if 'data' in d and isinstance(d['data'], dict): d.update(d['data'])
            return {"userid": user_id, "email": d.get('email', ''), "role": d.get('role', 'user')}
    except:
        pass
    return {"userid": user_id, "email": "", "role": "user"}

# Admin User Management
def get_all_users():
    databases = Databases(get_server_client())
    response = databases.list_documents(DB_ID, 'profiles', queries=[Query.limit(100)])
    users = []
    for doc in response.documents:
        d = doc.to_dict()
        if 'data' in d and isinstance(d['data'], dict): d.update(d['data'])
        d['id'] = doc.id
        users.append(d)
    return users

def update_user_role(profile_id, new_role):
    databases = Databases(get_server_client())
    databases.update_document(DB_ID, 'profiles', profile_id, {'role': new_role})

def get_all_diagnoses():
    databases = Databases(get_server_client())
    response = databases.list_documents(DB_ID, COL_ID, queries=[Query.order_desc("timestamp")])
    history = []
    for doc in response.documents:
        d = doc.to_dict()
        if 'data' in d and isinstance(d['data'], dict): d.update(d['data'])
        try: d['timestamp'] = datetime.fromisoformat(d['timestamp'].replace("Z", "+00:00"))
        except: pass 
        d['id'] = doc.id
        history.append(d)
    return history

# Database Methods
def save_diagnosis(user_id, diagnosis_data):
    client = get_server_client()
    databases = Databases(client)
    data = {
        "user_id": user_id,
        "type": diagnosis_data.get('type', ''),
        "diagnosis": diagnosis_data.get('diagnosis', ''),
        "confidence": float(diagnosis_data.get('confidence', 0.0)),
        "timestamp": datetime.now().isoformat()
    }
    if "image_url" in diagnosis_data: data["image_url"] = diagnosis_data["image_url"]
    if "scan_count" in diagnosis_data: data["scan_count"] = int(diagnosis_data["scan_count"])
    if "notes" in diagnosis_data: data["notes"] = diagnosis_data["notes"]

    databases.create_document(database_id=DB_ID, collection_id=COL_ID, document_id=ID.unique(), data=data)

def get_diagnosis_history(user_id):
    client = get_server_client()
    databases = Databases(client)
    response = databases.list_documents(
        database_id=DB_ID, collection_id=COL_ID, queries=[Query.equal("user_id", user_id), Query.order_desc("timestamp")]
    )
    history = []
    for doc in response.documents:
        d = doc.to_dict()
        if 'data' in d and isinstance(d['data'], dict): d.update(d['data'])
        try: d['timestamp'] = datetime.fromisoformat(d['timestamp'].replace("Z", "+00:00"))
        except: pass 
        d['id'] = doc.id
        history.append(d)
    return history

def delete_diagnosis(document_id):
    client = get_server_client()
    databases = Databases(client)
    databases.delete_document(database_id=DB_ID, collection_id=COL_ID, document_id=document_id)

# Storage Methods
def upload_medical_scan(user_id, file, filename):
    client = get_server_client()
    storage = Storage(client)
    file_bytes = file.read()
    input_file = InputFile.from_bytes(file_bytes, filename, mime_type=file.type)
    result = storage.create_file(bucket_id=BUCKET_ID, file_id=ID.unique(), file=input_file)
    file_id = result.id
    url = f"{ENDPOINT}/storage/buckets/{BUCKET_ID}/files/{file_id}/view?project={PROJECT_ID}"
    return url, file_id
