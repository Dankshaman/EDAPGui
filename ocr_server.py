# ocr_server.py
import uvicorn
from fastapi import FastAPI, File, UploadFile
from paddleocr import PaddleOCR
import numpy as np
import cv2
import logging

# --- Initialization ---
# Load the model into VRAM only ONCE when the server starts up
print("Loading PaddleOCR model into VRAM...")
# Using parameters from the original OCR.py for consistency.
ocr_engine = PaddleOCR(use_angle_cls=False, lang='en', use_gpu=True, show_log=False, use_dilation=True, use_space_char=True)
logging.getLogger('ppocr').setLevel(logging.ERROR)
print("Model loaded successfully!")

# Create the FastAPI application
app = FastAPI()

# --- Health Check Endpoint ---
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# --- API Endpoint ---
@app.post("/ocr")
async def perform_ocr(image: UploadFile = File(...)):
    """Receives an image, performs OCR, and returns the results."""
    # Read the image content from the uploaded file
    contents = await image.read()

    # Convert the image bytes to a numpy array
    np_arr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    # Run the OCR engine
    result = ocr_engine.ocr(img)

    # Return the result as JSON
    return {"filename": image.filename, "result": result}

# --- To run the server ---
# In your terminal, navigate to this file's directory and run:
# uvicorn ocr_server:app --host 0.0.0.0 --port 8000
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
