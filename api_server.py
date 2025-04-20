from flask import Flask, request, jsonify
from agents.medical_agent import medical_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

app = Flask(__name__)

APP_NAME = "medical_expert_adk"
SESSION_SERVICE = InMemorySessionService()

@app.route('/diagnose', methods=['POST'])
def diagnose_route():
    data = request.json
    user_id = data.get("user_id", "anonymous")
    session_id = data.get("session_id", f"session_{user_id}")
    message = data.get("message", "")
    runner = Runner(agent=medical_agent, app_name=APP_NAME, session_service=SESSION_SERVICE)
    content = Content(role="user", parts=[Part(text=message)])
    response_text = ""
    for event in runner.run(user_id=user_id, session_id=session_id, new_message=content):
        if event.is_final_response():
            response_text = event.content.parts[0].text
    return jsonify({
        "user_id": user_id,
        "session_id": session_id,
        "response": response_text
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "Medical Expert API is running."})

if __name__ == '__main__':
    app.run(port=8000, debug=True)