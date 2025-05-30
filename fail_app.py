from flask import Flask
import threading
import time
import os

app = Flask(__name__)
healthy = True

# Fail the app after N seconds
FAIL_AFTER = int(os.getenv("FAIL_AFTER", 30))

def trigger_failure():
    global healthy
    time.sleep(FAIL_AFTER)
    print("Simulating app failure now...")
    healthy = False

@app.route('/health')
def health():
    if healthy:
        return "OK", 200
    else:
        return "FAIL", 500

@app.route('/')
def home():
    return "Hello from the fail-app! Hit /health to check status."

if __name__ == '__main__':
    threading.Thread(target=trigger_failure).start()
    app.run(host='0.0.0.0', port=8080)
