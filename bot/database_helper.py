import sqlite3

class Database:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        # Create messages table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                role TEXT,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

        # Create users table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                age INTEGER,
                last_request_time DATETIME
            )
        """)
        self.conn.commit()

    def add_message(self, user_id, role, content):
        self.cursor.execute(
            "INSERT INTO messages (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content)
        )
        self.conn.commit()

    def get_message_history(self, user_id):
        self.cursor.execute("SELECT role, content FROM messages WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
        return self.cursor.fetchall()

    def get_message_count_today(self, user_id):
        self.cursor.execute(
            "SELECT COUNT(*) FROM messages WHERE user_id = ? AND DATE(timestamp) = DATE(CURRENT_TIMESTAMP)", (user_id,))
        return self.cursor.fetchone()[0]

    def add_or_update_user(self, user_id, name=None, age=None):
        self.cursor.execute("""
            INSERT OR IGNORE INTO users (user_id, name, age)
            VALUES (?, ?, ?)
        """, (user_id, name, age))

        if name or age:
            self.cursor.execute("""
                UPDATE users
                SET name = COALESCE(?, name),
                    age = COALESCE(?, age)
                WHERE user_id = ?
            """, (name, age, user_id))
        self.conn.commit()

    def get_user(self, user_id):
        self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = self.cursor.fetchone()
        if row:
            return {
                'user_id': row[0],
                'name': row[1],
                'age': row[2],
            }
        else:
            return None

    def update_last_request_time(self, user_id):
        self.cursor.execute(
            "UPDATE users SET last_request_time = CURRENT_TIMESTAMP WHERE user_id = ?",
            (user_id,)
        )
        self.conn.commit()

    def get_last_request_time(self, user_id):
        self.cursor.execute(
            "SELECT last_request_time FROM users WHERE user_id = ?",
            (user_id,)
        )
        row = self.cursor.fetchone()
        return row[0] if row else None
    def close(self):
        self.conn.close()
