import streamlit as st
import numpy as np
from PIL import Image
from tensorflow.keras.preprocessing.image import img_to_array
import appwrite_utils as aw

def predict_cancer(image, res):
    """Predicts cancer type from image using CNN"""
    img = image.resize((128, 128))
    img_array = img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    
    if res['cnn_model']:
        prediction = res['cnn_model'].predict(img_array, verbose=0)
        class_idx = np.argmax(prediction[0])
        confidence = prediction[0][class_idx]
        return res['class_names'][class_idx], confidence
    return "Error", 0.0

def show_cancer_detection(res):
    st.header("🧬 Multi-Cancer Diagnostic Dashboard")
    st.markdown("Upload medical scans for high-precision AI analysis.")
    
    if res['cnn_model'] is None:
        st.warning("⚠️ Cancer model not found. Please run 'train_cancer.py' first.")
        return

    # Use 2 columns for a desktop-friendly dashboard
    main_col, side_col = st.columns([2, 1], gap="large")
    
    with main_col:
        uploaded_files = st.file_uploader("Drop patient scans here (Supports JPG, PNG, JPEG)", 
                                          type=['jpg', 'png', 'jpeg'], 
                                          accept_multiple_files=True,
                                          help="You can upload multiple views of the same patient to increase diagnostic confidence.")

        if uploaded_files:
            st.subheader("🖼️ Scan Gallery")
            cols = st.columns(3)
            predictions = []
            
            for idx, file in enumerate(uploaded_files):
                image = Image.open(file).convert('RGB')
                with cols[idx % 3]: 
                    st.image(image, caption=file.name, use_container_width=True)
                
                pred_class, conf = predict_cancer(image, res)
                predictions.append((pred_class, conf, file))

    with side_col:
        if uploaded_files and predictions:
            # Aggregate Results
            vote_counts = {}
            for pred, conf, f in predictions:
                vote_counts[pred] = vote_counts.get(pred, 0) + 1
            
            final_pred = max(vote_counts, key=vote_counts.get)
            relevant_confs = [conf for pred, conf, f in predictions if pred == final_pred]
            avg_conf = np.mean(relevant_confs)

            st.markdown(f"""
            <div class="card" style="border-top: 4px solid var(--primary);">
                <div style="font-size: 0.85rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700; margin-bottom: 8px;">Analysis Summary</div>
                <h2 style="color: var(--primary); margin-top: 0; font-size: 1.8rem;">{final_pred}</h2>
                <div style="margin: 16px 0;">
                    <span class="badge badge-primary" style="font-size: 1rem; padding: 8px 16px;">
                        Confidence: {avg_conf*100:.1f}%
                    </span>
                </div>
                <p style="font-size: 0.9rem; color: var(--text-muted); line-height: 1.5;">
                    The AI has triangulated its diagnosis across {len(predictions)} scans. 
                    This result is based on deep-learning vision models specializing in oncological morphology.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Auto-save Logic
            save_key = f"saved_{'_'.join([f.name for f in uploaded_files])}"
            if not st.session_state.get(save_key):
                try:
                    uploaded_files[0].seek(0)
                    img_url, _ = aw.upload_medical_scan(st.session_state.user['localId'], uploaded_files[0], uploaded_files[0].name)
                    
                    data = {
                        "type": "Cancer Detection",
                        "diagnosis": final_pred,
                        "confidence": float(avg_conf),
                        "image_url": img_url,
                        "scan_count": len(uploaded_files)
                    }
                    aw.save_diagnosis(st.session_state.user['localId'], data)
                    st.session_state[save_key] = True
                    st.toast("✅ Diagnosis saved to cloud history", icon="💾")
                except Exception as e:
                    st.error(f"Auto-save failed: {e}")
        else:
            st.markdown("""
            <div class="card" style="border-style: dashed; opacity: 0.7; text-align: center; padding: 40px 20px;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🩺</div>
                <div style="color: var(--text-muted); font-weight: 500;">
                    Upload scans to begin the automated diagnostic workflow.
                </div>
            </div>
            """, unsafe_allow_html=True)
