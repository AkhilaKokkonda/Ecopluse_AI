# import os
# import sqlite3
# from contextlib import contextmanager
# from pathlib import Path

# from dotenv import load_dotenv

# load_dotenv()

# BASE_DIR = Path(__file__).resolve().parent

# DATABASE_PATH = Path(
#     os.getenv("DATABASE_PATH", str(BASE_DIR / "data" / "ecopulse.db"))
# )

# DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)


# @contextmanager
# def get_connection():
#     connection = sqlite3.connect(DATABASE_PATH)
#     connection.row_factory = sqlite3.Row
#     connection.execute("PRAGMA foreign_keys = ON")

#     try:
#         yield connection
#         connection.commit()
#     except Exception:
#         connection.rollback()
#         raise
#     finally:
#         connection.close()


# def init_db():
#     """Create the database tables and safely add missing AI columns."""

#     with get_connection() as connection:
#         connection.executescript("""
#             CREATE TABLE IF NOT EXISTS issues (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 title TEXT NOT NULL,
#                 category TEXT NOT NULL,
#                 building TEXT NOT NULL,
#                 location_details TEXT NOT NULL,
#                 description TEXT NOT NULL,
#                 severity INTEGER NOT NULL DEFAULT 3,
#                 safety_risk INTEGER NOT NULL DEFAULT 1,
#                 near_electrical INTEGER NOT NULL DEFAULT 0,
#                 estimated_resource_loss REAL NOT NULL DEFAULT 0,
#                 unresolved_hours REAL NOT NULL DEFAULT 0,
#                 priority_score REAL NOT NULL DEFAULT 0,
#                 priority_level TEXT NOT NULL DEFAULT 'Low',
#                 priority_reasons TEXT NOT NULL DEFAULT '[]',
#                 recommended_action TEXT NOT NULL DEFAULT '',
#                 status TEXT NOT NULL DEFAULT 'Reported',
#                 reporter_name TEXT NOT NULL DEFAULT '',
#                 reporter_contact TEXT NOT NULL DEFAULT '',
#                 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
#                 updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

#                 ai_urgency TEXT NOT NULL DEFAULT 'Unknown',
#                 ai_explanation TEXT NOT NULL DEFAULT '',
#                 ai_missing_information TEXT NOT NULL DEFAULT '[]',
#                 ai_analyzed INTEGER NOT NULL DEFAULT 0
#             );

#             CREATE TABLE IF NOT EXISTS issue_history (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 issue_id INTEGER NOT NULL,
#                 previous_status TEXT,
#                 new_status TEXT NOT NULL,
#                 notes TEXT NOT NULL DEFAULT '',
#                 changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
#                 FOREIGN KEY (issue_id) REFERENCES issues(id)
#                     ON DELETE CASCADE
#             );

#             CREATE TABLE IF NOT EXISTS repair_verifications (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 issue_id INTEGER NOT NULL,
#                 repair_action TEXT NOT NULL,
#                 completion_notes TEXT NOT NULL DEFAULT '',
#                 estimated_repair_cost REAL NOT NULL DEFAULT 0,
#                 confirmed INTEGER NOT NULL DEFAULT 0,
#                 completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
#                 reopened_at TEXT,
#                 FOREIGN KEY (issue_id) REFERENCES issues(id)
#                     ON DELETE CASCADE
#             );

#             CREATE TABLE IF NOT EXISTS campus_locations (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 building_name TEXT NOT NULL,
#                 location_name TEXT NOT NULL,
#                 location_details TEXT NOT NULL DEFAULT '',
#                 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
#                 updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
#                 UNIQUE (building_name, location_name)
#             );

#             CREATE INDEX IF NOT EXISTS idx_issues_status
#                 ON issues(status);

#             CREATE INDEX IF NOT EXISTS idx_issues_priority
#                 ON issues(priority_level);

#             CREATE INDEX IF NOT EXISTS idx_issues_created
#                 ON issues(created_at);

#             CREATE INDEX IF NOT EXISTS idx_history_issue
#                 ON issue_history(issue_id);

#             CREATE INDEX IF NOT EXISTS idx_locations_building
#                 ON campus_locations(building_name);
#         """)

#         # Safely migrate an existing database without deleting its records.
#         existing_columns = {
#             row["name"]
#             for row in connection.execute(
#                 "PRAGMA table_info(issues)"
#             ).fetchall()
#         }

#         ai_columns = {
#             "ai_urgency": (
#                 "TEXT NOT NULL DEFAULT 'Unknown'"
#             ),
#             "ai_explanation": (
#                 "TEXT NOT NULL DEFAULT ''"
#             ),
#             "ai_missing_information": (
#                 "TEXT NOT NULL DEFAULT '[]'"
#             ),
#             "ai_analyzed": (
#                 "INTEGER NOT NULL DEFAULT 0"
#             ),
#         }

