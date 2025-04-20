import json
import os
from google.adk.tools import ToolContext
from datetime import datetime

def get_config():
    config_path = os.environ.get("APP_CONFIG_PATH", "config/app_config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

app_config = get_config()
DATA_DIR = app_config.get("data_dir", "data/")
RULES_FILE = os.path.join(DATA_DIR, "disease_rules.json")
SYMPTOMS_FILE = os.path.join(DATA_DIR, "disease_symptoms.json")
QUESTIONS_FILE = os.path.join(DATA_DIR, "symptom_questions.json")
DESCRIPTIONS_DIR = os.path.join(DATA_DIR, "disease_descriptions")
TREATMENTS_DIR = os.path.join(DATA_DIR, "disease_treatments")
PATIENT_HISTORY_DIR = os.path.join(DATA_DIR, "patients")
os.makedirs(PATIENT_HISTORY_DIR, exist_ok=True)

def _load_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _get_description(disease):
    path = os.path.join(DESCRIPTIONS_DIR, f"{disease}.txt")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return "Description indisponible pour cette maladie."

def _get_treatment(disease):
    path = os.path.join(TREATMENTS_DIR, f"{disease}.txt")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return "Conseils ou traitements indisponibles pour cette maladie."

def _patient_history_path(patient_id):
    return os.path.join(PATIENT_HISTORY_DIR, f"{patient_id}.json")

def diagnose(symptoms: dict, tool_context: ToolContext = None) -> dict:
    """
    Diagnostique une maladie probable selon les symptômes fournis.
    Args:
        symptoms (dict): Dictionnaire {symptôme: 'oui'/'non'}
    Returns:
        dict: status, diagnosis, score, description, treatment
    """
    rules = _load_json(RULES_FILE)
    best_match = None
    max_score = -1
    for disease, rule in rules.items():
        score = sum(
            (symptoms.get(k, "").lower() == v.lower())
            for k, v in rule.items()
        )
        if score > max_score:
            max_score = score
            best_match = disease

    if best_match and max_score > 0:
        desc = _get_description(best_match)
        treat = _get_treatment(best_match)
        return {
            "status": "success",
            "diagnosis": best_match,
            "score": max_score,
            "description": desc,
            "treatment": treat
        }
    else:
        return {
            "status": "error",
            "message": "Aucune maladie détectée avec confiance à partir des symptômes fournis."
        }

def list_symptoms(tool_context: ToolContext = None) -> dict:
    """
    Retourne la liste des symptômes connus du système.
    """
    rules = _load_json(RULES_FILE)
    all_symptoms = set()
    for rule in rules.values():
        all_symptoms.update(rule.keys())
    return {
        "status": "success",
        "symptoms": sorted(list(all_symptoms))
    }

def suggest_questions(symptoms: dict = None, tool_context: ToolContext = None) -> dict:
    """
    Suggère les prochaines questions les plus discriminantes à poser à l'utilisateur.
    """
    questions = _load_json(QUESTIONS_FILE)
    rules = _load_json(RULES_FILE)
    # Priorité : symptômes non encore renseignés, les plus discriminants (présents dans le plus de maladies)
    all_symptoms = set()
    for rule in rules.values():
        all_symptoms.update(rule.keys())
    already_asked = set(symptoms.keys()) if symptoms else set()
    to_ask = [s for s in all_symptoms if s not in already_asked]
    # Tri par "fréquence" d'apparition dans les règles (les plus partagés en premier)
    freq = {s: 0 for s in to_ask}
    for rule in rules.values():
        for s in to_ask:
            if s in rule:
                freq[s] += 1
    suggestions = sorted(to_ask, key=lambda s: -freq[s])
    questions_out = [questions.get(s, f"Présentez-vous ce symptôme : {s} ? (oui/non)") for s in suggestions]
    return {
        "status": "success",
        "questions": questions_out
    }

def add_new_rule(disease: str, symptoms: dict, tool_context: ToolContext = None) -> dict:
    """
    Permet à l'agent d'ajouter une nouvelle règle de diagnostic (si besoin, sur validation humaine).
    Args:
        disease (str): Nom de la maladie
        symptoms (dict): Dictionnaire {symptôme: 'oui'/'non'}
    Returns:
        dict: status, message
    """
    rules = _load_json(RULES_FILE)
    if disease in rules:
        return {
            "status": "error",
            "message": f"La maladie '{disease}' existe déjà."
        }
    rules[disease] = symptoms
    _save_json(RULES_FILE, rules)
    return {
        "status": "success",
        "message": f"Nouvelle maladie '{disease}' ajoutée avec succès."
    }

def explain_disease(disease: str, tool_context: ToolContext = None) -> dict:
    """
    Donne une explication complète sur une maladie (description + traitement).
    """
    desc = _get_description(disease)
    treat = _get_treatment(disease)
    return {
        "status": "success",
        "disease": disease,
        "description": desc,
        "treatment": treat
    }

def get_patient_history(patient_id: str, tool_context: ToolContext = None) -> dict:
    """
    Récupère tout l'historique patient (diagnostics, symptômes, dates...).
    """
    path = _patient_history_path(patient_id)
    if not os.path.exists(path):
        return {
            "status": "error",
            "message": f"Aucun historique trouvé pour l'identifiant patient {patient_id}."
        }
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {
        "status": "success",
        "history": data
    }

def save_patient_interaction(patient_id: str, interaction: dict, tool_context: ToolContext = None) -> dict:
    """
    Sauvegarde une interaction (symptômes, résultats, timestamp) dans l'historique patient.
    """
    path = _patient_history_path(patient_id)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []
    timestamp = datetime.utcnow().isoformat()
    interaction['timestamp'] = timestamp
    data.append(interaction)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return {
        "status": "success",
        "message": f"Interaction sauvegardée pour {patient_id}."
    }