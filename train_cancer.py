import os
import random
import pickle
import numpy as np
from PIL import Image
from tqdm import tqdm
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator, load_img, img_to_array
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Input, Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping
 
original_dir = r"C:\Users\prann\Downloads\Multi Cancer\Multi Cancer" 
reduced_dir = r"C:\Users\prann\Downloads\Multi Cancer\Multi Cancer\Multi Cancer_Reduced"

os.makedirs(reduced_dir, exist_ok=True)

target_size = (128, 128)
max_images_per_class = 1000 

print(f"\n🔄 Reducing and cleaning dataset from: {original_dir}")
print(f"   Saving to: {reduced_dir}")
 
if not os.path.exists(original_dir):
    raise FileNotFoundError(f"❌ The directory {original_dir} does not exist. Please check the path.")
 
for subtype in os.listdir(original_dir):
    subtype_path = os.path.join(original_dir, subtype)
     
    if not os.path.isdir(subtype_path):
        continue

    save_path = os.path.join(reduced_dir, subtype)
    os.makedirs(save_path, exist_ok=True)
 
    valid_images = []
    for root, dirs, files in os.walk(subtype_path):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                valid_images.append(os.path.join(root, file))
 
    if not valid_images:
        print(f"⚠️  Warning: No images found in {subtype} (checked subfolders too)")
        continue

    random.shuffle(valid_images)
     
    selected_images = valid_images[:max_images_per_class]
 
    for img_path in tqdm(selected_images, desc=f"Processing {subtype}"):
        try:
            
            if os.path.getsize(img_path) == 0:
                continue
            
            filename = os.path.basename(img_path)
            
            if os.path.exists(os.path.join(save_path, filename)):
                filename = f"{random.randint(1000,9999)}_{filename}"

            with Image.open(img_path).convert("RGB") as img:
                img = img.resize(target_size, Image.LANCZOS)
                
                img.save(os.path.join(save_path, filename), "JPEG", quality=90, optimize=True)

        except Exception as e:
            print(f"Skipped {img_path}: {e}")

print("✅ Dataset reduced and cleaned at:", reduced_dir)

dataset_dir = reduced_dir
img_height, img_width = 128, 128
batch_size = 64
epochs = 20
 
total_files_processed = sum([len(files) for r, d, files in os.walk(dataset_dir)])
if total_files_processed == 0:
    print("\n❌ CRITICAL ERROR: No images were found or processed.")
    print(f"   Please check the folder structure in: {original_dir}")
    print("   Make sure the folders inside contain actual .jpg or .png files.")
    exit()
 

datagen = ImageDataGenerator(
    rescale=1. / 255,
    validation_split=0.2
)

print("\n⏳ Loading Training Data...")
train_gen = datagen.flow_from_directory(
    dataset_dir,
    target_size=(img_height, img_width),
    batch_size=batch_size,
    class_mode="categorical",
    subset="training",
    shuffle=True
)

print("⏳ Loading Validation Data...")
val_gen = datagen.flow_from_directory(
    dataset_dir,
    target_size=(img_height, img_width),
    batch_size=batch_size,
    class_mode="categorical",
    subset="validation",
    shuffle=True
)
 
class_indices = train_gen.class_indices
class_names = list(class_indices.keys())
print("\n📌 Classes found:", class_names)

with open('class_names.pickle', 'wb') as f:
    pickle.dump(class_names, f)
print("✅ Saved class_names.pickle (Required for Frontend)")

 

model = Sequential([
    Input(shape=(img_height, img_width, 3)),
    
    Conv2D(16, (3, 3), activation="relu"),
    MaxPooling2D(2, 2),

    Conv2D(32, (3, 3), activation="relu"),
    MaxPooling2D(2, 2),

    Conv2D(64, (3, 3), activation="relu"),
    MaxPooling2D(2, 2),

    Flatten(),
    Dense(128, activation="relu"),
    Dropout(0.5),
    Dense(len(class_names), activation="softmax")
])

model.compile(
    optimizer=Adam(learning_rate=0.0005),
    loss="categorical_crossentropy",
    metrics=["accuracy"]
)

 

steps_per_epoch = train_gen.samples // batch_size
validation_steps = val_gen.samples // batch_size

if validation_steps == 0:
    validation_steps = 1

early_stop = EarlyStopping(
    monitor="val_loss",
    patience=3,
    restore_best_weights=True,
    verbose=1
)

print("\n🚀 Starting Training...")
history = model.fit(
    train_gen,
    validation_data=val_gen,
    epochs=epochs,
    steps_per_epoch=steps_per_epoch,
    validation_steps=validation_steps,
    callbacks=[early_stop]
)

model.save("cancer_type_model.keras")
print("\n🎉 SUCCESS! Model saved as 'cancer_type_model.keras'")
print("You can now run 'streamlit run app.py' to use the frontend.")