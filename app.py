import streamlit as st
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.preprocessing.sequence import pad_sequences
from PIL import Image
import pytesseract
import pickle
import os
import appwrite_utils as aw
from io import BytesIO
from pages_ui.auth_page import show_auth_page
from pages_ui.cancer_detection import show_cancer_detection
from pages_ui.symptom_analysis import show_symptom_analysis
from pages_ui.diagnosis_history import show_diagnosis_history
from pages_ui.patient_history import show_patient_history
from pages_ui.user_management import show_user_management

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

st.set_page_config(page_title="MediScan AI", layout="wide", page_icon="🏥")

# --- Custom CSS Injection ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Outfit:wght@400;700&display=swap');
    
    :root {
        --primary: #0068C9;
        --secondary: #00A699;
        --accent: #FF4B4B;
        --bg-main: #F8FAFC;
        --card-bg: #FFFFFF;
        --text-main: #1E293B;
        --text-muted: #64748B;
        --border: #E2E8F0;
    }

    /* Global Styles */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        font-family: 'Inter', sans-serif;
        background-color: var(--bg-main);
        overflow: auto !important;
    }
    
    .stApp {
        overflow: auto !important;
        height: auto !important;
    }
    
    /* Hide Streamlit elements gracefully */
    header[data-testid="stHeader"], footer {
        visibility: hidden !important;
        display: none !important;
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #f1f1f1; }
    ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }

    /* Hero Title & Sidebar Style */
    .hero-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 2rem;
        background: linear-gradient(135deg, #0068C9 0%, #00A699 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        text-align: center;
        letter-spacing: -0.02em;
    }
    .hero-subtitle {
        text-align: center;
        color: var(--text-muted);
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
        font-weight: 500;
    }
    
    /* Modern Dashboard Cards */
    .card {
        background-color: var(--card-bg);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border: 1px solid var(--border);
        margin-bottom: 1rem;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }
    
    /* Status Badges */
    .badge {
        padding: 6px 12px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.025em;
        display: inline-flex;
        align-items: center;
    }
    .badge-primary { background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; }
    .badge-success { background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; }
    .badge-warning { background: #FFFBEB; color: #D97706; border: 1px solid #FEF3C7; }

    /* Login Image Container */
    .login-image-container {
        border-radius: 24px;
        overflow: hidden;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        height: 60vh;
        border: 4px solid white;
    }
    .login-image-container img {
        object-fit: cover;
        width: 100%;
        height: 100%;
    }

    /* Style Streamlit Buttons to match Premium Look */
    .stButton>button {
        border-radius: 12px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.5rem !important;
        transition: all 0.2s !important;
        background: linear-gradient(135deg, #0068C9 0%, #004F9E 100%) !important;
        color: white !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
    }
    .stButton>button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1) !important;
        opacity: 0.95;
    }
</style>
""", unsafe_allow_html=True)

# --- Session State Management ---
if 'user' not in st.session_state:
    st.session_state.user = None

# --- Firebase Auth UI ---
# --- Session Restoration Logic (Secure HMAC Guard) ---
if not st.session_state.user:
    params = st.query_params
    if 'userid' in params and 'stoken' in params:
        with st.spinner("🛡️ Verifying secure medical gateway..."):
            is_valid = aw.verify_session_signature(params['userid'], params['stoken'])
            if is_valid:
                 profile = aw.ensure_user_profile(params['userid'], "")
                 if profile.get('userid'):
                     st.session_state.user = {
                         "localId": profile['userid'],
                         "email": profile['email'],
                         "role": profile['role'],
                         "stoken": params['stoken']
                     }
                     st.rerun()
            else:
                 # Block access and clean up
                 st.query_params.clear()
                 st.error("🔒 Security Alert: Invalid or tampered session token. Access denied.")
                 st.stop() 

def auth_sidebar():
    st.sidebar.markdown('<div style="text-align: center; margin-top: -1rem; padding-bottom: 1rem;">', unsafe_allow_html=True)
    st.sidebar.markdown("### 🏥 MediScan AI Portal")
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.user:
        role_label = "👑 ADMIN" if st.session_state.user.get('role') == 'admin' else "USER"
        
        # User Profile Card in Sidebar
        st.sidebar.markdown(f"""
        <div class="card" style="padding: 12px; border-left: 4px solid var(--primary);">
            <div style="font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase;">Logged in as</div>
            <div style="font-weight: 700; font-size: 0.85rem; color: var(--text-main); margin-bottom: 4px;">{st.session_state.user['email']}</div>
            <span class="badge badge-primary">{role_label}</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.sidebar.markdown('<div style="height: 1rem;"></div>', unsafe_allow_html=True)
        
        if st.sidebar.button("🔌 Signout", use_container_width=True, help="Securely end your healthcare session."):
            st.session_state.user = None
            st.query_params.clear()
            st.rerun()
    else:
        st.sidebar.info("Please log in to the diagnostic portal to proceed.")

auth_sidebar()

@st.cache_resource
def load_resources():
    resources = {}
    
    try:
        resources['cnn_model'] = tf.keras.models.load_model('cancer_type_model.keras')
        if os.path.exists('class_names.pickle'):
            with open('class_names.pickle', 'rb') as f:
                resources['class_names'] = pickle.load(f)
        else:
            resources['class_names'] = ['ALL', 'Brain Cancer', 'Breast Cancer', 'Cervical Cancer', 
                                       'Kidney Cancer', 'Lung and Colon Cancer', 'Lymphoma', 'Oral Cancer']
    except Exception as e:
        st.error(f"❌ Error loading Cancer Model: {e}")
        resources['cnn_model'] = None

    try:
        resources['lstm_model'] = tf.keras.models.load_model('clinical_text_model.keras')
        
        with open('tokenizer.pickle', 'rb') as handle:
            resources['tokenizer'] = pickle.load(handle)
            
        with open('label_encoder.pickle', 'rb') as handle:
            resources['label_encoder'] = pickle.load(handle)
    except Exception as e:
        print(f"Text model not found or error: {e}") 
        resources['lstm_model'] = None

    return resources

res = load_resources()

st.markdown("<h1 class='hero-title'>🏥 MediScan AI</h1>", unsafe_allow_html=True)
st.markdown("<div class='hero-subtitle'>Advanced Multi-Modal Medical Diagnostics</div>", unsafe_allow_html=True)

if not st.session_state.user:
    show_auth_page()
else:
    st.markdown(f"**Welcome to the Patient Portal, `{st.session_state.user['email']}`.** Please navigate the tabs below.")
    st.divider()
    
    is_admin = st.session_state.user.get('role') == 'admin'
    tabs_list = ["🧬 Multi-Cancer Detection", "📝 Symptom Analysis", "📂 Diagnosis History"]
    if is_admin:
        tabs_list.append("🩺 Patient History")
        tabs_list.append("👑 User Management")
        
    tabs = st.tabs(tabs_list)
    
    with tabs[0]:
        show_cancer_detection(res)

    with tabs[1]:
        show_symptom_analysis(res)

    with tabs[2]:
        show_diagnosis_history()

    if is_admin:
        with tabs[3]:
            show_patient_history()

        with tabs[4]:
            show_user_management()