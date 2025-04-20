"""
Adapter Experta pour l'intégrer comme outil dans ADK :
permet de réutiliser ou d'interfacer la logique experta dans le nouveau système.
"""

try:
    from experta import KnowledgeEngine, Fact, Rule, DefFacts, MATCH, W, NOT
except ImportError:
    raise ImportError("Experta doit être installé pour utiliser l'adapter : pip install experta")

import os
import json

# Si tu veux migrer/adapter les règles experta, tu peux t'inspirer de ce squelette.
class MedicalExpertEngine(KnowledgeEngine):
    def __init__(self, rules_path="data/disease_rules.json"):
        super().__init__()
        self.rules = self._load_rules(rules_path)
        self.facts_memory = []

    def _load_rules(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @DefFacts()
    def base(self):
        yield Fact(findDisease="true")

    # Pour chaque symptôme, on peut générer dynamiquement une méthode ask_XXX
    # ou les coder à la main, voir ton code d'origine.

    # Règles de diagnostic (simplification)
    # On peut itérer sur self.rules pour générer dynamiquement les règles.

    # Exemples :
    # @Rule(Fact(findDisease="true"), ...)
    # def disease_X(self):
    #     self.declare(Fact(disease="Covid"))
    # ...etc.

    # Pour la démo, on va juste implémenter un diagnostic simple :
    def diagnose(self, symptoms):
        """
        Utilise la logique experta pour diagnostiquer selon les symptômes fournis.
        """
        best = None
        max_score = -1
        for disease, rule in self.rules.items():
            score = sum(
                (symptoms.get(k, "").lower() == v.lower())
                for k, v in rule.items()
            )
            if score > max_score:
                max_score = score
                best = disease
        return best, max_score

# Fonction ADK Tool pour utiliser Experta
def experta_diagnose(symptoms: dict, tool_context=None) -> dict:
    """
    Diagnostiquer via Experta (backend règles)
    """
    engine = MedicalExpertEngine()
    disease, score = engine.diagnose(symptoms)
    if disease and score > 0:
        return {
            "status": "success",
            "diagnosis": disease,
            "score": score
        }
    return {
        "status": "error",
        "message": "Aucune maladie détectée via Experta."
    }