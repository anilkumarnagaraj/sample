import re
import json
from typing import Optional, Dict, List
from dateutil import parser
from datetime import timezone
from transformers import pipeline
from flask import Flask, request, jsonify

app = Flask(__name__)

# Initialize zero-shot classifier once
zero_shot_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

def normalize_timestamp(ts_str: str) -> str:
    try:
        dt = parser.parse(ts_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return ts_str

def infer_tags(message: str, component: str, level: str) -> List[str]:
    tags = []
    if level:
        tags.append(f"level.{level}")
    if component:
        comp_tag = component.lower().replace(" ", "_")
        tags.append(f"component.{comp_tag}")

    keywords = {
        "timeout": "error.timeout",
        "failed": "error.failed",
        "connection": "error.connection",
        "notfound": "error.not_found",
        "not found": "error.not_found",
        "exception": "error.exception",
        "error": "error.generic",
        "panic": "error.panic",
        "refused": "error.connection_refused",
        "unauthorized": "error.unauthorized",
        "forbidden": "error.forbidden",
        "denied": "error.denied"
    }
    message_lower = message.lower()
    for k, tag in keywords.items():
        if k in message_lower:
            tags.append(tag)
    return list(set(tags))

def predict_component_with_llm(text: str) -> str:
    candidate_labels = ["microservice", "kubernetes", "prometheus", "unknown"]
    try:
        result = zero_shot_classifier(text, candidate_labels)
        for label, score in zip(result['labels'], result['scores']):
            if label != 'unknown' and score > 0.4:
                return label
        return "unknown"
    except Exception as e:
        print(f"[LLM ERROR] {e}")
        return "unknown"

def detect_source_type_and_component(line: str, component: Optional[str]) -> (str, str):
    if component and component.lower() != "unknown":
        return component, component.lower()
    predicted = predict_component_with_llm(line)
    return predicted, predicted

def parse_json_log(line: str) -> Optional[Dict]:
    try:
        obj = json.loads(line)
        level = obj.get("level", "").lower()
        if level != "error":
            return None
        timestamp_raw = obj.get("utc_date", "") or obj.get("timestamp", "")
        timestamp = normalize_timestamp(timestamp_raw)
        message = obj.get("msg", "") or obj.get("message", "")
        component = obj.get("component", "") or "unknown"

        component_pred, source_type = detect_source_type_and_component(line, component)

        return {
            "timestamp": timestamp,
            "log": message,
            "label": "Error",
            "source": component_pred,
            "tags": infer_tags(message, component_pred, level),
            "source_type": source_type
        }
    except json.JSONDecodeError:
        return None

def parse_plain_log(line: str) -> Optional[Dict]:
    regex = r"^(?P<timestamp>\S+) (?P<level>INFO|WARN|WARNING|ERROR) \[(?P<component>[^\]]+)] (?P<message>.+)$"
    m = re.match(regex, line)
    if m:
        level = m.group("level").lower()
        if level != "error":
            return None
        timestamp = normalize_timestamp(m.group("timestamp"))
        message = m.group("message")
        component = m.group("component") or "unknown"

        component_pred, source_type = detect_source_type_and_component(line, component)

        return {
            "timestamp": timestamp,
            "log": message,
            "label": "Error",
            "source": component_pred,
            "tags": infer_tags(message, component_pred, level),
            "source_type": source_type
        }
    return None

def parse_gin_log(line: str) -> Optional[Dict]:
    if line.startswith("[GIN]"):
        parts = line.split("|")
        if len(parts) >= 3:
            status_code = parts[1].strip()
            try:
                code = int(status_code)
                if code < 400:
                    return None
            except:
                return None
            time_match = re.search(r"\[GIN\]\s(\d{4}/\d{2}/\d{2}\s-\s\d{2}:\d{2}:\d{2})", line)
            timestamp_raw = time_match.group(1).replace(" - ", "T") if time_match else ""
            timestamp = normalize_timestamp(timestamp_raw + "Z") if timestamp_raw else ""
            component = "GIN"

            component_pred, source_type = detect_source_type_and_component(line, component)

            return {
                "timestamp": timestamp,
                "log": line.strip(),
                "label": "Error" if code >= 500 else "Warning",
                "source": component_pred,
                "tags": infer_tags(line, component_pred, "error" if code >= 500 else "warning"),
                "source_type": source_type
            }
    return None

def process_log_line(line: str) -> Optional[Dict]:
    for parser_func in [parse_json_log, parse_plain_log, parse_gin_log]:
        result = parser_func(line)
        if result:
            return result
    return None

@app.route("/classify", methods=["POST"])
def classify_logs():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    output = []
    for line in file.stream:
        line = line.decode("utf-8").strip()
        parsed = process_log_line(line)
        if parsed:
            output.append(parsed)

    return jsonify(output), 200

@app.route('/')
def home():
    return "Hello from the Auto-heal! Hit /classify to check/heal the system."

def trigger_test():
    print("Welcome to Auto-Heal Application!!!!")


if __name__ == '__main__':
    threading.Thread(target=trigger_test).start()
    app.run(host='0.0.0.0', port=8080)
