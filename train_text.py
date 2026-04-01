import pandas as pd
import numpy as np
import tensorflow as tf
import pickle
import os
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, LSTM, Dense, Dropout
 
CSV_PATH = r"C:\Users\prann\Downloads\Multi Cancer\clinical_notes_with_symptoms.csv"

if not os.path.exists(CSV_PATH):
    print(f"❌ Error: CSV file not found at {CSV_PATH}")
    print("Please check the path or move the CSV to this folder.")
    exit()

print("⏳ Loading dataset...")
df = pd.read_csv(CSV_PATH)
 
df['text'] = df['symptoms'] + " " + df['clinical_notes']
texts = df['text'].astype(str).values
labels = df['disease'].astype(str).values
 
print("⏳ Encoding labels...")
label_encoder = LabelEncoder()
encoded_labels = label_encoder.fit_transform(labels)
num_classes = len(label_encoder.classes_)
 
with open('label_encoder.pickle', 'wb') as handle:
    pickle.dump(label_encoder, handle, protocol=pickle.HIGHEST_PROTOCOL)
print("✅ Saved label_encoder.pickle")
 
print("⏳ Tokenizing text...")
max_words = 10000
max_len = 200

tokenizer = Tokenizer(num_words=max_words, oov_token="<OOV>")
tokenizer.fit_on_texts(texts)
sequences = tokenizer.texts_to_sequences(texts)
padded_sequences = pad_sequences(sequences, maxlen=max_len, padding='post', truncating='post')
 
with open('tokenizer.pickle', 'wb') as handle:
    pickle.dump(tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)
print("✅ Saved tokenizer.pickle")
 
X_train, X_test, y_train, y_test = train_test_split(padded_sequences, encoded_labels, test_size=0.2, random_state=42)
 
print("🏗️ Building Model...")
model = Sequential([
    Embedding(max_words, 128, input_length=max_len),
    LSTM(64, return_sequences=False),
    Dropout(0.5),
    Dense(64, activation='relu'),
    Dense(num_classes, activation='softmax')
])

model.compile(loss='sparse_categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
 
print("🚀 Starting Training...")
model.fit(X_train, y_train, epochs=10, batch_size=16, validation_split=0.1)
 
loss, accuracy = model.evaluate(X_test, y_test)
print(f"✅ Test Accuracy: {accuracy * 100:.2f}%")
 
model.save("clinical_text_model.keras")
print("🎉 Model saved as 'clinical_text_model.keras'")