PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS generations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    prompt          TEXT NOT NULL,
    negative_prompt TEXT,
    checkpoint      VARCHAR(255),
    sampler         VARCHAR(50),
    width           INTEGER,
    height          INTEGER,
    steps           INTEGER,
    cfg_scale       FLOAT,
    seed            BIGINT,
    image_path      TEXT NOT NULL DEFAULT '',
    image_data      BLOB NOT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_generations_user_id ON generations(user_id);