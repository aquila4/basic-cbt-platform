"""
init_db.py
Creates database.db with the required tables and loads demo/sample data.
Run this once before starting the app: python init_db.py
Safe to re-run — it drops and recreates all tables each time.
"""

import sqlite3
from werkzeug.security import generate_password_hash

DB_PATH = "database.db"

SCHEMA = """
DROP TABLE IF EXISTS student_answers;
DROP TABLE IF EXISTS results;
DROP TABLE IF EXISTS questions;
DROP TABLE IF EXISTS exams;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS admins;

CREATE TABLE admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL
);

CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE exams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    duration_minutes INTEGER NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_id INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_answer TEXT NOT NULL CHECK (correct_answer IN ('A','B','C','D')),
    FOREIGN KEY (exam_id) REFERENCES exams (id) ON DELETE CASCADE
);

CREATE TABLE results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    exam_id INTEGER NOT NULL,
    score INTEGER NOT NULL,
    total_questions INTEGER NOT NULL,
    percentage REAL NOT NULL,
    date_taken TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE,
    FOREIGN KEY (exam_id) REFERENCES exams (id) ON DELETE CASCADE
);

CREATE TABLE student_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    result_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    selected_answer TEXT,
    is_correct INTEGER NOT NULL,
    FOREIGN KEY (result_id) REFERENCES results (id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions (id) ON DELETE CASCADE
);
"""

def seed(conn):
    cur = conn.cursor()

    # Demo admin
    cur.execute(
        "INSERT INTO admins (username, password_hash, full_name) VALUES (?, ?, ?)",
        ("admin", generate_password_hash("admin123"), "System Administrator"),
    )

    # Demo students
    students = [
        ("STU001", "John Doe", "student001", "student123"),
        ("STU002", "Amina Yusuf", "student002", "student123"),
        ("STU003", "Chidi Okafor", "student003", "student123"),
    ]
    for sid, name, uname, pwd in students:
        cur.execute(
            "INSERT INTO students (student_id, full_name, username, password_hash) VALUES (?, ?, ?, ?)",
            (sid, name, uname, generate_password_hash(pwd)),
        )

    # Demo exam
    cur.execute(
        "INSERT INTO exams (title, description, duration_minutes) VALUES (?, ?, ?)",
        ("Mathematics Mock Test", "General mathematics practice exam covering basic arithmetic, algebra and geometry.", 30),
    )
    exam_id = cur.lastrowid

    questions = [
        ("What is 2 + 2?", "3", "4", "5", "6", "B"),
        ("What is the capital of Nigeria?", "Lagos", "Abuja", "Kano", "Ibadan", "B"),
        ("What is 12 x 3?", "24", "30", "36", "42", "C"),
        ("Which number is a prime number?", "9", "15", "21", "13", "D"),
        ("What is the square root of 81?", "7", "8", "9", "10", "C"),
        ("If x + 5 = 12, what is x?", "5", "6", "7", "8", "C"),
        ("What is 100 divided by 4?", "20", "25", "30", "35", "B"),
        ("What is the value of pi (to 2 decimal places)?", "3.12", "3.14", "3.16", "3.18", "B"),
        ("What is 15% of 200?", "20", "25", "30", "35", "C"),
        ("How many sides does a hexagon have?", "5", "6", "7", "8", "B"),
        ("What is 9 squared?", "72", "81", "90", "99", "B"),
        ("What is the sum of angles in a triangle?", "90 degrees", "180 degrees", "270 degrees", "360 degrees", "B"),
    ]
    for q_text, a, b, c, d, correct in questions:
        cur.execute(
            """INSERT INTO questions
               (exam_id, question_text, option_a, option_b, option_c, option_d, correct_answer)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (exam_id, q_text, a, b, c, d, correct),
        )

    conn.commit()


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    seed(conn)
    conn.close()
    print("Database initialized: database.db")
    print("Demo admin      -> username: admin       password: admin123")
    print("Demo student 1  -> username: student001  password: student123")
    print("Demo student 2  -> username: student002  password: student123")
    print("Demo student 3  -> username: student003  password: student123")


if __name__ == "__main__":
    main()
