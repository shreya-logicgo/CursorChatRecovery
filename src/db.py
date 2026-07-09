import sqlite3


class CursorDB:

    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def composer_records(self):

        cur = self.conn.cursor()

        cur.execute("""
            SELECT key,value
            FROM cursorDiskKV
            WHERE key LIKE 'composerData:%'
        """)

        return cur.fetchall()

    def get_record(self, key: str):
        cur = self.conn.cursor()

        cur.execute(
            """
            SELECT value
            FROM cursorDiskKV
            WHERE key = ?
            """,
            (key,)
        )

        row = cur.fetchone()

        return row["value"] if row else None
