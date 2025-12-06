import pickle
import pandas as pd
import numpy as np
from tensorflow.keras.models import Sequential, save_model
from tensorflow.keras.layers import Embedding, LSTM, Dense, Dropout
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from sklearn.preprocessing import LabelEncoder

# --- ASSUMING DATA IS LOADED INTO 'texts' and 'labels' variables per your original script ---
# (Load your CSV here)
# df = pd.read_csv("path_to_your_csv.csv")
# ... processing code ...

# 1. Train the Text Model (Same as your code)
tokenizer = Tokenizer(num_words=10000, oov_token="<OOV>")
tokenizer.fit_on_texts(texts)
sequences = tokenizer.texts_to_sequences(texts)
padded_sequences = pad_sequences(sequences, maxlen=200, padding='post', truncating='post')

label_encoder = LabelEncoder()
encoded_labels = label_encoder.fit_transform(labels)
num_classes = len(label_encoder.classes_)

model = Sequential([
    Embedding(10000, 128, input_length=200),
    LSTM(64, return_sequences=False),
    Dropout(0.5),
    Dense(64, activation='relu'),
    Dense(num_classes, activation='softmax')
])
model.compile(loss='sparse_categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
model.fit(padded_sequences, encoded_labels, epochs=10) # Reduced epochs for example

# 2. SAVE EVERYTHING (Crucial Step)
print("Saving artifacts...")

# Save the Keras model
model.save("clinical_text_model.keras")

# Save the Tokenizer (to convert new text to numbers)
with open('tokenizer.pickle', 'wb') as handle:
    pickle.dump(tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)

# Save the Label Encoder (to convert prediction numbers back to Disease Names)
with open('label_encoder.pickle', 'wb') as handle:
    pickle.dump(label_encoder, handle, protocol=pickle.HIGHEST_PROTOCOL)

print("✅ All text model artifacts saved.")