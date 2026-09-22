# Basic CBT Platform — Prototype

A working demo of a Computer-Based Test (CBT) platform, built with Flask,
SQLite, Jinja2, HTML/CSS and vanilla JavaScript. Intended as a client-facing
prototype before scoping a full project.

## 1. Requirements

- Python 3.9+
- pip

## 2. Installation

```bash
# from inside the cbt_platform folder
pip install -r requirements.txt
```

## 3. Database setup

Run this once to create `database.db` with the required tables and demo data:

```bash
python init_db.py
```

You can re-run it any time to reset the database back to the demo data
(it drops and recreates all tables).

## 4. Run the application

```bash
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

## 5. Demo login credentials

**Students**

| Username    | Password    | Name          |
|-------------|-------------|---------------|
| student001  | student123  | John Doe      |
| student002  | student123  | Amina Yusuf   |
| student003  | student123  | Chidi Okafor  |

**Admin**

| Username | Password  |
|----------|-----------|
| admin    | admin123  |

A demo exam — **Mathematics Mock Test** (30 minutes, 12 questions) — is
preloaded so you can test the student flow immediately.

## 6. Testing the student flow

1. Go to `/login`, select **Student**, sign in with `student001` / `student123`.
2. On the dashboard, click **Start exam** on the Mathematics Mock Test card.
3. Read the instructions, click **Start exam**.
4. Answer questions, using **Next**/**Previous** or the question navigator
   on the right. Answered questions are highlighted green.
5. Click **Submit Exam** (or let the timer run out — it auto-submits).
6. Confirm the result page shows score, percentage, correct/wrong counts.

## 7. Testing the admin flow

1. Go to `/login`, select **Admin**, sign in with `admin` / `admin123`.
2. **Dashboard** — check the student/exam/question totals and recent results.
3. **Exams** → **Create exam** — add a new exam (title, description, duration).
4. **Questions** → **Add question** — add a question to that exam, with four
   options and the correct answer.
5. **Students** → **Add student** — create a new student login.
6. Log out, log back in as the new student, and confirm the new exam
   appears on their dashboard and can be taken.
7. Back in the admin, check **Results** to see the new attempt listed.
8. Try deleting a question, an exam, and a student from their respective
   pages (each asks for confirmation first).

## 8. Project structure

```
app.py                  Flask application and all routes
init_db.py               Creates database.db and loads demo data
requirements.txt
database.db               (created by init_db.py — not included)

templates/
  base.html                Shared HTML shell
  login.html                Login page (student/admin toggle)
  student_dashboard.html
  instructions.html
  exam.html                  CBT exam interface
  result.html
  admin_dashboard.html
  students.html / add_student.html
  exams.html / add_exam.html
  questions.html / add_question.html
  results.html
  _topbar_student.html       Shared partial
  _admin_shell_open.html     Shared partial (top bar + side nav)

static/
  css/style.css              All styling
  js/exam.js                 Timer, question navigation, submit logic
```

## 9. Notes on scope

This is the **Basic CBT** version only, as scoped for the demo:

- No payments, SMS, AI, mobile app, facial recognition, multi-tenant
  support, bulk import, email automation, or cloud infrastructure.
- Security is prototype-level (hashed passwords, session-based login,
  route protection, input validation) — not hardened for production or
  advanced exam-security scenarios (e.g. it doesn't prevent tab-switching
  or screen recording).
- Single exam type: multiple-choice, auto-marked.

These can all be scoped as follow-on work once the client has reviewed
this prototype.
