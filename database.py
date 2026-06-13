"""
database.py - Database Initialization and Helper Functions
Uses SQLite for lightweight, file-based storage suitable for a college project.
"""

import sqlite3
import hashlib
import os
import shutil

# Path to the SQLite database file
# If running on Vercel, we must write to /tmp since the root directory is read-only
if os.environ.get("VERCEL"):
    DB_PATH = "/tmp/evoting.db"
    # Ensure the parent directory exists (useful for local simulation too)
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    # Copy the pre-seeded template database to /tmp on startup if not already present
    if not os.path.exists(DB_PATH):
        src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evoting.db")
        if os.path.exists(src_path):
            try:
                shutil.copy2(src_path, DB_PATH)
                print(f"[DB] Seeded database copied to writeable location: {DB_PATH}")
            except Exception as e:
                print(f"[DB] Error copying database to /tmp: {e}")
        else:
            print(f"[DB] Seeded database not found at source: {src_path}")
else:
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evoting.db")


def get_connection():
    """Returns a new database connection with row factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Allows column access by name
    return conn


def hash_password(password):
    """Hashes a password using SHA-256 for secure storage."""
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    """
    Initializes all database tables and seeds sample data.
    Safe to call multiple times — uses IF NOT EXISTS.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # --- Create Tables ---

    # Voters table: stores registered voter credentials
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS voters (
            voter_id    TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            password    TEXT NOT NULL,
            has_voted   INTEGER DEFAULT 0
        )
    """)

    # Candidates table: stores candidate details
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            candidate_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_name  TEXT NOT NULL
        )
    """)

    # Votes table: records each cast vote (no voter identity stored here)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            vote_id         INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id    INTEGER NOT NULL,
            timestamp       TEXT NOT NULL,
            FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id)
        )
    """)

    # Blockchain table: mirrors blockchain data in DB for persistence
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blockchain (
            block_index     INTEGER PRIMARY KEY,
            timestamp       TEXT NOT NULL,
            vote_data       TEXT NOT NULL,
            previous_hash   TEXT NOT NULL,
            current_hash    TEXT NOT NULL
        )
    """)

    # Election settings table: controls election state
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS election_settings (
            id              INTEGER PRIMARY KEY CHECK (id = 1),
            election_active INTEGER DEFAULT 0,
            election_name   TEXT DEFAULT 'College Student Council Election 2024'
        )
    """)

    # Admin table: stores admin credentials
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            admin_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL
        )
    """)

    conn.commit()

    # --- Seed Sample Data (only if tables are empty) ---

    # Default admin account: username=admin, password=admin123
    cursor.execute("SELECT COUNT(*) FROM admins")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO admins (username, password) VALUES (?, ?)",
            ("admin", hash_password("admin123"))
        )

    # Default election settings row
    cursor.execute("SELECT COUNT(*) FROM election_settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO election_settings (id, election_active) VALUES (1, 0)"
        )

    # Sample voters (voter_id, name, password)
    cursor.execute("SELECT COUNT(*) FROM voters")
    if cursor.fetchone()[0] == 0:
        sample_voters = [
            ("V001", "Arjun Kumar",      hash_password("pass001")),
            ("V002", "Priya Sharma",     hash_password("pass002")),
            ("V003", "Rahul Verma",      hash_password("pass003")),
            ("V004", "Sneha Patel",      hash_password("pass004")),
            ("V005", "Karthik Rajan",    hash_password("pass005")),
            ("V006", "Divya Nair",       hash_password("pass006")),
            ("V007", "Anil Mehta",       hash_password("pass007")),
            ("V008", "Pooja Singh",      hash_password("pass008")),
            ("V009", "Vikram Rao",       hash_password("pass009")),
            ("V010", "Meera Iyer",       hash_password("pass010")),
        ]
        cursor.executemany(
            "INSERT INTO voters (voter_id, name, password) VALUES (?, ?, ?)",
            sample_voters
        )

    # Sample candidates
    cursor.execute("SELECT COUNT(*) FROM candidates")
    if cursor.fetchone()[0] == 0:
        sample_candidates = [
            ("Amit Shah",),
            ("Neha Gupta",),
            ("Rohan Das",),
            ("Sunita Rao",),
        ]
        cursor.executemany(
            "INSERT INTO candidates (candidate_name) VALUES (?)",
            sample_candidates
        )

    conn.commit()
    conn.close()
    print("[DB] Database initialized with sample data.")


# ─── Helper Query Functions ────────────────────────────────────────────────────

def get_all_candidates():
    conn = get_connection()
    candidates = conn.execute("SELECT * FROM candidates").fetchall()
    conn.close()
    return [dict(c) for c in candidates]


def get_all_voters():
    conn = get_connection()
    voters = conn.execute("SELECT voter_id, name, has_voted FROM voters").fetchall()
    conn.close()
    return [dict(v) for v in voters]


def get_vote_counts():
    """Returns candidate names alongside their vote tallies."""
    conn = get_connection()
    results = conn.execute("""
        SELECT c.candidate_id, c.candidate_name, COUNT(v.vote_id) as vote_count
        FROM candidates c
        LEFT JOIN votes v ON c.candidate_id = v.candidate_id
        GROUP BY c.candidate_id
        ORDER BY vote_count DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in results]


def get_election_status():
    conn = get_connection()
    row = conn.execute("SELECT * FROM election_settings WHERE id=1").fetchone()
    conn.close()
    return dict(row) if row else {"election_active": 0}


def save_block_to_db(block):
    """Persists a blockchain block to the database for durability."""
    conn = get_connection()
    conn.execute("""
        INSERT OR REPLACE INTO blockchain
            (block_index, timestamp, vote_data, previous_hash, current_hash)
        VALUES (?, ?, ?, ?, ?)
    """, (
        block["index"],
        block["timestamp"],
        f"voter:{block['voter_id_hash'][:16]}... | candidate:{block['candidate_id']}",
        block["previous_hash"],
        block["current_hash"]
    ))
    conn.commit()
    conn.close()


def get_blockchain_from_db():
    """Loads all saved blockchain blocks from DB (for display only)."""
    conn = get_connection()
    blocks = conn.execute(
        "SELECT * FROM blockchain ORDER BY block_index"
    ).fetchall()
    conn.close()
    return [dict(b) for b in blocks]


def get_total_votes():
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM votes").fetchone()[0]
    conn.close()
    return count


def get_total_voters():
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM voters").fetchone()[0]
    conn.close()
    return count
