# Medical Expert ADK — Système Expert Médical Moderne

## Présentation

Ce projet fournit un système expert médical conversationnel, extensible et professionnel, basé sur l'Agent Development Kit (ADK) de Google, combinant la puissance des LLMs et des règles expertes.

---

## Fonctionnalités principales

- **Interface CLI** (terminal interactif)
- **Interface par fichiers** (surveillance de dossiers pour intégration batch ou avec d'autres langages/systèmes)
- **API REST/HTTP** (consommable en local ou à distance par tout langage)
- **Logging détaillé** (suivi, audit, debug)
- **Historique patient/session** (mémoire longue, suivi multiconsultations)
- **Ajout dynamique de maladies/règles** (outils d'extension inclus)
- **Explications naturelles, pédagogiques, personnalisées**
- **Multi-utilisateur, multi-session, multi-interface**
- **Extensible (agents secondaires, plugins, etc.)**

---

## Structure du projet

- `agents/` … Agents ADK (logique intelligente, orchestration)
- `tools/` … Outils métier (diagnostic, ajout règle, mémoire patient…)
- `data/` … Connaissances, descriptions, traitements, etc.
- `config/` … Fichiers de configuration (paramètres, logs, …)
- `logs/` … Journaux système (générés automatiquement)
- `sessions/` … Sauvegarde des historiques de session (générés dynamiquement)
- `file_interface.py` … Interface batch/texte (interopérabilité)
- `api_server.py` … API HTTP REST (intégration externe)
- `main.py` … Interface CLI (terminal)
- `requirements.txt` … Dépendances Python

---

## Configuration

- Place tes paramètres généraux dans `config/app_config.json` (modèle, langues, chemins, …)
- Configure le logging dans `config/logging.json` (emplacement des logs, niveau, format)
- Mets tes clés API dans `.env`

---

## 1. Utilisation CLI (Terminal interactif)

```sh
python main.py
```
- Lancement du système en mode interactif.
- **Création dynamique de session et d'utilisateur** : tu choisis ou génères un ID utilisateur/session au lancement.
- Dialogue naturel : tu tapes tes symptômes/questions, l’agent répond, pose des questions, effectue un diagnostic, explique, etc.
- L’historique et les logs sont automatiquement sauvegardés dans `sessions/` et `logs/`.

---

## 2. Utilisation via fichiers (interopérabilité batch ou pilotage externe)

- Place un fichier `.txt` dans `data/demo_inputs/` avec des lignes du type :

```txt
send_by_patient:Bonjour, j'ai de la fièvre et je tousse.
send_by_patient:Pas d'autres symptômes.
send_by_doctor:Merci, peux-tu préciser si tu as mal à la poitrine ?
```

- Lance la surveillance :
```sh
python file_interface.py
```
- Le système lit tous les nouveaux fichiers dans ce dossier, traite chaque message, et écrit les réponses dans `data/demo_outputs/` (même nom que le fichier source, préfixé par `response_`).

---

## 3. Utilisation via API REST (pour intégration avec d'autres applications/langages)

- Lance le serveur :
```sh
python api_server.py
```
- Tu peux alors envoyer des requêtes HTTP POST comme :

```sh
curl -X POST http://localhost:8000/diagnose \
  -H "Content-Type: application/json" \
  -d '{"user_id":"u001", "session_id":"sess001", "message":"J\'ai mal à la tête et de la fatigue"}'
```

- **Réponse:**
```json
{
  "user_id": "u001",
  "session_id": "sess001",
  "response": "D’après vos symptômes…"
}
```

### Exemple d'intégration Java (ex : agent Jade ou autre)

Supposons que tu utilises JADE ou tout autre agent Java, voici comment il pourrait interroger le système :

```java
import java.net.*;
import java.io.*;
import org.json.JSONObject;

public class MedicalExpertClient {
    public static void main(String[] args) throws Exception {
        String payload = "{\"user_id\":\"jade_agent_1\",\"session_id\":\"jade_sess_20250420\",\"message\":\"J'ai mal à la tête et de la fièvre.\"}";
        URL url = new URL("http://localhost:8000/diagnose");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("POST");
        conn.setRequestProperty("Content-Type", "application/json");
        conn.setDoOutput(true);

        OutputStream os = conn.getOutputStream();
        os.write(payload.getBytes());
        os.flush();

        BufferedReader in = new BufferedReader(new InputStreamReader(conn.getInputStream()));
        String line, response = "";
        while ((line = in.readLine()) != null) response += line;
        in.close();

        JSONObject json = new JSONObject(response);
        System.out.println("Réponse du système expert : " + json.getString("response"));
    }
}
```
- L’agent Java envoie simplement un POST à `/diagnose` et récupère la réponse.
- Tu peux donc intégrer ce système dans n’importe quelle architecture multi-agent, workflow, etc.

### Exemple de code Java (agent Jade) pour une conversation multi-tour via fichier :

```java 
import java.io.*;
import java.nio.file.*;
import java.util.List;

public class JadeFileAgent {

    private static final String INPUT_FILE = "data/demo_inputs/session_jade_001.txt";
    private static final String OUTPUT_FILE = "data/demo_outputs/response_session_jade_001.txt";

    // Envoie un message au système expert
    public static void sendMessage(String message) throws IOException {
        try (FileWriter fw = new FileWriter(INPUT_FILE, true)) {
            fw.write("send_by_patient:" + message + "\n");
        }
    }

    // Récupère la dernière réponse du système expert
    public static String getLastAgentReply() throws IOException, InterruptedException {
        Path outputPath = Paths.get(OUTPUT_FILE);
        for (int i = 0; i < 30; i++) { // Attend jusqu'à 30s max
            if (Files.exists(outputPath)) {
                List<String> lines = Files.readAllLines(outputPath);
                // Cherche la dernière ligne commençant par "reply_by_agent:"
                for (int j = lines.size() - 1; j >= 0; j--) {
                    String line = lines.get(j);
                    if (line.startsWith("reply_by_agent:")) {
                        return line.substring("reply_by_agent:".length()).trim();
                    }
                }
            }
            Thread.sleep(1000); // Attend 1s avant de relire
        }
        return "Pas de réponse du système expert (timeout)";
    }

    public static void main(String[] args) throws Exception {
        // Session multi-tour
        sendMessage("Bonjour, j'ai de la fièvre et mal à la tête.");
        System.out.println("Agent: " + getLastAgentReply());

        sendMessage("Non, je n'ai pas de toux.");
        System.out.println("Agent: " + getLastAgentReply());

        sendMessage("Oui, j'ai de la fatigue.");
        System.out.println("Agent: " + getLastAgentReply());

        // etc. Ajouter autant de messages que nécessaire
    }
}

```
> À respecter :
 - Ne jamais écraser les fichiers, toujours ajouter à la fin (append).
 - Toujours attendre la réponse dans OUTPUT avant d’envoyer un nouveau message.
 - Laisser le même nom de fichier pour toute la session (ex : session_jade_001.txt).

#### Explication du format d'échange fichier
- Input (écrit par Jade/Java/autre programme) :

- send_by_patient:Votre message...
(optionnel) : send_by_doctor:Votre message...
Output (produit par le système expert, même nom, prefixé response_) :

- reply_by_agent:Réponse générée...
(optionnel pour logs ou audits) : note_by_system:...
Multi-tour :

- Chaque message patient = 1 nouvelle ligne input
L’agent attend la nouvelle ligne de réponse output avant de continuer


## Exemple d'intégration avec Jade/Java (par fichier)

**1. L'agent écrit dans un fichier d'entrée (data/demo_inputs/session_jade_001.txt) :**
```
send_by_patient:Bonjour, j'ai mal à la tête.
send_by_patient:Oui, un peu de fatigue.
```
**2. Le système expert écrit les réponses ligne à ligne dans data/demo_outputs/response_session_jade_001.txt :**
```
reply_by_agent:Merci, avez-vous de la fièvre ? (oui/non)
reply_by_agent:Sur la base de vos symptômes, il est possible que...
```
**3. Le programme Java lit le fichier output après chaque message, puis écrit le suivant, etc.**

**Respecter ce format garantit un dialogue multi-tour robuste et sans erreur.**
---


## 4. Fonctionnement interne & histoire des sessions

- Chaque **session** est identifiée par `user_id` et `session_id` (créés dynamiquement ou fournis).
- Toute la conversation, les symptômes, les diagnostics, et l’historique sont sauvegardés dans `sessions/`.
- Les logs détaillés sont sauvegardés dans `logs/` (tout est configurable).
- Les outils peuvent mémoriser l’historique patient (`data/patients/`), permettant un vrai suivi longitudinal.

---

## 5. Ajout/mise à jour des connaissances

- Pour ajouter une maladie ou un symptôme, édite `data/disease_rules.json`, `data/symptom_questions.json`, `data/disease_descriptions/`, etc.
- Pour ajouter un outil métier ou une règle avancée, modifie `tools/diagnosis_tools.py`.
- Pour intégrer Experta (ancien système règles), utilise `tools/experta_adapter.py` ou migre progressivement.

---

## 6. Extensibilité

- Tu peux créer d’autres agents (ex : triage, suivi, urgence…) dans `agents/`.
- Tu peux exposer d’autres endpoints dans `api_server.py`.
- Tu peux plugger d’autres interfaces (GUI, mobile, etc.) très facilement.

---

## 7. Logs & configuration

- Les logs (niveau, format, destination) sont paramétrés dans `config/logging.json`.
- Les chemins, options générales, modèles, etc. sont dans `config/app_config.json`.
- Les logs sont générés automatiquement, et tu peux les visualiser après coup pour audit ou debug.

---

## 8. Gestion dynamique des sessions et utilisateurs

- À chaque lancement ou requête, tu peux choisir/générer un nouvel ID utilisateur et/ou session.
- Plusieurs utilisateurs peuvent utiliser le système simultanément (API ou CLI multi-session).
- L’historique est isolé par utilisateur/session.

---

## 9. FAQ

- **Peut-on utiliser le système à distance ?** Oui, via l’API REST.
- **Peut-on le piloter depuis du Java, C#, etc. ?** Oui, il suffit de faire des requêtes HTTP/JSON.
- **Peut-on enrichir la base de maladies ?** Oui, édition simple des fichiers JSON/TXT dans `data/`.

---

# Bon usage du Medical Expert ADK !