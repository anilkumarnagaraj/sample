import re
import json
from typing import Optional, Dict, List
from dateutil import parser
from datetime import timezone
from flask import Flask, request, jsonify

app = Flask(__name__)

# Component detection patterns
COMPONENT_PATTERNS = {
    "microservice": [r"service", r"ms-", r"microservice", r"api"],
    "kubernetes": [r"k8s", r"kubernetes", r"pod", r"node", r"container", r"kubelet"],
    "prometheus": [r"prometheus", r"metric", r"grafana", r"alertmanager", r"node_exporter"],
    "http": [r"http", r"status", r"response"],
    "database": [r"db", r"database", r"cloudant", r"document"],
    "payment": [r"payment", r"gateway"]
}

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
        tags.append(f"level.{level.lower()}")
    if component:
        comp_tag = component.lower().replace(" ", "_")
        tags.append(f"component.{comp_tag}")

    keywords = {
        r"timeout": "error.timeout",
        r"failed": "error.failed",
        r"connection": "error.connection",
        r"notfound": "error.not_found",
        r"not found": "error.not_found",
        r"exception": "error.exception",
        r"error": "error.generic",
        r"panic": "error.panic",
        r"refused": "error.connection_refused",
        r"unauthorized": "error.unauthorized",
        r"forbidden": "error.forbidden",
        r"denied": "error.denied",
        r"429": "error.rate_limit",
        r"5\d{2}": "error.server",
        r"4\d{2}": "error.client",
        r"deleted": "error.not_found",
        r"back[-\s]?off": "error.retry",
        r"crashed": "error.crash",
        r"exceeds threshold": "error.threshold_exceeded",
        r"alert": "error.alert"
    }
    message_lower = message.lower()
    for pattern, tag in keywords.items():
        if re.search(pattern, message_lower, re.IGNORECASE):
            tags.append(tag)
    return list(set(tags))

def predict_component(text: str) -> str:
    """Simple pattern matching for component detection"""
    text_lower = text.lower()
    for component, patterns in COMPONENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return component
    return "unknown"

def detect_source_type_and_component(line: str, component: Optional[str]) -> (str, str):
    if component and component.lower() != "unknown":
        return component, component.lower()
    predicted = predict_component(line)
    return predicted, predicted

def parse_json_log(line: str) -> Optional[Dict]:
    try:
        obj = json.loads(line)
        level = obj.get("level", "").lower()
        # Capture both error-level logs and logs containing "error" in message
        if level not in ["error", "warn", "warning", "alert"] and "error" not in obj.get("msg", "").lower() and "error" not in obj.get("message", "").lower():
            return None
            
        timestamp_raw = obj.get("utc_date", "") or obj.get("timestamp", "")
        timestamp = normalize_timestamp(timestamp_raw)
        message = obj.get("msg", "") or obj.get("message", "")
        component = obj.get("component", "") or "unknown"

        component_pred, source_type = detect_source_type_and_component(line, component)

        return {
            "timestamp": timestamp,
            "log": message,
            "label": "Error" if level == "error" else ("Warning" if level in ["warn", "warning"] else "Info"),
            "source": component_pred,
            "tags": infer_tags(message, component_pred, level),
            "source_type": source_type
        }
    except json.JSONDecodeError:
        return None

