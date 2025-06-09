import onnxruntime as ort
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import json
import os
import cv2
import boto3
import logging
import tempfile

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# S3 configuration
MODEL_S3_BUCKET = "team99-bird-detection-models"
VERSION_FILE_KEY = "birdTagging/current_version.txt"

LOCAL_MODEL_PATH = "/tmp/model.onnx"
LOCAL_LABELS_PATH = "/tmp/labels.json"
INPUT_SIZE = 640
CONFIDENCE_THRESHOLD = 0.5
IOU_THRESHOLD = 0.5

s3 = boto3.client("s3")

# Download the version string
version_obj = s3.get_object(Bucket=MODEL_S3_BUCKET, Key=VERSION_FILE_KEY)
version_str = version_obj["Body"].read().decode("utf-8").strip()
logger.info(f"Using model version: {version_str}")

# Construct model paths
model_key = f"birdTagging/models/{version_str}/model.onnx"
labels_key = f"birdTagging/models/{version_str}/labels.json"

# Download if not already in /tmp
if not os.path.exists(LOCAL_MODEL_PATH):
    logger.info(f"Downloading model from S3: {model_key}")
    s3.download_file(MODEL_S3_BUCKET, model_key, LOCAL_MODEL_PATH)
if not os.path.exists(LOCAL_LABELS_PATH):
    logger.info(f"Downloading labels from S3: {labels_key}")
    s3.download_file(MODEL_S3_BUCKET, labels_key, LOCAL_LABELS_PATH)

# Load ONNX session and labels
session_options = ort.SessionOptions()
session_options.enable_mem_pattern = False
session_options.enable_cpu_mem_arena = True
session_options.log_severity_level = 3
session_options.log_verbosity_level = 0

session = ort.InferenceSession(
    LOCAL_MODEL_PATH,
    sess_options=session_options,
    providers=["CPUExecutionProvider"]
)

logger.info("ONNX model loaded successfully.")

with open(LOCAL_LABELS_PATH, "r") as f:
    class_labels = json.load(f)

logger.info(f"Loaded class labels.")

def preprocess(image_path):
    image = Image.open(image_path).convert("RGB")
    orig_w, orig_h = image.size
    image_resized = image.resize((INPUT_SIZE, INPUT_SIZE))
    img = np.array(image_resized).astype(np.float32) / 255.0
    img = np.transpose(img, (2, 0, 1))
    img = np.expand_dims(img, axis=0)
    return img, (orig_w, orig_h)

def postprocess(output, orig_size):
    preds = np.transpose(output[0], (0, 2, 1))[0]
    orig_w, orig_h = orig_size
    results = []

    for det in preds:
        scores = det[4:]
        class_id = int(np.argmax(scores))
        confidence = scores[class_id]

        if confidence > CONFIDENCE_THRESHOLD:
            if class_id >= len(class_labels):
                continue
            xc, yc, w, h = det[:4]
            x1, y1 = xc - w / 2, yc - h / 2
            x2, y2 = xc + w / 2, yc + h / 2

            x1 *= orig_w / INPUT_SIZE
            y1 *= orig_h / INPUT_SIZE
            x2 *= orig_w / INPUT_SIZE
            y2 *= orig_h / INPUT_SIZE

            results.append({
                "class_id": class_id,
                "label": class_labels[class_id],
                "confidence": float(confidence),
                "bbox": [x1, y1, x2, y2]
            })

    return results

def non_max_suppression(detections, iou_thresh=IOU_THRESHOLD):
    boxes = np.array([d["bbox"] for d in detections])
    scores = np.array([d["confidence"] for d in detections])
    indices = []

    if len(boxes) == 0:
        return []

    x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
    areas = (x2 - x1) * (y2 - y1)
    order = scores.argsort()[::-1]

    while order.size > 0:
        i = order[0]
        indices.append(i)

        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])

        inter_w = np.maximum(0.0, xx2 - xx1)
        inter_h = np.maximum(0.0, yy2 - yy1)
        inter_area = inter_w * inter_h
        iou = inter_area / (areas[i] + areas[order[1:]] - inter_area)

        keep = np.where(iou <= iou_thresh)[0]
        order = order[keep + 1]

    return [detections[i] for i in indices]

def run_inference(image_path):
    input_tensor, orig_size = preprocess(image_path)
    input_name = session.get_inputs()[0].name
    output = session.run(None, {input_name: input_tensor})

    raw = postprocess(output, orig_size)
    return non_max_suppression(raw)

def draw_detections(image_path, detections, output_path):
    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except:
        font = ImageFont.load_default()

    for det in detections:
        x1, y1, x2, y2 = det["bbox"]
        label = f"{det['label']} {det['confidence']:.2f}"
        draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
        draw.text((x1, y1 - 10), label, fill="red", font=font)

    image.save(output_path)

def process_video(video_path):
    cap = cv2.VideoCapture(video_path)
    tags = set()

    if not cap.isOpened():
        print("Failed to open video file.")
        return []

    frame_rate = 1  # 1 frame per second
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps * frame_rate) if fps > 0 else 30

    count = 0
    success, frame = cap.read()

    while success:
        if count % frame_interval == 0:
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=True) as tmp_img:
                cv2.imwrite(tmp_img.name, frame)
                detections = run_inference(tmp_img.name)  # existing function
                for d in detections:
                    if "label" in d:
                        tags.add(d["label"].lower())
        success, frame = cap.read()
        count += 1

    cap.release()
    return list(tags)
