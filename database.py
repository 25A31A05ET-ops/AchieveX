import os
import shutil
import sqlite3
import tempfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "database")
PROJECT_DB_PATH = os.path.join(DB_DIR, "achievex.db")
FALLBACK_DB_PATH = os.path.join(tempfile.gettempdir(), "achievex.db")
DB_PATH = os.environ.get(
    "DATABASE_PATH",
    FALLBACK_DB_PATH if os.environ.get("VERCEL") else PROJECT_DB_PATH,
)


def ensure_directories():
    for directory in (DB_DIR, os.path.join(BASE_DIR, "uploads")):
        try:
            os.makedirs(directory, exist_ok=True)
        except OSError:
            pass


def _open_database():
    global DB_PATH

    try:
        return sqlite3.connect(DB_PATH)
    except (OSError, sqlite3.OperationalError):
        if DB_PATH == FALLBACK_DB_PATH:
            raise

        if os.path.exists(PROJECT_DB_PATH) and not os.path.exists(FALLBACK_DB_PATH):
            try:
                shutil.copy2(PROJECT_DB_PATH, FALLBACK_DB_PATH)
            except OSError:
                pass

        DB_PATH = FALLBACK_DB_PATH
        return sqlite3.connect(DB_PATH)


def get_connection():
    ensure_directories()
    conn = _open_database()
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    ensure_directories()
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                short_name TEXT
            );

            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('STUDENT','FACULTY','VERIFIER')),
                department TEXT,
                academic_year TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                achievement_type TEXT,
                organization TEXT,
                achievement_date TEXT,
                position TEXT,
                description TEXT,
                department TEXT,
                academic_year TEXT,
                certificate_filename TEXT,
                evidence_filename TEXT,
                status TEXT NOT NULL DEFAULT 'PENDING' CHECK(status IN ('PENDING','VERIFIED','REJECTED')),
                is_featured INTEGER NOT NULL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS verifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                achievement_id INTEGER NOT NULL,
                verifier_id INTEGER,
                status TEXT NOT NULL CHECK(status IN ('APPROVED','REJECTED')),
                remarks TEXT,
                verified_at TEXT,
                FOREIGN KEY(achievement_id) REFERENCES achievements(id) ON DELETE CASCADE,
                FOREIGN KEY(verifier_id) REFERENCES users(id) ON DELETE SET NULL
            );
            """
        )

        department_rows = [
            ("Computer Science and Engineering", "CSE"),
            ("Electronics and Communication Engineering", "ECE"),
            ("Mechanical Engineering", "MECH"),
            ("Electrical Engineering", "EEE"),
            ("Information Technology", "IT"),
        ]

        for dep_name, short_name in department_rows:
            conn.execute(
                "INSERT OR IGNORE INTO departments (name, short_name) VALUES (?, ?)",
                (dep_name, short_name),
            )

        category_rows = [
            "Technical", "Non-Technical", "Hackathon", "Coding", "Certification",
            "Research", "Sports", "Cultural", "Entrepreneurship", "Innovation",
            "Leadership"
        ]

        for category_name in category_rows:
            conn.execute(
                "INSERT OR IGNORE INTO categories (name) VALUES (?)",
                (category_name,),
            )

        conn.commit()


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