#         for column_name, column_definition in ai_columns.items():
#             if column_name not in existing_columns:
#                 connection.execute(
#                     f"ALTER TABLE issues ADD COLUMN "
#                     f"{column_name} {column_definition}"
#                 )


# if __name__ == "__main__":
#     init_db()
#     print("EcoPulse AI database initialized successfully.")
#     print(f"Database location: {DATABASE_PATH}")


import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

DATABASE_PATH = Path(
    os.getenv("DATABASE_PATH", str(BASE_DIR / "data" / "ecopulse.db"))
)

DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db():
    """Create tables and safely migrate missing columns."""

    with get_connection() as connection:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                building TEXT NOT NULL,
                location_details TEXT NOT NULL,
                description TEXT NOT NULL,
                severity INTEGER NOT NULL DEFAULT 3,
                safety_risk INTEGER NOT NULL DEFAULT 1,
                near_electrical INTEGER NOT NULL DEFAULT 0,
                estimated_resource_loss REAL NOT NULL DEFAULT 0,
                unresolved_hours REAL NOT NULL DEFAULT 0,
                priority_score REAL NOT NULL DEFAULT 0,
                priority_level TEXT NOT NULL DEFAULT 'Low',
                priority_reasons TEXT NOT NULL DEFAULT '[]',
                recommended_action TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Reported',
                reporter_name TEXT NOT NULL DEFAULT '',
                reporter_contact TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                ai_urgency TEXT NOT NULL DEFAULT 'Unknown',
                ai_explanation TEXT NOT NULL DEFAULT '',
                ai_missing_information TEXT NOT NULL DEFAULT '[]',
                ai_analyzed INTEGER NOT NULL DEFAULT 0,
                ai_recommended_action TEXT NOT NULL DEFAULT '',
                photo_path TEXT NOT NULL DEFAULT '',
                assigned_staff TEXT NOT NULL DEFAULT '',
                in_progress_at TEXT,
                resolved_at TEXT
            );

            CREATE TABLE IF NOT EXISTS issue_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_id INTEGER NOT NULL,
                previous_status TEXT,
                new_status TEXT NOT NULL,
                notes TEXT NOT NULL DEFAULT '',
                changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (issue_id) REFERENCES issues(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS repair_verifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_id INTEGER NOT NULL,
                repair_action TEXT NOT NULL,
                completion_notes TEXT NOT NULL DEFAULT '',
                estimated_repair_cost REAL NOT NULL DEFAULT 0,
                confirmed INTEGER NOT NULL DEFAULT 0,
                completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                reopened_at TEXT,
                FOREIGN KEY (issue_id) REFERENCES issues(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS campus_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                building_name TEXT NOT NULL,
                location_name TEXT NOT NULL,
                location_details TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (building_name, location_name)
            );

            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_id INTEGER NOT NULL,
                recipient_name TEXT NOT NULL DEFAULT '',
                message TEXT NOT NULL,
                is_read INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (issue_id) REFERENCES issues(id)
                    ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_issues_status
                ON issues(status);

            CREATE INDEX IF NOT EXISTS idx_issues_priority
                ON issues(priority_level);

            CREATE INDEX IF NOT EXISTS idx_issues_created
                ON issues(created_at);

            CREATE INDEX IF NOT EXISTS idx_history_issue
                ON issue_history(issue_id);

            CREATE INDEX IF NOT EXISTS idx_locations_building
                ON campus_locations(building_name);

            CREATE INDEX IF NOT EXISTS idx_notifications_issue
                ON notifications(issue_id);
        """)

        # Safely add missing columns to existing databases.
        existing_columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(issues)"
            ).fetchall()
        }

        required_columns = {
            "ai_urgency": "TEXT NOT NULL DEFAULT 'Unknown'",
            "ai_explanation": "TEXT NOT NULL DEFAULT ''",
            "ai_missing_information": "TEXT NOT NULL DEFAULT '[]'",
            "ai_analyzed": "INTEGER NOT NULL DEFAULT 0",
            "ai_recommended_action": "TEXT NOT NULL DEFAULT ''",
            "photo_path": "TEXT NOT NULL DEFAULT ''",
            "assigned_staff": "TEXT NOT NULL DEFAULT ''",
            "in_progress_at": "TEXT",
            "resolved_at": "TEXT",
        }

        for column_name, column_definition in required_columns.items():
            if column_name not in existing_columns:
                connection.execute(
                    f"ALTER TABLE issues ADD COLUMN "
                    f"{column_name} {column_definition}"
                )


if __name__ == "__main__":
    init_db()
    print("EcoPulse AI database initialized successfully.")
    print(f"Database location: {DATABASE_PATH}")
