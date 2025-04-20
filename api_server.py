import os
import sys
import json
import logging
import uuid
import datetime
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from agents.medical_agent import medical_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
import dotenv

from utils.utils import sanitize_for_logging

# Charger les variables d'environnement
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
logger = logging.getLogger("medical_expert_api")

# Créer dossiers essentiels dynamiquement
for d in [app_config["logs_dir"], app_config["sessions_dir"], os.path.join(app_config["data_dir"], "patients")]:
    os.makedirs(d, exist_ok=True)

APP_NAME = app_config.get("app_name", "medical_expert_adk")
SESSION_SERVICE = InMemorySessionService()

# Initialisation de l'application Flask
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24).hex())
# Activer CORS pour permettre les requêtes cross-origin (utile pour les clients Web)
CORS(app)

# Dictionnaire pour conserver les runners par session
session_runners = {}


def get_runner_for_session(session_id):
    """Obtient ou crée un runner pour une session donnée."""
    if session_id not in session_runners:
        session_runners[session_id] = Runner(agent=medical_agent, app_name=APP_NAME, session_service=SESSION_SERVICE)
    return session_runners[session_id]


def generate_session_id():
    """Génère un identifiant de session unique."""
    dt = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"session_{dt}_{uuid.uuid4().hex[:4]}"


def generate_user_id():
    """Génère un identifiant utilisateur unique."""
    return f"user_{uuid.uuid4().hex[:8]}"


@app.route('/api/session/new', methods=['POST'])
def create_session():
    """Crée une nouvelle session et retourne ses identifiants."""
    data = request.get_json(silent=True) or {}

    # Utiliser les identifiants fournis ou en générer de nouveaux
    user_id = data.get("user_id", generate_user_id())
    session_id = data.get("session_id", generate_session_id())

    # Créer la session dans le service de session
    SESSION_SERVICE.create_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)

    # Log de création de session
    logger.info(f"Nouvelle session API créée : session_id={session_id} user_id={user_id}")

    return jsonify({
        "status": "success",
        "user_id": user_id,
        "session_id": session_id,
        "message": "Session créée avec succès"
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    """Point d'entrée principal pour la conversation avec l'agent."""
    data = request.json or {}

    # Vérifier que les paramètres requis sont présents
    if "message" not in data:
        return jsonify({"status": "error", "message": "Le paramètre 'message' est requis"}), 400

    # Récupérer ou générer les identifiants de session
    user_id = data.get("user_id")
    session_id = data.get("session_id")

    # Si l'un des identifiants est manquant, créer une nouvelle session
    if not user_id or not session_id:
        user_id = user_id or generate_user_id()
        session_id = session_id or generate_session_id()
        SESSION_SERVICE.create_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)
        logger.info(f"Nouvelle session API implicite : session_id={session_id} user_id={user_id}")

    message = data.get("message", "")
    safe_message = sanitize_for_logging(message)

    # Journaliser la requête
    logger.info(f"API User({user_id}) [{session_id}] : {safe_message}")

    # Préparer le contenu pour l'agent
    content = Content(role="user", parts=[Part(text=message)])

    # Obtenir le runner pour cette session
    runner = get_runner_for_session(session_id)

    # Exécuter l'agent et récupérer la réponse finale
    response_text = ""
    try:
        for event in runner.run(user_id=user_id, session_id=session_id, new_message=content):
            if event.is_final_response():
                response_text = event.content.parts[0].text

        # Journaliser la réponse (après sanitization pour éviter les problèmes d'encodage)
        safe_response = sanitize_for_logging(response_text)
        logger.info(f"API Agent [{session_id}] : {safe_response}")

        return jsonify({
            "status": "success",
            "user_id": user_id,
            "session_id": session_id,
            "response": response_text
        })

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Erreur lors du traitement de la requête pour session={session_id}: {error_msg}")
        return jsonify({
            "status": "error",
            "user_id": user_id,
            "session_id": session_id,
            "error": error_msg
        }), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """Récupère l'historique de conversation d'une session spécifique."""
    user_id = request.args.get("user_id")
    session_id = request.args.get("session_id")

    if not user_id or not session_id:
        return jsonify({"status": "error", "message": "Les paramètres user_id et session_id sont requis"}), 400

    # Cette fonctionnalité nécessiterait d'accéder à l'historique stocké dans la session
    # Pour l'instant, retournons un message explicatif
    return jsonify({
        "status": "success",
        "message": "Fonctionnalité d'historique pas encore implémentée. Vous devriez stocker l'historique côté client ou implémenter un stockage persistant."
    })


@app.route('/api/session/end', methods=['POST'])
def end_session():
    """Termine une session existante."""
    data = request.json or {}

    # Vérifier que les paramètres requis sont présents
    if "session_id" not in data:
        return jsonify({"status": "error", "message": "Le paramètre 'session_id' est requis"}), 400

    session_id = data["session_id"]
    user_id = data.get("user_id", "unknown")

    # Supprimer le runner associé à cette session
    if session_id in session_runners:
        del session_runners[session_id]

    # Log de fin de session
    logger.info(f"Fin session API : session_id={session_id} user_id={user_id}")

    return jsonify({
        "status": "success",
        "message": "Session terminée avec succès"
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Vérifie si l'API est en cours d'exécution."""
    return jsonify({
        "status": "ok",
        "message": "Medical Expert API is running",
        "version": app_config.get("version", "1.0.0"),
        "timestamp": datetime.datetime.now().isoformat()
    })


# Gestionnaire d'erreurs pour les routes non trouvées
@app.errorhandler(404)
def not_found(e):
    return jsonify({"status": "error", "message": "Endpoint not found"}), 404


# Gestionnaire d'erreurs global
@app.errorhandler(Exception)
def handle_exception(e):
    logger.exception("Erreur non gérée dans l'API")
    return jsonify({
        "status": "error",
        "message": "Une erreur interne s'est produite",
        "error": str(e)
    }), 500


if __name__ == '__main__':
    # Récupérer les paramètres de port et d'hôte à partir de la config ou des variables d'environnement
    port = int(os.environ.get("API_PORT", app_config.get("api_port", 8000)))
    host = os.environ.get("API_HOST", app_config.get("api_host", "0.0.0.0"))
    debug = os.environ.get("API_DEBUG", "").lower() in ("true", "1", "yes") or app_config.get("api_debug", False)

    print(f"=== Démarrage du serveur API Medical Expert sur {host}:{port} ===")
    app.run(host=host, port=port, debug=debug)