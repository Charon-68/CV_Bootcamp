import sqlite3
import json
from typing import Any
from vision.types import Incident
from runtime.logger import get_logger

logger = get_logger("nexusguard.database")

class Database:
    def __init__(self, db_path: str = "nexusguard.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    frame_index INTEGER,
                    risk REAL,
                    label TEXT,
                    summary TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    meta TEXT
                )
            ''')
            conn.commit()
        logger.info(f"Database initialized at {self.db_path}")

    def insert_incident(self, event: Incident):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO incidents (frame_index, risk, label, summary, meta)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    event.frame_index,
                    event.risk,
                    event.label,
                    event.summary,
                    json.dumps(event.meta)
                ))
                conn.commit()
            logger.info(f"Persisted incident for frame {event.frame_index} to DB.")
        except Exception as e:
            logger.error(f"Failed to persist incident: {e}")

db = Database()
