import sqlite3

db = r"server\data\transitshield.db"
conn = sqlite3.connect(db)
c = conn.cursor()


def ensure_columns(table, columns):
    c.execute(f"PRAGMA table_info({table})")
    existing = [row[1] for row in c.fetchall()]
    print(f"{table}: {existing}")
    for col_name, col_def in columns.items():
        if col_name not in existing:
            c.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}")
            print(f"  + Added {col_name}")
    conn.commit()


ensure_columns("reports", {
    "created_at": "DATETIME DEFAULT NULL",
})

ensure_columns("candidate_clips", {
    "clip_id": "TEXT DEFAULT ''",
    "vlm_result": "TEXT DEFAULT NULL",
    "timestamp": "DATETIME DEFAULT NULL",
    "verification_status": "TEXT DEFAULT 'pending'",
})

ensure_columns("investigation_timeline_entries", {
    "candidate_id": "INTEGER DEFAULT NULL",
    "timestamp": "DATETIME DEFAULT NULL",
    "camera_id": "TEXT DEFAULT ''",
    "location": "TEXT DEFAULT ''",
    "note": "TEXT DEFAULT ''",
    "sort_order": "INTEGER DEFAULT 0",
})

conn.close()
print("Migration complete.")
