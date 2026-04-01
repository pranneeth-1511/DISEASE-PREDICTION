import streamlit as st
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.preprocessing.sequence import pad_sequences
from PIL import Image
import pytesseract
import pickle
import os
import firebase_utils as fb
from io import BytesIO

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

st.set_page_config(page_title="MediScan AI", layout="wide", page_icon="🏥")

# --- Session State Management ---
if 'user' not in st.session_state:
    st.session_state.user = None

# --- Firebase Auth UI ---
def auth_ui():
    st.sidebar.title("👤 Patient Portal")
    
    if st.session_state.user:
        st.sidebar.success(f"Logged in as: {st.session_state.user['email']}")
        if st.sidebar.button("Logout"):
            st.session_state.user = None
            st.rerun()
    else:
        choice = st.sidebar.selectbox("Login/Signup", ["Login", "Sign Up"])
        email = st.sidebar.text_input("Email")
        password = st.sidebar.text_input("Password", type="password")
        
        if choice == "Login":
            if st.sidebar.button("Login"):
                res = fb.sign_in_with_email(email, password)
                if 'idToken' in res:
                    st.session_state.user = res
                    st.rerun()
                else:
                    st.sidebar.error("Invalid credentials")
        else:
            if st.sidebar.button("Sign Up"):
                res = fb.sign_up_with_email(email, password)
                if 'idToken' in res:
                    st.sidebar.success("Account created! Please login.")
                else:
                    st.sidebar.error(res.get('error', {}).get('message', 'Signup failed'))

auth_ui()

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

st.title("🏥 MediScan AI: Multi-Modal Diagnosis")

if not st.session_state.user:
    st.info("Please Login or Sign Up from the sidebar to access the AI Diagnostic tools.")
    st.image("https://img.freepik.com/free-vector/medical-technology-concept_23-2148403362.jpg", use_column_width=True)
else:
    st.write(f"Welcome, {st.session_state.user['email']}. Upload scans for analysis.")
    
    tabs = ["🧬 Multi-Cancer Detection", "📝 Symptom Analysis", "📂 Diagnosis History"]
    tab1, tab2, tab3 = st.tabs(tabs)

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
                        st.image(image, caption=file.name, use_column_width=True)
                    
                    pred_class, conf = predict_cancer(image)
                    predictions.append((pred_class, conf, file))

                if predictions:
                    vote_counts = {}
                    for pred, conf, f in predictions:
                        vote_counts[pred] = vote_counts.get(pred, 0) + 1
                    
                    final_prediction = max(vote_counts, key=vote_counts.get)
                    relevant_confs = [conf for pred, conf, f in predictions if pred == final_prediction]
                    avg_conf = np.mean(relevant_confs)

                    st.success(f"## 🎯 Final Diagnosis: {final_prediction}")
                    st.info(f"Confidence: {avg_conf*100:.2f}% (Based on {len(predictions)} scans)")
                    
                    if st.button("💾 Save Results to Cloud", key="save_cancer"):
                        with st.spinner("Saving to cloud..."):
                            try:
                                # Upload first image as reference
                                img_url, _ = fb.upload_medical_scan(st.session_state.user['localId'], uploaded_files[0], uploaded_files[0].name)
                                
                                data = {
                                    "type": "Cancer Detection",
                                    "diagnosis": final_prediction,
                                    "confidence": float(avg_conf),
                                    "image_url": img_url,
                                    "scan_count": len(uploaded_files)
                                }
                                fb.save_diagnosis(st.session_state.user['localId'], data)
                                st.success("✅ Diagnosis saved to your history!")
                            except Exception as e:
                                st.error(f"Failed to save: {e}")

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
                            st.image(img_ocr, caption="Uploaded Note", use_column_width=True)
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
                            st.success(f"## 🩺 Predicted Condition: {disease}")
                            st.write(f"**Confidence:** {conf*100:.2f}%")
                            
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
                            data = st.session_state.last_text_pred
                            data['type'] = "Symptom Analysis"
                            fb.save_diagnosis(st.session_state.user['localId'], data)
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
                history = fb.get_diagnosis_history(st.session_state.user['localId'])
                
                if not history:
                    st.info("No records found yet. Perform a diagnosis to see it here.")
                else:
                    for entry in history:
                        with st.expander(f"📅 {entry['timestamp'].strftime('%Y-%m-%d %H:%M')} | {entry['type']} - {entry['diagnosis']}"):
                            col_a, col_b = st.columns([1, 2])
                            with col_a:
                                if 'image_url' in entry:
                                    st.image(entry['image_url'], use_column_width=True)
                                else:
                                    st.info("No image associated.")
                            with col_b:
                                st.write(f"**Diagnosis:** {entry['diagnosis']}")
                                st.write(f"**Confidence:** {entry['confidence']*100:.2f}%")
                                if 'notes' in entry:
                                    st.write(f"**Notes:** {entry['notes']}")
                                if 'scan_count' in entry:
                                    st.write(f"**Scans Analyzed:** {entry['scan_count']}")
                                st.caption(f"ID: {entry['id']}")
            except Exception as e:
                st.error(f"Error fetching history: {e}")