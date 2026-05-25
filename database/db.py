import sqlite3
import os

DB_PATH = "data/db/vaada.db"


def get_connection():
    os.makedirs("data/db", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets you access columns by name
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_connection()
    with open("database/schema.sql", "r") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print("✓ Database initialized")


# ── Politicians ──────────────────────────────────────────────

def add_politician(name: str, party: str, channel_url: str) -> int:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO politicians (name, party, channel_url) VALUES (?, ?, ?)",
        (name, party, channel_url)
    )
    conn.commit()
    pid = cursor.lastrowid
    conn.close()
    return pid


def get_all_politicians() -> list:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM politicians").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Videos ───────────────────────────────────────────────────

def add_video(politician_id: int, youtube_id: str, title: str,
              upload_date: str, duration: int) -> int:
    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO videos (politician_id, youtube_id, title, upload_date, duration_seconds)
               VALUES (?, ?, ?, ?, ?)""",
            (politician_id, youtube_id, title, upload_date, duration)
        )
        conn.commit()
        vid = cursor.lastrowid
    except sqlite3.IntegrityError:
        # video already exists
        row = conn.execute(
            "SELECT id FROM videos WHERE youtube_id = ?", (youtube_id,)
        ).fetchone()
        vid = row['id']
    conn.close()
    return vid


def mark_video_processed(video_id: int):
    conn = get_connection()
    conn.execute("UPDATE videos SET processed = 1 WHERE id = ?", (video_id,))
    conn.commit()
    conn.close()


# ── Statements ───────────────────────────────────────────────

def add_statement(politician_id: int, video_id: int, text: str,
                  start_time: float, end_time: float, youtube_url: str,
                  topic_tags: str, embedding: bytes, statement_date: str) -> int:
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO statements
           (politician_id, video_id, text, start_time, end_time,
            youtube_url, topic_tags, embedding, statement_date)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (politician_id, video_id, text, start_time, end_time,
         youtube_url, topic_tags, embedding, statement_date)
    )
    conn.commit()
    sid = cursor.lastrowid
    conn.close()
    return sid


def get_statements_for_politician(politician_id: int, topic: str = None) -> list:
    conn = get_connection()
    if topic:
        rows = conn.execute(
            """SELECT * FROM statements
               WHERE politician_id = ? AND topic_tags LIKE ?
               ORDER BY statement_date ASC""",
            (politician_id, f'%{topic}%')
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT * FROM statements
               WHERE politician_id = ?
               ORDER BY statement_date ASC""",
            (politician_id,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Contradictions ───────────────────────────────────────────

def add_contradiction(statement_a_id: int, statement_b_id: int,
                      classification: str, confidence: float,
                      explanation: str, severity: str) -> int:
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO contradictions
           (statement_a_id, statement_b_id, classification, confidence, explanation, severity)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (statement_a_id, statement_b_id, classification,
         confidence, explanation, severity)
    )
    conn.commit()
    cid = cursor.lastrowid
    conn.close()
    return cid


def get_contradictions_for_politician(politician_id: int,
                                       severity: str = None) -> list:
    conn = get_connection()
    query = """
        SELECT c.*, 
               sa.text as text_a, sa.youtube_url as url_a, sa.statement_date as date_a,
               sb.text as text_b, sb.youtube_url as url_b, sb.statement_date as date_b
        FROM contradictions c
        JOIN statements sa ON c.statement_a_id = sa.id
        JOIN statements sb ON c.statement_b_id = sb.id
        WHERE sa.politician_id = ?
    """
    params = [politician_id]

    if severity:
        query += " AND c.severity = ?"
        params.append(severity)

    query += " ORDER BY c.detected_at DESC"

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]