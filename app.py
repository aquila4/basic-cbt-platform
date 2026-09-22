"""
app.py
Basic CBT (Computer-Based Test) platform prototype.

Run:
    python init_db.py   (once, to create database.db + demo data)
    python app.py

Then open http://127.0.0.1:5000
"""

import sqlite3
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import check_password_hash

DB_PATH = "database.db"

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-this-in-production"  # prototype only


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


# ---------------------------------------------------------------------------
# Auth helpers / decorators
# ---------------------------------------------------------------------------

def student_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "student":
            flash("Please log in as a student to continue.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Please log in as an admin to continue.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    if session.get("role") == "student":
        return redirect(url_for("student_dashboard"))
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form.get("role")
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        db = get_db()

        if role == "student":
            user = db.execute(
                "SELECT * FROM students WHERE username = ?", (username,)
            ).fetchone()
            if user and check_password_hash(user["password_hash"], password):
                session.clear()
                session["role"] = "student"
                session["user_id"] = user["id"]
                session["full_name"] = user["full_name"]
                return redirect(url_for("student_dashboard"))
            flash("Invalid student username or password.", "error")

        elif role == "admin":
            user = db.execute(
                "SELECT * FROM admins WHERE username = ?", (username,)
            ).fetchone()
            if user and check_password_hash(user["password_hash"], password):
                session.clear()
                session["role"] = "admin"
                session["user_id"] = user["id"]
                session["full_name"] = user["full_name"]
                return redirect(url_for("admin_dashboard"))
            flash("Invalid admin username or password.", "error")
        else:
            flash("Please select a role.", "error")

        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Student routes
# ---------------------------------------------------------------------------

@app.route("/student/dashboard")
@student_required
def student_dashboard():
    db = get_db()
    student = db.execute(
        "SELECT * FROM students WHERE id = ?", (session["user_id"],)
    ).fetchone()

    exams = db.execute(
        """SELECT e.*, COUNT(q.id) AS question_count
           FROM exams e LEFT JOIN questions q ON q.exam_id = e.id
           GROUP BY e.id ORDER BY e.id"""
    ).fetchall()

    taken_exam_ids = {
        row["exam_id"]
        for row in db.execute(
            "SELECT exam_id FROM results WHERE student_id = ?", (student["id"],)
        ).fetchall()
    }

    return render_template(
        "student_dashboard.html", student=student, exams=exams, taken_exam_ids=taken_exam_ids
    )


@app.route("/student/instructions/<int:exam_id>")
@student_required
def instructions(exam_id):
    db = get_db()
    exam = db.execute("SELECT * FROM exams WHERE id = ?", (exam_id,)).fetchone()
    if not exam:
        flash("Exam not found.", "error")
        return redirect(url_for("student_dashboard"))
    question_count = db.execute(
        "SELECT COUNT(*) AS c FROM questions WHERE exam_id = ?", (exam_id,)
    ).fetchone()["c"]
    return render_template("instructions.html", exam=exam, question_count=question_count)


@app.route("/student/exam/<int:exam_id>")
@student_required
def exam(exam_id):
    db = get_db()
    exam_row = db.execute("SELECT * FROM exams WHERE id = ?", (exam_id,)).fetchone()
    if not exam_row:
        flash("Exam not found.", "error")
        return redirect(url_for("student_dashboard"))

    questions = db.execute(
        "SELECT id, question_text, option_a, option_b, option_c, option_d FROM questions WHERE exam_id = ? ORDER BY id",
        (exam_id,),
    ).fetchall()

    if not questions:
        flash("This exam has no questions yet.", "error")
        return redirect(url_for("student_dashboard"))

    return render_template("exam.html", exam=exam_row, questions=questions)


@app.route("/student/submit/<int:exam_id>", methods=["POST"])
@student_required
def submit_exam(exam_id):
    db = get_db()
    exam_row = db.execute("SELECT * FROM exams WHERE id = ?", (exam_id,)).fetchone()
    if not exam_row:
        flash("Exam not found.", "error")
        return redirect(url_for("student_dashboard"))

    questions = db.execute(
        "SELECT * FROM questions WHERE exam_id = ? ORDER BY id", (exam_id,)
    ).fetchall()

    correct_count = 0
    answer_rows = []
    for q in questions:
        selected = request.form.get(f"question_{q['id']}")
        is_correct = 1 if selected == q["correct_answer"] else 0
        correct_count += is_correct
        answer_rows.append((q["id"], selected, is_correct))

    total = len(questions)
    percentage = round((correct_count / total) * 100, 1) if total else 0.0

    cur = db.execute(
        """INSERT INTO results (student_id, exam_id, score, total_questions, percentage, date_taken)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (session["user_id"], exam_id, correct_count, total, percentage, datetime.now().isoformat(sep=" ", timespec="seconds")),
    )
    result_id = cur.lastrowid

    db.executemany(
        "INSERT INTO student_answers (result_id, question_id, selected_answer, is_correct) VALUES (?, ?, ?, ?)",
        [(result_id, qid, sel, ok) for qid, sel, ok in answer_rows],
    )
    db.commit()

    return redirect(url_for("result", result_id=result_id))


@app.route("/student/result/<int:result_id>")
@student_required
def result(result_id):
    db = get_db()
    result_row = db.execute(
        """SELECT r.*, s.full_name AS student_name, e.title AS exam_title
           FROM results r
           JOIN students s ON s.id = r.student_id
           JOIN exams e ON e.id = r.exam_id
           WHERE r.id = ?""",
        (result_id,),
    ).fetchone()

    if not result_row or result_row["student_id"] != session["user_id"]:
        flash("Result not found.", "error")
        return redirect(url_for("student_dashboard"))

    wrong = result_row["total_questions"] - result_row["score"]
    return render_template("result.html", result=result_row, wrong=wrong)


# ---------------------------------------------------------------------------
# Admin routes — dashboard
# ---------------------------------------------------------------------------

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    db = get_db()
    total_students = db.execute("SELECT COUNT(*) AS c FROM students").fetchone()["c"]
    total_exams = db.execute("SELECT COUNT(*) AS c FROM exams").fetchone()["c"]
    total_questions = db.execute("SELECT COUNT(*) AS c FROM questions").fetchone()["c"]
    recent_results = db.execute(
        """SELECT r.*, s.full_name AS student_name, e.title AS exam_title
           FROM results r
           JOIN students s ON s.id = r.student_id
           JOIN exams e ON e.id = r.exam_id
           ORDER BY r.id DESC LIMIT 5"""
    ).fetchall()
    return render_template(
        "admin_dashboard.html",
        total_students=total_students,
        total_exams=total_exams,
        total_questions=total_questions,
        recent_results=recent_results,
    )


# ---------------------------------------------------------------------------
# Admin routes — students
# ---------------------------------------------------------------------------

@app.route("/admin/students")
@admin_required
def students():
    db = get_db()
    all_students = db.execute("SELECT * FROM students ORDER BY id").fetchall()
    return render_template("students.html", students=all_students)


@app.route("/admin/students/add", methods=["GET", "POST"])
@admin_required
def add_student():
    if request.method == "POST":
        full_name = (request.form.get("full_name") or "").strip()
        student_id = (request.form.get("student_id") or "").strip()
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        if not all([full_name, student_id, username, password]):
            flash("All fields are required.", "error")
            return redirect(url_for("add_student"))

        db = get_db()
        try:
            from werkzeug.security import generate_password_hash
            db.execute(
                "INSERT INTO students (student_id, full_name, username, password_hash) VALUES (?, ?, ?, ?)",
                (student_id, full_name, username, generate_password_hash(password)),
            )
            db.commit()
            flash(f"Student '{full_name}' added successfully.", "success")
            return redirect(url_for("students"))
        except sqlite3.IntegrityError:
            flash("A student with that Student ID or username already exists.", "error")
            return redirect(url_for("add_student"))

    return render_template("add_student.html")


@app.route("/admin/students/delete/<int:student_pk>", methods=["POST"])
@admin_required
def delete_student(student_pk):
    db = get_db()
    db.execute("DELETE FROM students WHERE id = ?", (student_pk,))
    db.commit()
    flash("Student deleted.", "success")
    return redirect(url_for("students"))


# ---------------------------------------------------------------------------
# Admin routes — exams
# ---------------------------------------------------------------------------

@app.route("/admin/exams")
@admin_required
def exams():
    db = get_db()
    all_exams = db.execute(
        """SELECT e.*, COUNT(q.id) AS question_count
           FROM exams e LEFT JOIN questions q ON q.exam_id = e.id
           GROUP BY e.id ORDER BY e.id"""
    ).fetchall()
    return render_template("exams.html", exams=all_exams)


@app.route("/admin/exams/add", methods=["GET", "POST"])
@admin_required
def add_exam():
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        description = (request.form.get("description") or "").strip()
        duration = request.form.get("duration_minutes")

        if not title or not duration:
            flash("Exam title and duration are required.", "error")
            return redirect(url_for("add_exam"))

        db = get_db()
        db.execute(
            "INSERT INTO exams (title, description, duration_minutes) VALUES (?, ?, ?)",
            (title, description, int(duration)),
        )
        db.commit()
        flash(f"Exam '{title}' created successfully.", "success")
        return redirect(url_for("exams"))

    return render_template("add_exam.html")


@app.route("/admin/exams/delete/<int:exam_pk>", methods=["POST"])
@admin_required
def delete_exam(exam_pk):
    db = get_db()
    db.execute("DELETE FROM exams WHERE id = ?", (exam_pk,))
    db.commit()
    flash("Exam deleted.", "success")
    return redirect(url_for("exams"))


# ---------------------------------------------------------------------------
# Admin routes — questions
# ---------------------------------------------------------------------------

@app.route("/admin/questions")
@admin_required
def questions():
    db = get_db()
    all_questions = db.execute(
        """SELECT q.*, e.title AS exam_title
           FROM questions q JOIN exams e ON e.id = q.exam_id
           ORDER BY q.exam_id, q.id"""
    ).fetchall()
    return render_template("questions.html", questions=all_questions)


@app.route("/admin/questions/add", methods=["GET", "POST"])
@admin_required
def add_question():
    db = get_db()
    all_exams = db.execute("SELECT * FROM exams ORDER BY title").fetchall()

    if request.method == "POST":
        exam_id = request.form.get("exam_id")
        question_text = (request.form.get("question_text") or "").strip()
        option_a = (request.form.get("option_a") or "").strip()
        option_b = (request.form.get("option_b") or "").strip()
        option_c = (request.form.get("option_c") or "").strip()
        option_d = (request.form.get("option_d") or "").strip()
        correct_answer = request.form.get("correct_answer")

        if not all([exam_id, question_text, option_a, option_b, option_c, option_d, correct_answer]):
            flash("All fields are required.", "error")
            return redirect(url_for("add_question"))

        db.execute(
            """INSERT INTO questions
               (exam_id, question_text, option_a, option_b, option_c, option_d, correct_answer)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (exam_id, question_text, option_a, option_b, option_c, option_d, correct_answer),
        )
        db.commit()
        flash("Question added successfully.", "success")
        return redirect(url_for("questions"))

    return render_template("add_question.html", exams=all_exams)


@app.route("/admin/questions/delete/<int:question_pk>", methods=["POST"])
@admin_required
def delete_question(question_pk):
    db = get_db()
    db.execute("DELETE FROM questions WHERE id = ?", (question_pk,))
    db.commit()
    flash("Question deleted.", "success")
    return redirect(url_for("questions"))


# ---------------------------------------------------------------------------
# Admin routes — results
# ---------------------------------------------------------------------------

@app.route("/admin/results")
@admin_required
def all_results():
    db = get_db()
    results_rows = db.execute(
        """SELECT r.*, s.full_name AS student_name, s.student_id AS student_number, e.title AS exam_title
           FROM results r
           JOIN students s ON s.id = r.student_id
           JOIN exams e ON e.id = r.exam_id
           ORDER BY r.id DESC"""
    ).fetchall()
    return render_template("results.html", results=results_rows)


if __name__ == "__main__":
    app.run(debug=True)
