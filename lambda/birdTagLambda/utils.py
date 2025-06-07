import onnxruntime as ort
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import json
import os
import cv2

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.onnx")
LABELS_PATH = os.path.join(os.path.dirname(__file__), "labels.json")
INPUT_SIZE = 640
CONFIDENCE_THRESHOLD = 0.5
IOU_THRESHOLD = 0.5

session_options = ort.SessionOptions()
session_options.enable_mem_pattern = False
session_options.enable_cpu_mem_arena = True
session_options.log_severity_level = 3
session_options.log_verbosity_level = 0

session = ort.InferenceSession(
    MODEL_PATH,
    sess_options=session_options,
    providers=["CPUExecutionProvider"]
)

with open(LABELS_PATH, "r") as f:
    class_labels = json.load(f)

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

def process_video(video_path, output_path):
    cap = cv2.VideoCapture(video_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
    bird_types_found = set()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        tmp_path = "/tmp/frame.jpg"
        pil_image.save(tmp_path)
        detections = run_inference(tmp_path)
        bird_types_found.update(d["label"] for d in detections)

        draw_detections(tmp_path, detections, tmp_path)
        annotated = Image.open(tmp_path)
        annotated_frame = cv2.cvtColor(np.array(annotated), cv2.COLOR_RGB2BGR)
        out.write(annotated_frame)

    cap.release()
    out.release()

    return [{"label": label} for label in bird_types_found]
