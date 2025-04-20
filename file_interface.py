import os
import time
import threading
import json
import logging
from agents.medical_agent import medical_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

def get_config():
    config_path = os.environ.get("APP_CONFIG_PATH", "config/app_config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)
app_config = get_config()

import logging.config
logging_config = json.load(open("config/logging.json", "r", encoding="utf-8"))
logging.config.dictConfig(logging_config)
logger = logging.getLogger("file_interface")

DATA_DIR = app_config["input_files_dir"]
RESPONSE_DIR = app_config["output_files_dir"]
os.makedirs(RESPONSE_DIR, exist_ok=True)
SESSION_SERVICE = InMemorySessionService()
APP_NAME = app_config["app_name"]

def process_file(file_path, user_id):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    session_id = os.path.splitext(os.path.basename(file_path))[0]
    runner = Runner(agent=medical_agent, app_name=APP_NAME, session_service=SESSION_SERVICE)
    responses = []
    for line in lines:
        if not line.strip():
            continue
        prefix, msg = line.split(":", 1) if ":" in line else ("send_by_patient", line)
        if prefix.strip().lower().startswith("send_by_patient"):
            content = Content(role="user", parts=[Part(text=msg.strip())])
            last_reply = ""
            for event in runner.run(user_id=user_id, session_id=session_id, new_message=content):
                if event.is_final_response():
                    last_reply = event.content.parts[0].text
                    responses.append(f"reply_by_agent:{last_reply}")
        elif prefix.strip().lower().startswith("send_by_doctor"):
            responses.append(f"note_by_doctor:{msg.strip()}")
    response_file = os.path.join(RESPONSE_DIR, f"response_{os.path.basename(file_path)}")
    with open(response_file, "w", encoding="utf-8") as f:
        for r in responses:
            f.write(r + "\n")
    logger.info(f"Réponses écrites dans : {response_file}")

def monitor_folder(input_folder, user_id="file_user"):
    already_processed = set()
    logger.info(f"Monitoring : {input_folder}")
    while True:
        files = [f for f in os.listdir(input_folder) if f.endswith(".txt")]
        for fname in files:
            full_path = os.path.join(input_folder, fname)
            if full_path not in already_processed:
                try:
                    process_file(full_path, user_id=user_id)
                    already_processed.add(full_path)
                except Exception as e:
                    logger.error(f"Erreur : {e}")
        time.sleep(3)

if __name__ == "__main__":
    monitor_folder(DATA_DIR)