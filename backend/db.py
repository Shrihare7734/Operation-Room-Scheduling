import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "or_schedule.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            medical_id TEXT,
            procedure_type TEXT DEFAULT 'General Surgery',
            duration INTEGER NOT NULL,
            direness TEXT NOT NULL,
            k REAL NOT NULL,
            status TEXT DEFAULT 'waiting',
            arrival_time TEXT,
            earliest_start_time TEXT,
            latest_end_time TEXT,
            estimated_min_duration INTEGER,
            estimated_max_duration INTEGER,
            preferred_date TEXT,
            preferred_start_time TEXT,
            notes TEXT,
            surgeon_id INTEGER,
            room_id INTEGER,
            equipment TEXT
        )
        """
    )
    table_info = conn.execute("PRAGMA table_info(patients)").fetchall()
    columns = {row[1] for row in table_info}
    migrations = {
        "arrival_time": "TEXT",
        "earliest_start_time": "TEXT",
        "latest_end_time": "TEXT",
        "estimated_min_duration": "INTEGER",
        "estimated_max_duration": "INTEGER",
        "medical_id": "TEXT",
        "procedure_type": "TEXT DEFAULT 'General Surgery'",
        "preferred_date": "TEXT",
        "preferred_start_time": "TEXT",
        "notes": "TEXT",
        "surgeon_id": "INTEGER",
        "room_id": "INTEGER",
        "equipment": "TEXT",
    }
    for column, definition in migrations.items():
        if column not in columns:
            conn.execute(f"ALTER TABLE patients ADD COLUMN {column} {definition}")
    conn.execute("UPDATE patients SET preferred_date = COALESCE(preferred_date, date('now', 'localtime'))")
    conn.execute("UPDATE patients SET preferred_date = date('now', 'localtime') WHERE medical_id IS NULL")
    conn.execute("UPDATE patients SET procedure_type = COALESCE(procedure_type, 'General Surgery')")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            equipment TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS surgeons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            available TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def get_all_patients():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM patients ORDER BY id ASC").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_patient(data):
    conn = get_connection()
    arrival_time = data.get("arrival_time") or __import__("datetime").datetime.now().isoformat()
    equipment = data.get("equipment", "")
    if isinstance(equipment, list):
        equipment = ", ".join(str(item) for item in equipment)
    cursor = conn.execute(
        """
        INSERT INTO patients (name, medical_id, procedure_type, duration, direness, k, status,
                 arrival_time, earliest_start_time, latest_end_time,
                 estimated_min_duration, estimated_max_duration, preferred_date, preferred_start_time, notes,
                     surgeon_id, room_id, equipment)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data.get("name"),
            data.get("medical_id"),
            data.get("procedure_type", "General Surgery"),
            int(data.get("duration", 0)),
            data.get("direness", "routine"),
            float(data.get("k", 1.0)),
            data.get("status", "waiting"),
            arrival_time,
            data.get("earliest_start_time") or arrival_time,
            data.get("latest_end_time"),
            data.get("estimated_min_duration") or data.get("duration") or 30,
            data.get("estimated_max_duration") or data.get("estimated_min_duration") or data.get("duration") or 60,
            data.get("preferred_date"),
            data.get("preferred_start_time"),
            data.get("notes"),
            data.get("surgeon_id") or None,
            data.get("room_id") or None,
            equipment,
        ),
    )
    conn.commit()
    patient_id = cursor.lastrowid
    conn.close()
    return {"id": patient_id, **data, "duration": int(data.get("duration", 0)), "k": float(data.get("k", 1.0)), "status": data.get("status", "waiting"), "arrival_time": arrival_time}


def delete_patient(patient_id):
    conn = get_connection()
    cursor = conn.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0


def update_status(patient_id, status):
    conn = get_connection()
    conn.execute("UPDATE patients SET status = ? WHERE id = ?", (status, patient_id))
    conn.commit()
    conn.close()


def get_rooms():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM rooms ORDER BY id ASC").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_surgeons():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM surgeons ORDER BY id ASC").fetchall()
    conn.close()
    return [dict(row) for row in rows]
