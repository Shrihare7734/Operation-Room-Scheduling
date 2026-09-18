from db import init_db, get_connection


def seed_database():
    init_db()
    conn = get_connection()

    conn.execute("DELETE FROM patients")
    conn.execute("DELETE FROM rooms")
    conn.execute("DELETE FROM surgeons")

    conn.executemany(
        "INSERT INTO rooms (name, equipment) VALUES (?, ?)",
        [
            ("General OR", "Standard surgical suite"),
            ("Cardiac OR", "Cardiac monitoring"),
            ("Ortho OR", "Joint replacement tools"),
        ],
    )

    conn.executemany(
        "INSERT INTO surgeons (name, available) VALUES (?, ?)",
        [
            ("Dr. Smith", "Mon-Fri"),
            ("Dr. Jones", "Mon-Fri"),
            ("Dr. Lee", "Tue-Sat"),
            ("Dr. Patel", "Mon-Thu"),
        ],
    )

    conn.executemany(
        "INSERT INTO patients (name, duration, direness, k, status) VALUES (?, ?, ?, ?, ?)",
        [
            ("Ava Morgan", 90, "routine", 1.1, "waiting"),
            ("Noah Singh", 75, "urgent", 1.8, "waiting"),
            ("Emma Wilson", 120, "critical", 2.5, "waiting"),
            ("Liam Davis", 60, "emergency", 3.0, "waiting"),
            ("Sophia Brown", 110, "routine", 1.4, "waiting"),
        ],
    )

    conn.commit()
    conn.close()
    print("Database seeded successfully.")


if __name__ == "__main__":
    seed_database()
