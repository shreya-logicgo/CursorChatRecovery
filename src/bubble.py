import json


class BubbleParser:

    def __init__(self, db):
        self.db = db

    def load(self, bubble_id):

        key = f"bubbleId:{bubble_id}"

        value = self.db.get_record(key)

        if value is None:
            cur = self.db.conn.cursor()
            cur.execute(
                """
                SELECT value
                FROM cursorDiskKV
                WHERE key LIKE ?
                """,
                (f"bubbleId:%:{bubble_id}",),
            )
            row = cur.fetchone()
            value = row["value"] if row else None

        if value is None:
            return None

        return json.loads(value)
