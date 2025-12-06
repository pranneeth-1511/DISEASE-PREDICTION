import streamlit as st
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.preprocessing.sequence import pad_sequences
from PIL import Image
import pytesseract
import pickle
import os

# --- WINDOWS TESSERACT CONFIGURATION ---
# Keep this if you are on Windows. If on Linux/Mac, you might need to comment it out or change path.
# Default standard path for Windows:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Set page config
st.set_page_config(page_title="MediScan AI", layout="wide", page_icon="🏥")

# --- 1. LOAD RESOURCES (Cached for performance) ---
@st.cache_resource
def load_resources():
    resources = {}
    
    # --- Load Cancer Model (Image) ---
    try:
        resources['cnn_model'] = tf.keras.models.load_model('cancer_type_model.keras')
        # Load class names if they exist, otherwise use default list
        if os.path.exists('class_names.pickle'):
            with open('class_names.pickle', 'rb') as f:
                resources['class_names'] = pickle.load(f)
        else:
            # Fallback if pickle doesn't exist
            resources['class_names'] = ['ALL', 'Brain Cancer', 'Breast Cancer', 'Cervical Cancer', 
                                       'Kidney Cancer', 'Lung and Colon Cancer', 'Lymphoma', 'Oral Cancer']
    except Exception as e:
        st.error(f"❌ Error loading Cancer Model: {e}")
        resources['cnn_model'] = None

    # --- Load Clinical Text Model (Text) ---
    try:
        resources['lstm_model'] = tf.keras.models.load_model('clinical_text_model.keras')
        
        with open('tokenizer.pickle', 'rb') as handle:
            resources['tokenizer'] = pickle.load(handle)
            
        with open('label_encoder.pickle', 'rb') as handle:
            resources['label_encoder'] = pickle.load(handle)
    except Exception as e:
        # It's okay if text model isn't trained yet, app should still run for images
        print(f"Text model not found or error: {e}") 
        resources['lstm_model'] = None

    return resources

# Load all models once
res = load_resources()

# --- 2. PREDICTION FUNCTIONS ---

def predict_cancer(image):
    """Predicts cancer type from image using CNN"""
    # Resize and preprocess matches training (128x128)
    img = image.resize((128, 128))
    img_array = img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    
    prediction = res['cnn_model'].predict(img_array, verbose=0)
    class_idx = np.argmax(prediction[0])
    confidence = prediction[0][class_idx]
    
    return res['class_names'][class_idx], confidence

def predict_disease_from_text(text_input):
    """Predicts disease from text symptoms using LSTM"""
    max_len = 200 # Must match 'train_text.py'
    
    # Tokenize and Pad
    sequence = res['tokenizer'].texts_to_sequences([text_input])
    padded = pad_sequences(sequence, maxlen=max_len, padding='post', truncating='post')
    
    # Predict
    pred = res['lstm_model'].predict(padded, verbose=0)
    class_idx = np.argmax(pred)
    disease_name = res['label_encoder'].inverse_transform([class_idx])[0]
    confidence = np.max(pred)
    
    return disease_name, confidence

# --- 3. FRONTEND UI ---

st.title("🏥 MediScan AI: Multi-Modal Diagnosis")
st.write("Upload medical scans for cancer detection or enter clinical notes for disease prediction.")

# Create Tabs
tab1, tab2 = st.tabs(["🧬 Multi-Cancer Detection", "📝 Clinical Note & Symptom Analysis"])

# === TAB 1: CANCER DETECTION ===
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
            cols = st.columns(3) # Display images in a grid
            
            for idx, file in enumerate(uploaded_files):
                image = Image.open(file).convert('RGB')
                
                # Show image
                with cols[idx % 3]: 
                    st.image(image, caption=file.name, use_column_width=True)
                
                # Predict
                pred_class, conf = predict_cancer(image)
                predictions.append((pred_class, conf))

            # --- VOTING LOGIC ---
            if predictions:
                vote_counts = {}
                for pred, conf in predictions:
                    vote_counts[pred] = vote_counts.get(pred, 0) + 1
                
                final_prediction = max(vote_counts, key=vote_counts.get)
                
                # Calculate average confidence for the winner
                relevant_confs = [conf for pred, conf in predictions if pred == final_prediction]
                avg_conf = np.mean(relevant_confs)

                st.success(f"## 🎯 Final Diagnosis: {final_prediction}")
                st.info(f"Confidence: {avg_conf*100:.2f}% (Based on {len(predictions)} scans)")

# === TAB 2: CLINICAL NOTES (OCR + MANUAL INPUT) ===
with tab2:
    st.header("Predict Disease from Symptoms/Notes")
    
    if res['lstm_model'] is None:
        st.error("❌ Text model not found. Please run 'train_text.py' to generate the model files.")
    else:
        col1, col2 = st.columns([1, 1])
        
        extracted_text = ""
        
        # --- Left Column: OCR Upload ---
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

        # --- Right Column: Text Input & Prediction ---
        with col2:
            st.subheader("Option 2: Review & Predict")
            st.write("Edit extracted text or type symptoms manually.")
            
            # The text area is pre-filled with OCR text if available
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