from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO
from pathlib import Path

from db import add_patient, delete_patient, get_all_patients, get_rooms, get_surgeons, init_db
from scheduler import build_schedule, handle_emergency, total_cost, validate_time_window
from seed import seed_database

app = Flask(__name__)
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*")


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


init_db()
if not get_all_patients():
    seed_database()


@app.route("/", methods=["GET"])
def index():
    if (FRONTEND_DIST / "index.html").exists():
        return send_from_directory(FRONTEND_DIST, "index.html")
    return jsonify({
        "message": "OR Scheduling Engine API",
        "routes": ["/patients", "/schedule", "/emergency", "/rooms", "/surgeons"],
    })


@app.route("/patients", methods=["GET"])
def list_patients():
    return jsonify({"patients": get_all_patients()})


@app.route("/schedule", methods=["POST"])
def create_schedule():
    data = request.get_json(silent=True) or {}
    patients = data.get("patients", [])
    selected_date = data.get("date")
    if selected_date:
        patients = [
            patient for patient in patients
            if not patient.get("preferred_date") or patient.get("preferred_date") == selected_date
        ]
    rooms = get_rooms()
    surgeons = get_surgeons()
    schedule = build_schedule(patients, rooms, surgeons)
    for index, patient in enumerate(schedule):
        room = next((item for item in rooms if item["id"] == patient.get("room_id")), None)
        surgeon = next((item for item in surgeons if item["id"] == patient.get("surgeon_id")), None)
        room = room or (rooms[index % len(rooms)] if rooms else None)
        surgeon = surgeon or (surgeons[index % len(surgeons)] if surgeons else None)
        if room:
            patient["room_id"] = room["id"]
            patient["room_name"] = room["name"]
            patient["room_type"] = room["equipment"]
        if surgeon:
            patient["surgeon_id"] = surgeon["id"]
            patient["surgeon_name"] = surgeon["name"]
    contexts = {item.get("scoring", {}).get("context") for item in schedule if item.get("scoring")}
    return jsonify({"schedule": schedule, "total_cost": total_cost(schedule), "context": next(iter(contexts), "NORMAL_OPERATIONS")})


@app.route("/emergency", methods=["POST"])
def emergency_handler():
    data = request.get_json(silent=True) or {}
    current_schedule = data.get("current_schedule", [])
    emergency_patient = data.get("emergency_patient", {})
    if emergency_patient.get("name") and emergency_patient.get("medical_id"):
        emergency_patient = add_patient({**emergency_patient, "status": "emergency"})
    schedule = handle_emergency(current_schedule, emergency_patient, get_rooms(), get_surgeons())
    response = {"schedule": schedule, "total_cost": total_cost(schedule)}
    socketio.emit("schedule_updated", response)
    return jsonify(response)


@app.route("/patients", methods=["POST"])
def create_patient():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Patient name is required."}), 400
    if not data.get("medical_id"):
        return jsonify({"error": "Medical ID is required."}), 400
    window_errors = validate_time_window(data)
    if window_errors:
        return jsonify({"error": window_errors[0]}), 400
    try:
        patient = add_patient(data)
    except Exception as exc:
        return jsonify({"error": f"Failed to add patient: {exc}"}), 400
    return jsonify({"patient": patient, "message": "Patient added successfully"})


@app.route("/patients/<int:patient_id>", methods=["DELETE"])
def remove_patient(patient_id):
    if not delete_patient(patient_id):
        return jsonify({"error": "Operation not found."}), 404
    return jsonify({"message": "Operation removed successfully"})


@app.route("/rooms", methods=["GET"])
def rooms():
    return jsonify({"rooms": get_rooms()})


@app.route("/surgeons", methods=["GET"])
def surgeons():
    return jsonify({"surgeons": get_surgeons()})


@app.route("/<path:path>", methods=["GET"])
def frontend_assets(path):
    requested_file = FRONTEND_DIST / path
    if requested_file.is_file():
        return send_from_directory(FRONTEND_DIST, path)
    if (FRONTEND_DIST / "index.html").exists():
        return send_from_directory(FRONTEND_DIST, "index.html")
    return jsonify({"error": "Frontend build not found."}), 404


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
