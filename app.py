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

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

st.set_page_config(page_title="MediScan AI", layout="wide", page_icon="🏥")

# --- Custom CSS Injection ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    /* Global Styles */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        font-family: 'Inter', sans-serif;
    }
    
    /* Hero Title */
    .hero-title {
        font-weight: 800;
        font-size: 3rem;
        text-align: center;
        background: -webkit-linear-gradient(45deg, #0068C9, #00A699);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
        padding-bottom: 4px;
    }
    .hero-subtitle {
        text-align: center;
        color: #6C757D;
        font-size: 1.2rem;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    
    /* Cards */
    .card {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border: 1px solid #E9ECEF;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        margin-bottom: 1rem;
    }
    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.08);
    }
    .card h2, .card h3 {
        margin-top: 0;
        color: #212529;
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Button Polish */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        transform: scale(1.02);
    }
    
    /* Status Badge */
    .badge {
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-primary { background: #E7F1FF; color: #0068C9; }
</style>
""", unsafe_allow_html=True)

# --- Session State Management ---
if 'user' not in st.session_state:
    st.session_state.user = None

# --- Firebase Auth UI ---
def auth_sidebar():
    st.sidebar.title("👤 Patient Portal")
    if st.session_state.user:
        role_label = "👑 ADMIN" if st.session_state.user.get('role') == 'admin' else "USER"
        st.sidebar.success(f"Logged in as: {st.session_state.user['email']} ({role_label})")
        if st.sidebar.button("Logout"):
            st.session_state.user = None
            st.rerun()

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

def predict_cancer(image):
    """Predicts cancer type from image using CNN"""
    img = image.resize((128, 128))
    img_array = img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    
    # Check if model exists
    if res['cnn_model']:
        prediction = res['cnn_model'].predict(img_array, verbose=0)
        class_idx = np.argmax(prediction[0])
        confidence = prediction[0][class_idx]
        return res['class_names'][class_idx], confidence
    return "Error", 0.0

def predict_disease_from_text(text_input):
    """Predicts disease from text symptoms using LSTM"""
    max_len = 200 
    sequence = res['tokenizer'].texts_to_sequences([text_input])
    padded = pad_sequences(sequence, maxlen=max_len, padding='post', truncating='post')
    
    if res['lstm_model']:
        pred = res['lstm_model'].predict(padded, verbose=0)
        class_idx = np.argmax(pred)
        disease_name = res['label_encoder'].inverse_transform([class_idx])[0]
        confidence = np.max(pred)
        return disease_name, confidence
    return "Error", 0.0

st.markdown("<h1 class='hero-title'>🏥 MediScan AI</h1>", unsafe_allow_html=True)
st.markdown("<div class='hero-subtitle'>Advanced Multi-Modal Medical Diagnostics</div>", unsafe_allow_html=True)

if not st.session_state.user:
    st.markdown('<div style="text-align: center; margin-bottom: 2rem; color: #6C757D;">Please Login or Sign Up to securely access your diagnostic tools.</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        choice = st.radio("Access Portal", ["Login", "Sign Up"], horizontal=True, label_visibility="hidden")
        email = st.text_input("Email", placeholder="admin@mediscan.ai")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        
        st.write("") # Spacing
        if choice == "Login":
            if st.button("Secure Login", use_container_width=True):
                res = aw.sign_in_with_email(email, password)
                if 'idToken' in res:
                    st.session_state.user = res
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        else:
            if st.button("Create Account", use_container_width=True):
                res = aw.sign_up_with_email(email, password)
                if 'idToken' in res:
                    st.success("Account created successfully! Please select Login.")
                else:
                    st.error(res.get('error', {}).get('message', 'Signup failed'))
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.markdown(f"**Welcome to the Patient Portal, `{st.session_state.user['email']}`.** Please navigate the tabs below.")
    st.divider()
    
    is_admin = st.session_state.user.get('role') == 'admin'
    tabs_list = ["🧬 Multi-Cancer Detection", "📝 Symptom Analysis", "📂 Diagnosis History"]
    if is_admin:
        tabs_list.append("🩺 Patient History")
        tabs_list.append("👑 User Management")
        
    tabs = st.tabs(tabs_list)
    tab1, tab2, tab3 = tabs[0], tabs[1], tabs[2]

    with tab1:
        st.header("Upload Patient Scans")
        
        if res['cnn_model'] is None:
            st.warning("⚠️ Cancer model not found. Please run 'train_cancer.py' first.")
        else:
            uploaded_files = st.file_uploader("Upload Scans (Support for multiple images)", 
                                              type=['jpg', 'png', 'jpeg'], 
                                              accept_multiple_files=True)

            if uploaded_files:
                st.divider()
                predictions = []
                cols = st.columns(3)
                
                for idx, file in enumerate(uploaded_files):
                    image = Image.open(file).convert('RGB')
                    with cols[idx % 3]: 
                        st.image(image, caption=file.name, use_container_width=True)
                    
                    pred_class, conf = predict_cancer(image)
                    predictions.append((pred_class, conf, file))

                if predictions:
                    vote_counts = {}
                    for pred, conf, f in predictions:
                        vote_counts[pred] = vote_counts.get(pred, 0) + 1
                    
                    final_prediction = max(vote_counts, key=vote_counts.get)
                    relevant_confs = [conf for pred, conf, f in predictions if pred == final_prediction]
                    avg_conf = np.mean(relevant_confs)

                    st.markdown(f"""
                    <div class="card">
                        <div style="font-size: 0.9rem; color: #6C757D; text-transform: uppercase; font-weight: bold;">AI Diagnosis Result</div>
                        <h2 style="color: #0068C9; margin-top: 8px;">🎯 {final_prediction}</h2>
                        <div style="font-size: 1.1rem; color: #212529;">
                            <strong>Confidence Score:</strong> <span class="badge badge-primary">{avg_conf*100:.2f}%</span>
                        </div>
                        <p style="font-size: 0.9rem; color: #868E96; margin-top: 8px;">Analyzed across {len(predictions)} scans to ensure accuracy.</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    save_key = f"saved_{'_'.join([f.name for f in uploaded_files])}"
                    if not st.session_state.get(save_key):
                        with st.spinner("💾 Saving detection results automatically..."):
                            try:
                                # Upload first image as reference
                                uploaded_files[0].seek(0)
                                img_url, _ = aw.upload_medical_scan(st.session_state.user['localId'], uploaded_files[0], uploaded_files[0].name)
                                
                                data = {
                                    "type": "Cancer Detection",
                                    "diagnosis": final_prediction,
                                    "confidence": float(avg_conf),
                                    "image_url": img_url,
                                    "scan_count": len(uploaded_files)
                                }
                                aw.save_diagnosis(st.session_state.user['localId'], data)
                                st.session_state[save_key] = True
                                st.success("✅ Diagnosis saved automatically to history!")
                            except Exception as e:
                                st.error(f"Failed to auto-save: {e}")

    with tab2:
        st.header("Predict Disease from Symptoms/Notes")
        
        if res['lstm_model'] is None:
            st.error("❌ Text model not found. Please run 'train_text.py' to generate the model files.")
        else:
            col1, col2 = st.columns([1, 1])
            extracted_text = ""
            
            with col1:
                st.subheader("Option 1: Upload Note Image")
                note_image = st.file_uploader("Upload Image", type=['jpg', 'png', 'jpeg'], key="note_uploader")
                
                if note_image:
                    try:
                        with st.spinner("🔍 Extracting text..."):
                            img_ocr = Image.open(note_image)
                            st.image(img_ocr, caption="Uploaded Note", use_container_width=True)
                            extracted_text = pytesseract.image_to_string(img_ocr)
                            st.success("Text extracted successfully!")
                    except Exception as e:
                        st.error(f"OCR Failed: {e}. (Ensure Tesseract is installed)")

            with col2:
                st.subheader("Option 2: Review & Predict")
                user_input = st.text_area("Clinical Notes / Symptoms", 
                                          value=extracted_text, 
                                          height=250,
                                          placeholder="Example: Patient experiencing severe back pain...")
                
                if st.button("🔍 Predict Disease"):
                    if user_input.strip():
                        try:
                            disease, conf = predict_disease_from_text(user_input)
                            st.divider()
                            st.markdown(f"""
                            <div class="card">
                                <div style="font-size: 0.9rem; color: #6C757D; text-transform: uppercase; font-weight: bold;">NLP Analysis Result</div>
                                <h2 style="color: #00A699; margin-top: 8px;">🩺 {disease}</h2>
                                <div style="font-size: 1.1rem; color: #212529;">
                                    <strong>Confidence Score:</strong> <span class="badge badge-primary">{conf*100:.2f}%</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Cache prediction for saving
                            st.session_state.last_text_pred = {
                                "diagnosis": disease,
                                "confidence": float(conf),
                                "notes": user_input
                            }
                        except Exception as e:
                            st.error(f"Prediction Error: {e}")
                    else:
                        st.warning("⚠️ Please enter text or upload an image first.")
                
                if 'last_text_pred' in st.session_state:
                    if st.button("💾 Save to History", key="save_text"):
                        try:
                            with st.spinner("Saving to cloud..."):
                                data = st.session_state.last_text_pred
                                data['type'] = "Symptom Analysis"
                                
                                if note_image:
                                    note_image.seek(0)
                                    img_url, _ = aw.upload_medical_scan(st.session_state.user['localId'], note_image, note_image.name)
                                    data['image_url'] = img_url

                                aw.save_diagnosis(st.session_state.user['localId'], data)
                                st.success("✅ Saved to history!")
                                del st.session_state.last_text_pred
                        except Exception as e:
                            st.error(f"Save failed: {e}")

    with tab3:
        st.header("Your Diagnosis History")
        if st.button("🔄 Refresh History"):
            st.cache_data.clear()
        
        with st.spinner("Fetching your records..."):
            try:
                history = aw.get_diagnosis_history(st.session_state.user['localId'])
                
                if not history:
                    st.info("No records found yet. Perform a diagnosis to see it here.")
                else:
                    for entry in history:
                        card_html = f"""
                        <div class="card" style="margin-bottom: 20px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                                <span style="font-weight: 600; color: #495057;">📅 {entry['timestamp'].strftime('%Y-%m-%d %H:%M')}</span>
                                <span class="badge badge-primary">{entry['type']}</span>
                            </div>
                            <h3 style="color: #0068C9; margin-top: 0; margin-bottom: 10px;">{entry['diagnosis']}</h3>
                            <div style="color: #495057;">
                                <strong>Confidence:</strong> <span style="color: #212529; font-weight: bold;">{entry['confidence']*100:.2f}%</span>
                            </div>
                        """
                        if 'notes' in entry:
                            card_html += f'<div style="margin-top: 10px; padding: 10px; background-color: #F8F9FA; border-radius: 8px; font-size: 0.9rem;"><strong>Notes:</strong> {entry["notes"]}</div>'
                        if 'scan_count' in entry:
                            card_html += f'<div style="margin-top: 10px; font-size: 0.9rem;"><strong>Scans Analyzed:</strong> {entry["scan_count"]}</div>'
                        
                        card_html += f'<div style="margin-top: 15px; font-size: 0.8rem; color: #CED4DA;">ID: {entry.get("id", "N/A")}</div></div>'
                        
                        if 'image_url' in entry:
                            col_a, col_b = st.columns([1, 2])
                            with col_a:
                                st.image(entry['image_url'], use_container_width=True, caption="Reference Scan")
                            with col_b:
                                st.markdown(card_html, unsafe_allow_html=True)
                        else:
                            st.markdown(card_html, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error fetching history: {e}")

    if is_admin:
        with tabs[3]:
            st.header("🩺 Patient History")
            all_users = aw.get_all_users()
            user_options = {f"{u['email']} (ID: {u['userid']})": u['userid'] for u in all_users if u.get('role', 'user') == 'user'}
            
            selected_user_label = st.selectbox("Select Patient to View", list(user_options.keys()))
            if selected_user_label:
                selected_userid = user_options[selected_user_label]
                st.divider()
                st.subheader(f"Records for {selected_user_label.split(' ')[0]}")
                
                with st.spinner("Fetching patient records..."):
                    try:
                        p_history = aw.get_diagnosis_history(selected_userid)
                        if not p_history:
                            st.info("No records found for this patient.")
                        else:
                            for entry in p_history:
                                card_html = f"""
                                <div class="card" style="margin-bottom: 20px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                                        <span style="font-weight: 600; color: #495057;">📅 {entry['timestamp'].strftime('%Y-%m-%d %H:%M')}</span>
                                        <span class="badge badge-primary">{entry['type']}</span>
                                    </div>
                                    <h3 style="color: #0068C9; margin-top: 0; margin-bottom: 10px;">{entry['diagnosis']}</h3>
                                    <div style="color: #495057;">
                                        <strong>Confidence:</strong> <span style="color: #212529; font-weight: bold;">{entry['confidence']*100:.2f}%</span>
                                    </div>
                                """
                                if 'notes' in entry:
                                    card_html += f'<div style="margin-top: 10px; padding: 10px; background-color: #F8F9FA; border-radius: 8px; font-size: 0.9rem;"><strong>Notes:</strong> {entry["notes"]}</div>'
                                if 'scan_count' in entry:
                                    card_html += f'<div style="margin-top: 10px; font-size: 0.9rem;"><strong>Scans Analyzed:</strong> {entry["scan_count"]}</div>'
                                card_html += f'<div style="margin-top: 15px; font-size: 0.8rem; color: #CED4DA;">ID: {entry.get("id", "N/A")}</div></div>'
                                
                                if 'image_url' in entry:
                                    col_a, col_b = st.columns([1, 2])
                                    with col_a:
                                        st.image(entry['image_url'], use_container_width=True, caption="Reference Scan")
                                    with col_b:
                                        st.markdown(card_html, unsafe_allow_html=True)
                                        if st.button("🗑️ Delete Record", key=f"del_{entry['id']}", type="primary"):
                                            aw.delete_diagnosis(entry['id'])
                                            st.rerun()
                                else:
                                    st.markdown(card_html, unsafe_allow_html=True)
                                    if st.button("🗑️ Delete Record", key=f"del_noimg_{entry['id']}", type="primary"):
                                        aw.delete_diagnosis(entry['id'])
                                        st.rerun()
                    except Exception as e:
                        st.error(f"Error fetching history: {e}")

        with tabs[4]:
            st.header("👥 Manage Users")
            st.markdown("Change roles below. Only admins can see this tab.")
            st.divider()
            
            users = aw.get_all_users()
            for u in users:
                c1, c2, c3 = st.columns([3, 1.5, 1])
                with c1:
                    st.write(f"**{u['email']}**  \n`ID: {u['userid']}`")
                with c2:
                    current_role = u.get('role', 'user')
                    new_role = st.selectbox("Role", ["user", "admin"], index=0 if current_role == 'user' else 1, key=f"role_{u['id']}", label_visibility="collapsed")
                with c3:
                    if new_role != current_role:
                        if st.button("Update", key=f"btn_{u['id']}", use_container_width=True):
                            aw.update_user_role(u['id'], new_role)
                            st.success("Updated!")
                st.divider()