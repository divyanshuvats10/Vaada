CREATE TABLE IF NOT EXISTS politicians (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    party       TEXT,
    channel_url TEXT,
    added_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS videos (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    politician_id INTEGER REFERENCES politicians(id),
    youtube_id   TEXT UNIQUE,
    title        TEXT,
    upload_date  DATE,
    duration_seconds INTEGER,
    processed    INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS statements (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    politician_id  INTEGER REFERENCES politicians(id),
    video_id       INTEGER REFERENCES videos(id),
    text           TEXT,
    start_time     REAL,
    end_time       REAL,
    youtube_url    TEXT,
    topic_tags     TEXT,
    embedding      BLOB,
    statement_date DATE,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS contradictions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    statement_a_id   INTEGER REFERENCES statements(id),
    statement_b_id   INTEGER REFERENCES statements(id),
    classification   TEXT,
    confidence       REAL,
    explanation      TEXT,
    severity         TEXT,
    detected_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);