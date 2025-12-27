from flask import Flask, request, jsonify, render_template, Response
import os
import uuid
import traceback
import numpy as np
import queue
import time

from models.preprocess import preprocess_images
from models.pixel_change import pixel_difference
from models.texture_change import texture_change
from models.geojson_writer import write_change_geojson

app = Flask(__name__)

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# SSE Log Queue
log_queue = queue.Queue()

def log(message):
    print(message)          # VS Code terminal
    log_queue.put(message)  # UI terminal

@app.route("/")
def index():
    return render_template("index.html")

# SSE Log Stream
@app.route("/logs")
def stream_logs():
    def event_stream():
        while True:
            try:
                msg = log_queue.get(timeout=1)
                yield f"data: {msg}\n\n"
                if msg == "__ANALYSIS_DONE__":
                    break
            except queue.Empty:
                yield "data: .\n\n"
                time.sleep(0.5)

    return Response(event_stream(), mimetype="text/event-stream")

# Change Detection
@app.route("/detect-change", methods=["POST"])
def detect_change():
    try:
        log("Request received")

        if "before" not in request.files or "after" not in request.files:
            return jsonify({"error": "Both images are required"}), 400

        uid = str(uuid.uuid4())
        before_path = os.path.join(UPLOAD_DIR, f"{uid}_before.tif")
        after_path = os.path.join(UPLOAD_DIR, f"{uid}_after.tif")

        request.files["before"].save(before_path)
        request.files["after"].save(after_path)
        log("Files saved")

        # Preprocessing
        log("Starting preprocessing...")
        before_img, after_img, meta = preprocess_images(before_path, after_path)
        log("Preprocessing completed")

        # Pixel Change Detection
        log("Running pixel-level change detection...")
        pixel_result = pixel_difference(before_img, after_img)
        pixel_change_mask = pixel_result["change_mask"]
        pixel_changed_pixels = int(np.count_nonzero(pixel_change_mask))
        log(f"Pixel-level change detection complete | Pixels: {pixel_changed_pixels}")

        # Texture Change Detection
        log("Running texture change detection...")
        texture_mask = texture_change(
            before_path,
            after_path,
            pixel_change_mask
        )

        final_change_mask = pixel_change_mask & texture_mask
        texture_confirmed_pixels = int(np.count_nonzero(final_change_mask))
        log(f"Texture change detection complete | Pixels: {texture_confirmed_pixels}")

        # GeoJSON Generation
        log("Generating GeoJSON...")
        geojson_data = write_change_geojson(
            change_mask=final_change_mask,
            pixel_changed_pixels=pixel_changed_pixels,
            texture_confirmed_pixels=texture_confirmed_pixels,
            crs=meta["crs"],
            min_area_pixels=50
        )
        log("GeoJSON generation complete")

        log("Analysis completed")
        log("__ANALYSIS_DONE__")

        return jsonify({
            "status": "success",
            "before_preview": meta["before_preview"],
            "after_preview": meta["after_preview"],
            "stats": {
                "pixel_changed_pixels": pixel_changed_pixels,
                "texture_confirmed_pixels": texture_confirmed_pixels
            },
            "geojson": geojson_data
        })

    except Exception as e:
        log("BACKEND ERROR")
        traceback.print_exc()
        log("__ANALYSIS_DONE__")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
