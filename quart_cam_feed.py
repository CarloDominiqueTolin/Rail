import cv2
import asyncio
from datetime import datetime
from quart import Quart, Response, jsonify
import os
from yolov5.segment.segment_cracks import inference
import re

app = Quart(__name__)

# Initialize webcam (0 is the default camera, adjust if needed)
camera = cv2.VideoCapture(0)

async def generate_frames():
    """Generator to yield frames from the camera."""
    while True:
        success, frame = camera.read()
        if not success:
            break

        #frame, detections = inference(frame)
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        await asyncio.sleep(0.01) 

@app.route('/video_feed')
async def video_feed():
    """Route for streaming the feed."""
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
async def index():
    """Live Feed"""
    return (
        '<html><head><title>Live Camera Feed</title></head>'
        '<body><h1>Live Webcam Feed</h1>'
        '<img src="/video_feed" width="640" height="480"/>'
        '<form action="/capture" method="post">'
        '<button type="submit">Capture Image</button>'
        '</form>'
        '</body></html>'
    )

@app.route('/capture', methods=['POST'])
async def capture():
    """API to capture a single frame and save it to an image file."""
    success, frame = camera.read()  # Capture a single frame
    if not success:
        return jsonify({"error": "Failed to capture image"}), 500

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"capture_{timestamp}.jpg"
    filename = os.path.join('assets/db/',filename)

    frame, detections = inference(frame)
    cv2.imwrite(filename, frame)

    timestamp = timestamp.split('_')[0]+" "+timestamp.split('_')[1]
    matches = re.findall(r"(\d+)\s+([a-zA-Z]+)", detections)
    detections = {desc: int(num) for num, desc in matches}

    return jsonify({"timestamp": timestamp, "filename": filename, 'detections':detections})


if __name__ == '__main__':
    app.run(debug=True)