def parse_plain_log(line: str) -> Optional[Dict]:
    # Pattern for standard plain logs
    regex = r"^(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\s+(?P<level>\w+)\s+\[(?P<component>[^\]]+)\]\s+(?P<message>.+)$"
    m = re.match(regex, line)
    if m:
        level = m.group("level").lower()
        if level not in ["error", "warn", "warning", "alert"] and "error" not in m.group("message").lower():
            return None
            
        timestamp = normalize_timestamp(m.group("timestamp"))
        message = m.group("message")
        component = m.group("component") or "unknown"

        component_pred, source_type = detect_source_type_and_component(line, component)

        return {
            "timestamp": timestamp,
            "log": message,
            "label": "Error" if level == "error" else ("Warning" if level in ["warn", "warning"] else "Info"),
            "source": component_pred,
            "tags": infer_tags(message, component_pred, level),
            "source_type": source_type
        }
    
    # Pattern for kubernetes logs
    k8s_regex = r"^(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\s+(?P<level>\w+)\s+(?P<component>\w+)\s+(?P<message>.+)$"
    k8s_match = re.match(k8s_regex, line)
    if k8s_match:
        level = k8s_match.group("level").lower()
        if level not in ["error", "warn", "warning", "alert"] and "error" not in k8s_match.group("message").lower():
            return None
            
        timestamp = normalize_timestamp(k8s_match.group("timestamp"))
        message = k8s_match.group("message")
        component = k8s_match.group("component") or "unknown"

        component_pred, source_type = detect_source_type_and_component(line, component)

        return {
            "timestamp": timestamp,
            "log": message,
            "label": "Error" if level == "error" else ("Warning" if level in ["warn", "warning"] else "Info"),
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

def parse_http_status_log(line: str) -> Optional[Dict]:
    """
    Parses logs in format: "2025-05-31T18:41:32Z Error Status: 429 - Response: <!doctype html>"
    """
    pattern = r"^(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\s+(?P<level>\w+)\s+Status:\s(?P<status>\d{3})\s+-\s+Response:\s(?P<response>.+)$"
    match = re.match(pattern, line)
    if match:
        status_code = match.group("status")
        level = match.group("level").lower()
        try:
            code = int(status_code)
            if code < 400 and level not in ["error", "warn", "warning"]:
                return None
        except:
            return None

        timestamp = normalize_timestamp(match.group("timestamp"))
        message = match.group("response")
        component = "http"

        component_pred, source_type = detect_source_type_and_component(line, component)

        return {
            "timestamp": timestamp,
            "log": message,
            "label": "Error" if code >= 500 or level == "error" else ("Warning" if code >= 400 or level in ["warn", "warning"] else "Info"),
            "source": component_pred,
            "tags": infer_tags(f"Status: {status_code}", component_pred, "error" if code >= 500 else "warning"),
            "source_type": source_type
        }
    return None

def process_log_line(line: str) -> Optional[Dict]:
    for parser_func in [parse_json_log, parse_plain_log, parse_gin_log, parse_http_status_log]:
        result = parser_func(line)
        if result:
            return result
    return None

@app.route('/classify', methods=['POST'])
def classify_logs():
    """
    Endpoint to classify logs from a file, direct text input, or plain text body
    Accepts:
    - file: log file to process (multipart/form-data)
    - text: direct log text to process (application/json)
    - raw text: plain text body (text/plain)
    """
    # Handle file upload
    if 'file' in request.files:
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
    
    # Handle JSON input
    elif request.is_json and 'text' in request.json:
        lines = request.json['text'].split('\n')
        output = []
        for line in lines:
            parsed = process_log_line(line.strip())
            if parsed:
                output.append(parsed)
        return jsonify(output), 200
    
    # Handle plain text input
    elif request.content_type == 'text/plain':
        text = request.get_data(as_text=True)
        lines = text.split('\n')
        output = []
        for line in lines:
            parsed = process_log_line(line.strip())
            if parsed:
                output.append(parsed)
        return jsonify(output), 200
    
    return jsonify({
        "error": "Unsupported content type",
        "supported_types": [
            "multipart/form-data (file upload)",
            "application/json (with 'text' field)",
            "text/plain (raw log text)"
        ]
    }), 415

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "version": "1.0"})

@app.route('/')
def home():
    """Default endpoint with usage instructions"""
    return """
    <h1>Log Classification Service</h1>
    <p>Endpoints:</p>
    <ul>
        <li>POST /classify - Process log file or text</li>
        <li>GET /health - Service health check</li>
    </ul>
    <p>Send logs as either:</p>
    <ul>
        <li>File upload with 'file' form field</li>
        <li>JSON with {'text': 'log lines\\n'} in request body</li>
        <li>Plain text directly in request body</li>
    </ul>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
