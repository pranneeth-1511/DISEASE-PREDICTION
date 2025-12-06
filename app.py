import streamlit as st
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.preprocessing.sequence import pad_sequences
from PIL import Image
import pytesseract
import pickle
import os

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

st.set_page_config(page_title="MediScan AI", layout="wide", page_icon="🏥")

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
    
    prediction = res['cnn_model'].predict(img_array, verbose=0)
    class_idx = np.argmax(prediction[0])
    confidence = prediction[0][class_idx]
    
    return res['class_names'][class_idx], confidence

def predict_disease_from_text(text_input):
    """Predicts disease from text symptoms using LSTM"""
    max_len = 200 
    sequence = res['tokenizer'].texts_to_sequences([text_input])
    padded = pad_sequences(sequence, maxlen=max_len, padding='post', truncating='post')
    
    pred = res['lstm_model'].predict(padded, verbose=0)
    class_idx = np.argmax(pred)
    disease_name = res['label_encoder'].inverse_transform([class_idx])[0]
    confidence = np.max(pred)
    
    return disease_name, confidence

st.title("🏥 MediScan AI: Multi-Modal Diagnosis")
st.write("Upload medical scans for cancer detection or enter clinical notes for disease prediction.")
tab1, tab2 = st.tabs(["🧬 Multi-Cancer Detection", "📝 Clinical Note & Symptom Analysis"])

with tab1:
    st.header("Upload Patient Scans")
    
    if res['cnn_model'] is None:
        st.warning("⚠️ Cancer model not found. Please run 'train_cancer.py' first.")
    else:
        uploaded_files = st.file_uploader("Upload Scans (Support for multiple images per patient)", 
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
                predictions.append((pred_class, conf))
 
            if predictions:
                vote_counts = {}
                for pred, conf in predictions:
                    vote_counts[pred] = vote_counts.get(pred, 0) + 1
                
                final_prediction = max(vote_counts, key=vote_counts.get)
                 
                relevant_confs = [conf for pred, conf in predictions if pred == final_prediction]
                avg_conf = np.mean(relevant_confs)

                st.success(f"## 🎯 Final Diagnosis: {final_prediction}")
                st.info(f"Confidence: {avg_conf*100:.2f}% (Based on {len(predictions)} scans)")
 
with tab2:
    st.header("Predict Disease from Symptoms/Notes")
    
    if res['lstm_model'] is None:
        st.error("❌ Text model not found. Please run 'train_text.py' to generate the model files.")
    else:
        col1, col2 = st.columns([1, 1])
        
        extracted_text = ""
        
        with col1:
            st.subheader("Option 1: Upload Note Image")
            st.write("Extract text automatically from a prescription or handwritten note.")
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
            st.write("Edit extracted text or type symptoms manually.")
             
            user_input = st.text_area("Clinical Notes / Symptoms", 
                                      value=extracted_text, 
                                      height=250,
                                      placeholder="Example: Patient experiencing severe back pain, chest swelling, and fatigue...")
            
            if st.button("🔍 Predict Disease"):
                if user_input.strip():
                    try:
                        disease, conf = predict_disease_from_text(user_input)
                        st.divider()
                        st.success(f"## 🩺 Predicted Condition: {disease}")
                        st.write(f"**Confidence:** {conf*100:.2f}%")
                    except Exception as e:
                        st.error(f"Prediction Error: {e}")
                else:
                    st.warning("⚠️ Please enter text or upload an image first.")