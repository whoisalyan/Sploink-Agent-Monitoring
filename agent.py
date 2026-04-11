import requests
import time
import random
import uuid
import argparse

API_URL = "http://localhost:5000/events"

def send_event(session_id, step, action, input_str, output_str, status="success"):
    payload = {
        "session_id": session_id,
        "timestamp": time.time(),
        "step": step,
        "action": action,
        "input": input_str,
        "output": output_str,
        "metadata": {"status": status}
    }
    try:
        resp = requests.post(API_URL, json=payload)
        print(f"[{session_id[:8]}] Step {step}: {action} -> {resp.status_code}")
    except Exception as e:
        print(f"Error sending event: {e}")

def simulate_normal():
    session_id = f"normal-{uuid.uuid4().hex[:6]}"
    steps = [
        ("read_file", "config.json", "{'mode': 'prod'}"),
        ("llm_call", "analyze config", "The config is valid."),
        ("run_command", "npm start", "Server started on port 3000"),
        ("write_file", "logs.txt", "Check complete")
    ]
    for i, (act, inp, out) in enumerate(steps):
        send_event(session_id, i+1, act, inp, out)
        time.sleep(0.5)

def simulate_loop():
    session_id = f"loop-{uuid.uuid4().hex[:6]}"
    for i in range(1, 10):
        # Repeat the same action pattern
        action = "read_file" if i % 2 == 0 else "llm_call"
        inp = "check_status.py" if i % 2 == 0 else "is it done yet?"
        out = "file content..." if i % 2 == 0 else "no, wait."
        send_event(session_id, i, action, inp, out)
        time.sleep(0.3)

def simulate_drift():
    session_id = f"drift-{uuid.uuid4().hex[:6]}"
    # Start with file operations
    for i in range(1, 6):
        send_event(session_id, i, "read_file", f"file_{i}.txt", "content")
        time.sleep(0.3)
    # Drift into LLM calls exclusively
    for i in range(6, 11):
        send_event(session_id, i, "llm_call", "what is life?", "42")
        time.sleep(0.3)

def simulate_failure():
    session_id = f"failure-{uuid.uuid4().hex[:6]}"
    for i in range(1, 5):
        status = "success" if i < 2 else "failure"
        send_event(session_id, i, "run_command", "rm -rf /", "Permission denied", status=status)
        time.sleep(0.4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=["normal", "loop", "drift", "failure"], default="normal")
    args = parser.parse_args()
    
    scenarios = {
        "normal": simulate_normal,
        "loop": simulate_loop,
        "drift": simulate_drift,
        "failure": simulate_failure
    }
    
    print(f"Starting scenario: {args.scenario}")
    scenarios[args.scenario]()
    print("Simulation complete.")
