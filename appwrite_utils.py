import streamlit as st
from appwrite.client import Client
from appwrite.services.account import Account
from appwrite.services.databases import Databases
from appwrite.services.storage import Storage
from appwrite.id import ID
from appwrite.query import Query
from appwrite.input_file import InputFile
from datetime import datetime

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
def sign_up_with_email(email, password):
    client = get_auth_client()
    account = Account(client)
    try:
        user = account.create(user_id=ID.unique(), email=email, password=password)
        session = account.create_email_password_session(email=email, password=password)
        
        # Check if first user
        databases = Databases(get_server_client())
        existing = databases.list_documents(DB_ID, 'profiles', queries=[Query.limit(1)])
        role = 'admin' if len(existing.documents) == 0 else 'user'
        
        databases.create_document(DB_ID, 'profiles', ID.unique(), {
            'userid': session.userid,
            'email': email,
            'role': role
        })
        
        return {"localId": session.userid, "email": email, "idToken": session.id, "role": role}
    except Exception as e:
        return {"error": {"message": str(e)}}

def sign_in_with_email(email, password):
    client = get_auth_client()
    account = Account(client)
    try:
        session = account.create_email_password_session(email=email, password=password)
        
        databases = Databases(get_server_client())
        profiles = databases.list_documents(DB_ID, 'profiles', queries=[Query.equal('userid', session.userid)])
        
        role = 'user'
        if len(profiles.documents) > 0:
            d = profiles.documents[0].to_dict()
            if 'data' in d and isinstance(d['data'], dict): d.update(d['data'])
            role = d.get('role', 'user')
            
        return {"localId": session.userid, "email": email, "idToken": session.id, "role": role}
    except Exception as e:
        return {"error": {"message": str(e)}}

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
