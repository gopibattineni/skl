import os
import cv2
import numpy as np
import PyPDF2
from pdf2image import convert_from_path
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.mobilenet_v3 import preprocess_input
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Load the trained MobileNetV3 model
MODEL_PATH = "my_model.keras"
model = load_model(MODEL_PATH)
print("MobileNetV3 Model loaded successfully!")

# Define class names (update based on your dataset)
classes = ["Actinic keratosis", "Basal cell carcinoma", "Benign keratosis", 
           "Chickenpox", "Cowpox", "Dermatofibroma", "HFMD", "Healthy", 
           "Measles", "Melanocytic nevus", "Melanoma", "Monkeypox", 
           "Squamous cell carcinoma", "Vascular lesion"]

# Function to make predictions on images
def model_predict(img_path, model):
    img = image.load_img(img_path, target_size=(224, 224))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)
    preds = model.predict(x)
    pred_class_index = np.argmax(preds, axis=1)[0]
    pred_score = np.max(preds) * 100
    return pred_class_index, pred_score

# Function to process PDFs and extract images
def extract_images_from_pdf(pdf_path):
    images = convert_from_path(pdf_path)
    image_paths = []
    for i, img in enumerate(images):
        img_path = f"uploads/extracted_page_{i}.jpg"
        img.save(img_path, "JPEG")
        image_paths.append(img_path)
    return image_paths

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def upload():
    if request.method == "POST":
        f = request.files["file"]

        # Ensure uploads directory exists
        basepath = os.path.dirname(__file__)
        upload_folder = os.path.join(basepath, "uploads")
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        # Save the uploaded file
        file_path = os.path.join(upload_folder, secure_filename(f.filename))
        f.save(file_path)
        print(f"File saved at: {file_path}")

        # Check file type
        if f.filename.lower().endswith(".pdf"):
            image_paths = extract_images_from_pdf(file_path)
            if not image_paths:
                return "No images found in the PDF."
            
            results = []
            for img_path in image_paths:
                pred_class_index, pred_score = model_predict(img_path, model)
                results.append(f"Page {image_paths.index(img_path) + 1}: {classes[pred_class_index]} with {pred_score:.2f}% confidence")
            return "<br>".join(results)

        else:
            pred_class_index, pred_score = model_predict(file_path, model)
            result = f'<div class="result-box"> \
            <span class="highlight-text">I am thinking this will be</span> \
            <span class="highlight-prediction">{classes[pred_class_index]}</span> \
            <span class="highlight-text">with confidence of</span> \
            <span class="highlight-prediction">{pred_score:.2f}%</span> \
          </div>'

        return result

if __name__ == "__main__":
    app.run(debug=True)