import os
import sys
import json
import logging
import uuid
import datetime
from agents.medical_agent import medical_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
import dotenv

from utils.utils import sanitize_for_logging

dotenv.load_dotenv()

# === CONFIG ===
APP_CONFIG_PATH = os.environ.get("APP_CONFIG_PATH", "config/app_config.json")
LOG_CONFIG_PATH = os.environ.get("LOG_CONFIG_PATH", "config/logging.json")

def load_json_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

app_config = load_json_config(APP_CONFIG_PATH)
logging_config = load_json_config(LOG_CONFIG_PATH)
import logging.config
logging.config.dictConfig(logging_config)
logger = logging.getLogger("medical_expert_cli")

# Créer dossiers essentiels dynamiquement
for d in [app_config["logs_dir"], app_config["sessions_dir"], os.path.join(app_config["data_dir"], "patients")]:
    os.makedirs(d, exist_ok=True)

APP_NAME = app_config.get("app_name", "medical_expert_adk")
SESSION_SERVICE = InMemorySessionService()

def get_user_id():
    uid = input("Identifiant utilisateur (laisser vide pour générer aléatoirement) : ").strip()
    if not uid:
        uid = "user_" + uuid.uuid4().hex[:8]
    return uid

def get_session_id():
    sid = input("Id de session (laisser vide pour générer avec timestamp) : ").strip()
    if not sid:
        dt = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        sid = f"session_{dt}_{uuid.uuid4().hex[:4]}"
    return sid

def main():
    print("=== Système Expert Médical (ADK) ===")
    user_id = get_user_id()
    session_id = get_session_id()
    logger.info(f"Démarrage session : session_id={session_id} user_id={user_id}")

    runner = Runner(agent=medical_agent, app_name=APP_NAME, session_service=SESSION_SERVICE)
    # >>>> AJOUT ICI <<<<
    SESSION_SERVICE.create_session(app_name=APP_NAME,user_id=user_id, session_id=session_id)
    print("Tapez vos symptômes/questions (ou 'exit' pour quitter) :")
    while True:
        user_input = input("> ").strip()
        if user_input.lower() in ("quit", "exit"):
            logger.info(f"Fin session : session_id={session_id} user_id={user_id}")
            break
        if not user_input:
            continue
        safe_user_input = sanitize_for_logging(user_input)
        logger.info(f"User({user_id}) [{session_id}] : {safe_user_input}")
        content = Content(role="user", parts=[Part(text=user_input)])
        response = ""
        for event in runner.run(user_id=user_id, session_id=session_id, new_message=content):
            if event.is_final_response():
                response = event.content.parts[0].text
        print(response)
        logger.info(f"Agent [{session_id}] : {response}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(f"Erreur fatale dans le CLI : {e}")
        sys.exit(1)