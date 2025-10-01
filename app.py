import os
from datetime import datetime
from typing import Dict, List

from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from database import fetch_user_by_email, fetch_user_by_id, get_connection, init_db
from diagnostics import (
    SUBJECT_QUIZZES,
    TEACHER_PROMPT,
    calculate_level,
    plan_from_level,
)
from translations import TRANSLATIONS


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "aurora-secret-key")

    init_db()

    @app.before_request
    def load_logged_in_user():
        user_id = session.get("user_id")
        if user_id is None:
            g.user = None
        else:
            row = fetch_user_by_id(user_id)
            g.user = dict(row) if row else None

    @app.context_processor
    def inject_translations():
        lang = current_language()
        dictionary = TRANSLATIONS.get(lang, TRANSLATIONS["ru"])

        def translate(key: str) -> str:
            return dictionary.get(key, key)

        return {"t": translate, "current_language": lang}

    def current_language() -> str:
        if g.get("user"):
            return g.user["language"]
        return session.get("language", "ru")

    def store_diagnostics(user_id: int, results: Dict[str, Dict[str, float]]):
        with get_connection() as conn:
            for subject, payload in results.items():
                conn.execute(
                    """
                    INSERT INTO diagnostics (user_id, subject, score, level, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        subject,
                        payload["score"],
                        payload["level"],
                        datetime.utcnow().isoformat(),
                    ),
                )

    def fetch_latest_diagnostics(user_id: int) -> Dict[str, Dict[str, float]]:
        results: Dict[str, Dict[str, float]] = {}
        with get_connection() as conn:
            cur = conn.execute(
                """
                SELECT d.subject, d.score, d.level
                FROM diagnostics d
                JOIN (
                    SELECT subject, MAX(created_at) AS created_at
                    FROM diagnostics
                    WHERE user_id = ?
                    GROUP BY subject
                ) latest ON d.subject = latest.subject AND d.created_at = latest.created_at
                WHERE d.user_id = ?
                """,
                (user_id, user_id),
            )
            for row in cur.fetchall():
                results[row["subject"]] = {"score": row["score"], "level": row["level"]}
        return results

    def generate_plan(diagnostics_snapshot: Dict[str, Dict[str, float]]) -> Dict[str, List[str]]:
        plan: Dict[str, List[str]] = {}
        for subject in SUBJECT_QUIZZES:
            if subject in diagnostics_snapshot:
                level = diagnostics_snapshot[subject]["level"]
                plan[subject] = plan_from_level(subject, level)
        return plan

    def call_ai_assistant(prompt: str, token: str, subject: str) -> str:
        if not token:
            return ""
        try:
            import openai
        except ImportError:
            return "OpenAI library is not installed. Install the 'openai' package to enable the assistant."

        openai.api_key = token
        user_message = f"Subject: {subject}\nQuestion: {prompt}" if subject else prompt
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": TEACHER_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.7,
                max_tokens=400,
            )
        except Exception as exc:  # pragma: no cover - network call
            return f"Error contacting OpenAI API: {exc}"

        choice = response.choices[0]
        return choice.message["content"].strip()

    @app.route("/")
    def home():
        if g.user:
            return redirect(url_for("dashboard"))
        return render_template("home.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").lower().strip()
            password = request.form.get("password", "")
            confirm = request.form.get("confirm_password", "")
            lang = request.form.get("language", "ru")

            if password != confirm:
                flash(TRANSLATIONS[current_language()]["register_password_mismatch"], "danger")
            elif fetch_user_by_email(email):
                flash(TRANSLATIONS[current_language()]["register_email_exists"], "danger")
            else:
                password_hash = generate_password_hash(password)
                with get_connection() as conn:
                    conn.execute(
                        "INSERT INTO users (name, email, password_hash, language) VALUES (?, ?, ?, ?)",
                        (name, email, password_hash, lang),
                    )
                session["language"] = lang
                flash(TRANSLATIONS[current_language()]["login_title"], "success")
                return redirect(url_for("login"))
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email", "").lower().strip()
            password = request.form.get("password", "")
            user = fetch_user_by_email(email)
            if user and check_password_hash(user["password_hash"], password):
                session.clear()
                session["user_id"] = user["id"]
                session["language"] = user["language"]
                return redirect(url_for("dashboard"))
            flash(TRANSLATIONS[current_language()]["invalid_login"], "danger")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash(TRANSLATIONS[current_language()]["logout_success"], "info")
        return redirect(url_for("home"))

    @app.route("/dashboard")
    def dashboard():
        if not g.user:
            return redirect(url_for("login"))
        diagnostics_snapshot = fetch_latest_diagnostics(g.user["id"])
        plan = generate_plan(diagnostics_snapshot)
        return render_template(
            "dashboard.html",
            diagnostics_snapshot=diagnostics_snapshot,
            plan=plan,
            quizzes=SUBJECT_QUIZZES,
        )

    @app.route("/diagnostics", methods=["GET", "POST"])
    def diagnostics():
        if not g.user:
            return redirect(url_for("login"))

        if request.method == "POST":
            results: Dict[str, Dict[str, float]] = {}
            for subject, quiz in SUBJECT_QUIZZES.items():
                correct = 0
                total = len(quiz["questions"])
                for idx, question in enumerate(quiz["questions"]):
                    answer = request.form.get(f"{subject}_{idx}")
                    if answer == question["answer"]:
                        correct += 1
                score = correct / total if total else 0
                level = calculate_level(score)
                results[subject] = {"score": score, "level": level}
            store_diagnostics(g.user["id"], results)
            flash(TRANSLATIONS[current_language()]["diagnostics_success"], "success")
            return redirect(url_for("dashboard"))

        return render_template("diagnostics.html", quizzes=SUBJECT_QUIZZES)

    @app.route("/assistant", methods=["GET", "POST"])
    def assistant():
        if not g.user:
            return redirect(url_for("login"))

        error = None
        history_key = f"assistant_history_{g.user['id']}"
        history = session.setdefault(history_key, [])
        token = g.user["openai_token"] if g.user else None
        if request.method == "POST":
            question = request.form.get("question", "").strip()
            subject = request.form.get("subject", "")
            if not token:
                error = TRANSLATIONS[current_language()]["assistant_missing_token"]
            elif question:
                response = call_ai_assistant(question, token, subject)
                if response.startswith("Error") or "not installed" in response:
                    error = response
                else:
                    history.append({"question": question, "answer": response, "subject": subject})
                    session.modified = True
        return render_template(
            "assistant.html",
            history=history,
            error=error,
            quizzes=SUBJECT_QUIZZES,
        )

    @app.route("/settings", methods=["GET", "POST"])
    def settings():
        if not g.user:
            return redirect(url_for("login"))

        current = TRANSLATIONS[current_language()]
        if request.method == "POST":
            language = request.form.get("language", g.user["language"])
            token = request.form.get("openai_token") or None
            with get_connection() as conn:
                conn.execute(
                    "UPDATE users SET language = ?, openai_token = ? WHERE id = ?",
                    (language, token, g.user["id"]),
                )
            session["language"] = language
            flash(current["settings_saved"], "success")
            return redirect(url_for("settings"))

        return render_template("settings.html")

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
