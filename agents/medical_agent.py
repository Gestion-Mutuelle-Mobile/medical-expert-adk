from google.adk.agents import Agent
from tools.diagnosis_tools import (
    diagnose, list_symptoms, suggest_questions, add_new_rule,
    explain_disease, get_patient_history, save_patient_interaction
)
import os
import json

def load_app_config():
    config_path = os.environ.get("APP_CONFIG_PATH", "config/app_config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

app_config = load_app_config()
MODEL_ID = app_config.get("default_model", "gemini-2.0-flash")

medical_agent = Agent(
    name=app_config.get("medical_agent_name", "medical_expert_agent"),
    model=MODEL_ID,
    description=(
        "Agent expert médical conversationnel, capable de diagnostiquer, expliquer, "
        "mémoriser, enrichir ses règles, conseiller et dialoguer naturellement."
    ),
    instruction=(
        "Tu es un agent médical intelligent (et tu te fais passer pour le docteur Fox et te comporte comme tel), empathique, rigoureux. "
        "Guide l'utilisateur pour collecter tous les symptômes pertinents (un par un si besoin). "
        "Utilise 'diagnose' dès que possible pour proposer un diagnostic, toujours expliquer l'incertitude. "
        "Propose d'autres questions avec 'suggest_questions' si tu hésites. "
        "Utilise 'list_symptoms' pour savoir quoi demander. "
        "Tu peux aussi appeler 'add_new_rule' si un nouveau cas se présente. "
        "Pour chaque maladie, explique en détail ('explain_disease') et donne conseils. "
        "Sauvegarde chaque échange ('save_patient_interaction'). "
        "Sois toujours bienveillant, rassurant, pédagogique et professionnel et tu peux aussi te permettre de l'humour."
        "Si dans la bases de fichiers de connaissances une maladie ne figure pas ou son traitement tu es libre d'utiliser tes connaissances a toi en tant que LLM."
"si tu estime que la consultation est finie , dans ton dernier message du dois rajouter 'END_DIAG' a la fin"
    ),
    tools=[
        diagnose,
        list_symptoms,
        suggest_questions,
        add_new_rule,
        explain_disease,
        get_patient_history,
        save_patient_interaction
    ]
)