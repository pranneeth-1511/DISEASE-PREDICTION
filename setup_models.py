import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Conv2D, Flatten, MaxPooling2D, Embedding, LSTM, Input
import pickle
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.preprocessing.text import Tokenizer

print("🔄 Generating placeholder models for frontend testing...")
 
model_cnn = Sequential([
    Input(shape=(128, 128, 3)),
    Conv2D(16, (3,3), activation='relu'),
    MaxPooling2D(2,2),
    Flatten(),
    Dense(8, activation='softmax')  
])
model_cnn.compile(optimizer='adam', loss='categorical_crossentropy')
model_cnn.save("cancer_type_model.keras")
print("✅ Created cancer_type_model.keras")

model_lstm = Sequential([
    Embedding(10000, 128, input_length=200),
    LSTM(64),
    Dense(5, activation='softmax')
])
model_lstm.compile(optimizer='adam', loss='sparse_categorical_crossentropy')
model_lstm.save("clinical_text_model.keras")
print("✅ Created clinical_text_model.keras")
 
tokenizer = Tokenizer(num_words=10000, oov_token="<OOV>")

tokenizer.fit_on_texts(["fever cough headache", "tumor pain swelling"])
with open('tokenizer.pickle', 'wb') as handle:
    pickle.dump(tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)
print("✅ Created tokenizer.pickle")

label_encoder = LabelEncoder()
label_encoder.fit(["Flu", "Covid", "Pneumonia", "Bronchitis", "Healthy"]) # Dummy labels
with open('label_encoder.pickle', 'wb') as handle:
    pickle.dump(label_encoder, handle, protocol=pickle.HIGHEST_PROTOCOL)
print("✅ Created label_encoder.pickle")

print("\n🎉 All files created! You can now run 'streamlit run app.py'")