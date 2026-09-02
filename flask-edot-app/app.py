from flask import Flask, jsonify, request
from datetime import datetime
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Routes de l'application ---

@app.route("/")
def index():
    logger.info("Route / accessed")
    return jsonify({
        "message": "Bienvenue sur l'application Flask instrumentée avec EDOT",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    })

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat() + "Z"})

@app.route("/users", methods=["GET"])
def list_users():
    logger.info("GET /users")
    users = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
        {"id": 3, "name": "Charlie"},
    ]
    return jsonify({"users": users})

@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    logger.info(f"GET /users/{user_id}")
    users = {1: "Alice", 2: "Bob", 3: "Charlie"}
    name = users.get(user_id)
    if name is None:
        logger.warning(f"User {user_id} not found")
        return jsonify({"error": "User not found"}), 404
    return jsonify({"id": user_id, "name": name})

@app.route("/users", methods=["POST"])
def create_user():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "Anonymous")
    logger.info(f"POST /users with name={name}")
    return jsonify({"id": 4, "name": name, "created": True}), 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
