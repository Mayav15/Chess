# Chess Database — Player profiles with SQLite
# Handles user accounts: signup, login, password hashing, and game stat tracking
# Pure database logic — no pygame imports here

import sqlite3
import hashlib
import os
import uuid
from datetime import datetime

# Where the SQLite database file lives (next to this code)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chess_profiles.db')

# How many iterations to run when hashing passwords. Higher = more secure but slower.
# 100,000 is a common standard recommended by security organizations.
PBKDF2_ITERATIONS = 100_000


class ProfileDB:
    #This class is the only thing that talks to the database
    #All other code goes through this class to create users, log in, and update stats

    def __init__(self, db_path=None):
        #Opens (or creates) the SQLite database file
        self.db_path = db_path or DB_PATH
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  #Lets us access columns by name (e.g. row['username'])
        self._create_tables()

    def _create_tables(self):
        #Creates the players table if it doesn't exist yet
        #Running this every time is safe because of "IF NOT EXISTS"
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS players (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    uuid            TEXT    UNIQUE NOT NULL,
                    username        TEXT    UNIQUE NOT NULL,
                    password_hash   TEXT    NOT NULL,
                    salt            TEXT    NOT NULL,
                    created_at      TEXT    NOT NULL,
                    last_active     TEXT    NOT NULL,
                    games_played    INTEGER DEFAULT 0,
                    wins            INTEGER DEFAULT 0,
                    losses          INTEGER DEFAULT 0,
                    draws           INTEGER DEFAULT 0,
                    current_streak  INTEGER DEFAULT 0,
                    max_streak      INTEGER DEFAULT 0
                )
            ''')

    def _hash_password(self, password, salt=None):
        #Hashes a password using PBKDF2 with SHA-256
        #If no salt is provided, generates a new random one (used during signup)
        #Returns (hash_hex, salt_hex) as hex strings for easy storage in the database
        if salt is None:
            salt = os.urandom(32)  #32 random bytes — different for every user
        elif isinstance(salt, str):
            salt = bytes.fromhex(salt)  #Convert hex string back to bytes
        #PBKDF2 runs the hash function many times to slow down brute-force attacks
        hash_bytes = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, PBKDF2_ITERATIONS)
        return hash_bytes.hex(), salt.hex()

    def _row_to_dict(self, row):
        #Converts a SQLite Row object into a regular Python dict
        #Returns None if the row is None (no user found)
        if row is None:
            return None
        return {key: row[key] for key in row.keys()}

    def create_user(self, username, password):
        #Creates a new user account. Returns the user dict on success, None if username is taken
        #Username matching is case-insensitive (Alice == alice)
        username = username.strip()
        if not username:
            return None

        # Check if username already exists (case-insensitive)
        existing = self.conn.execute(
            'SELECT id FROM players WHERE LOWER(username) = LOWER(?)',
            (username,)
        ).fetchone()
        if existing:
            return None  #Username taken

        # Hash the password and generate a unique ID for this user
        password_hash, salt = self._hash_password(password)
        user_uuid = str(uuid.uuid4())  #Stable global ID for future websocket/online use
        now = datetime.now().isoformat()

        try:
            with self.conn:
                cursor = self.conn.execute('''
                    INSERT INTO players (uuid, username, password_hash, salt, created_at, last_active)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_uuid, username, password_hash, salt, now, now))
                user_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            return None  #Race condition — someone else just took this username

        return self.get_user(user_id)

    def authenticate(self, username, password):
        #Verifies username + password and returns the user dict on success, None on failure
        #Updates last_active timestamp when login succeeds
        username = username.strip()
        row = self.conn.execute(
            'SELECT * FROM players WHERE LOWER(username) = LOWER(?)',
            (username,)
        ).fetchone()
        if row is None:
            return None  #Username doesn't exist

        # Re-hash the provided password using the same salt and compare
        expected_hash, _ = self._hash_password(password, row['salt'])
        if expected_hash != row['password_hash']:
            return None  #Wrong password

        # Update last active time
        now = datetime.now().isoformat()
        with self.conn:
            self.conn.execute(
                'UPDATE players SET last_active = ? WHERE id = ?',
                (now, row['id'])
            )

        return self.get_user(row['id'])

    def get_user(self, user_id):
        #Fetches a user by ID and returns a dict of their data
        row = self.conn.execute(
            'SELECT * FROM players WHERE id = ?',
            (user_id,)
        ).fetchone()
        return self._row_to_dict(row)

    def update_stats(self, user_id, result):
        #Updates a user's stats after a game ends
        #result is one of: 'win', 'loss', 'draw'
        #Wins increment current_streak; losses and draws reset it to 0
        #max_streak grows whenever current_streak exceeds the previous max
        if result not in ('win', 'loss', 'draw'):
            return  #Ignore invalid results silently

        row = self.conn.execute(
            'SELECT current_streak, max_streak FROM players WHERE id = ?',
            (user_id,)
        ).fetchone()
        if row is None:
            return  #User doesn't exist

        current_streak = row['current_streak']
        max_streak = row['max_streak']

        # Streak logic — only consecutive wins count as a streak
        if result == 'win':
            current_streak += 1
            if current_streak > max_streak:
                max_streak = current_streak
        else:
            current_streak = 0  #Loss or draw breaks the streak

        # Build the update statement based on the result
        now = datetime.now().isoformat()
        column_to_increment = {'win': 'wins', 'loss': 'losses', 'draw': 'draws'}[result]

        with self.conn:
            self.conn.execute(f'''
                UPDATE players
                SET games_played = games_played + 1,
                    {column_to_increment} = {column_to_increment} + 1,
                    current_streak = ?,
                    max_streak = ?,
                    last_active = ?
                WHERE id = ?
            ''', (current_streak, max_streak, now, user_id))

    def close(self):
        #Closes the database connection
        if self.conn:
            self.conn.close()
            self.conn = None
