import csv
import io
import os
import uuid
from datetime import datetime
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, send_file, send_from_directory, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from database import DB_PATH, get_connection, init_db

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "achievex-hackathon-demo-secret")
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        return func(*args, **kwargs)

    return wrapper


def role_required(*roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not session.get("user_id"):
                flash("Please log in to continue.", "error")
                return redirect(url_for("login"))
            user = get_user_by_id(session["user_id"])
            if user is None or user["role"] not in roles:
                flash("You do not have access to this page.", "error")
                return redirect(url_for("dashboard"))
            return func(*args, **kwargs)

        return wrapper

    return decorator


def get_user_by_id(user_id):
    with get_connection() as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def get_achievement_by_id(achievement_id):
    with get_connection() as conn:
        return conn.execute(
            "SELECT a.*, u.name AS owner_name, u.email, u.role AS owner_role, u.department AS owner_department, u.academic_year AS owner_academic_year FROM achievements a JOIN users u ON a.user_id = u.id WHERE a.id = ?",
            (achievement_id,),
        ).fetchone()


def get_user_achievements(user_id):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM achievements WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()


def get_recent_submissions(limit=5):
    with get_connection() as conn:
        return conn.execute(
            "SELECT a.*, u.name AS person_name, u.role FROM achievements a JOIN users u ON a.user_id = u.id ORDER BY a.created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()


def normalize_status(value):
    return (value or "").strip().upper()


def allowed_file(filename):
    if not filename:
        return False
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload(file, prefix):
    if not file or file.filename == "":
        return None

    if not allowed_file(file.filename):
        raise ValueError("Only PDF, PNG, JPG, and JPEG files are allowed.")

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > app.config["MAX_CONTENT_LENGTH"]:
        raise ValueError("File is too large. Please upload a file under 5MB.")

    ext = os.path.splitext(secure_filename(file.filename))[1].lower()
    unique_name = f"{prefix}_{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
    file.save(save_path)
    return unique_name


def get_dashboard_stats_for_user(user_id):
    with get_connection() as conn:
        stats = conn.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'VERIFIED' THEN 1 ELSE 0 END) AS verified,
                SUM(CASE WHEN status = 'PENDING' THEN 1 ELSE 0 END) AS pending,
                SUM(CASE WHEN status = 'REJECTED' THEN 1 ELSE 0 END) AS rejected
            FROM achievements WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()
        return {
            "total": stats["total"] or 0,
            "verified": stats["verified"] or 0,
            "pending": stats["pending"] or 0,
            "rejected": stats["rejected"] or 0,
        }


def get_admin_dashboard_stats():
    with get_connection() as conn:
        totals = conn.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'VERIFIED' THEN 1 ELSE 0 END) AS verified,
                SUM(CASE WHEN status = 'PENDING' THEN 1 ELSE 0 END) AS pending,
                SUM(CASE WHEN status = 'REJECTED' THEN 1 ELSE 0 END) AS rejected,
                SUM(CASE WHEN u.role = 'STUDENT' THEN 1 ELSE 0 END) AS students,
                SUM(CASE WHEN u.role = 'FACULTY' THEN 1 ELSE 0 END) AS faculty
            FROM achievements a
            LEFT JOIN users u ON a.user_id = u.id
            """
        ).fetchone()

        student_count = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'STUDENT'").fetchone()[0]
        faculty_count = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'FACULTY'").fetchone()[0]

        return {
            "total": totals["total"] or 0,
            "verified": totals["verified"] or 0,
            "pending": totals["pending"] or 0,
            "rejected": totals["rejected"] or 0,
            "students": student_count,
            "faculty": faculty_count,
        }


@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        with get_connection() as conn:
            user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            flash("Login successful.", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid credentials. Please try again.", "error")
        return render_template("login.html")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    user = get_user_by_id(session["user_id"])
    if user["role"] == "STUDENT":
        stats = get_dashboard_stats_for_user(user["id"])
        recent = get_user_achievements(user["id"])[:5]
        return render_template("dashboard.html", user=user, stats=stats, recent=recent, page_title="Student Dashboard")

    if user["role"] == "FACULTY":
        stats = get_dashboard_stats_for_user(user["id"])
        recent = get_user_achievements(user["id"])[:5]
        return render_template("dashboard.html", user=user, stats=stats, recent=recent, page_title="Faculty Dashboard")

    if user["role"] == "VERIFIER":
        stats = get_admin_dashboard_stats()
        recent = get_recent_submissions(5)
        pending = get_recent_submissions(6)
        pending = [item for item in pending if item["status"] in ("PENDING", "REJECTED")]
        return render_template("dashboard.html", user=user, stats=stats, recent=recent, pending=pending, page_title="Verification Dashboard")

    return redirect(url_for("login"))


@app.route("/submit_achievement", methods=["GET", "POST"])
@login_required
def submit_achievement():
    user = get_user_by_id(session["user_id"])
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        category = (request.form.get("category") or "").strip()
        achievement_type = (request.form.get("achievement_type") or "").strip() or "Achievement"
        organization = (request.form.get("organization") or "").strip()
        achievement_date = request.form.get("achievement_date")
        position = (request.form.get("position") or "").strip()
        description = (request.form.get("description") or "").strip()
        department = (request.form.get("department") or "").strip() or user["department"]
        academic_year = (request.form.get("academic_year") or "").strip() or user["academic_year"]

        if not all([title, category, organization, achievement_date, description]):
            flash("Please complete all required fields before submitting.", "error")
            return render_template("submit_achievement.html", user=user)

        try:
            certificate_file = save_upload(request.files.get("certificate_file"), "cert")
            evidence_file = save_upload(request.files.get("evidence_file"), "evidence")
        except ValueError as exc:
            flash(str(exc), "error")
            return render_template("submit_achievement.html", user=user)

        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO achievements (
                    user_id, title, category, achievement_type, organization, achievement_date,
                    position, description, department, academic_year, certificate_filename,
                    evidence_filename, status, is_featured, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', 0, ?, ?)
                """,
                (
                    user["id"],
                    title,
                    category,
                    achievement_type,
                    organization,
                    achievement_date,
                    position,
                    description,
                    department,
                    academic_year,
                    certificate_file,
                    evidence_file,
                    now,
                    now,
                ),
            )
            conn.commit()

        flash("Achievement submitted successfully and is now pending verification.", "success")
        return redirect(url_for("my_achievements"))

    return render_template("submit_achievement.html", user=user)


@app.route("/my_achievements")
@login_required
def my_achievements():
    user = get_user_by_id(session["user_id"])
    achievements = get_user_achievements(user["id"])
    return render_template("my_achievements.html", user=user, achievements=achievements)


@app.route("/achievement/<int:achievement_id>")
@login_required
def achievement_detail(achievement_id):
    user = get_user_by_id(session["user_id"])
    achievement = get_achievement_by_id(achievement_id)
    if not achievement:
        flash("Achievement not found.", "error")
        return redirect(url_for("dashboard"))

    if user["role"] not in ("VERIFIER", "STUDENT", "FACULTY"):
        flash("Access denied.", "error")
        return redirect(url_for("dashboard"))

    if user["role"] != "VERIFIER" and achievement["user_id"] != user["id"]:
        flash("You can only view your own achievement records.", "error")
        return redirect(url_for("my_achievements"))

    with get_connection() as conn:
        verifications = conn.execute(
            "SELECT v.*, u.name AS verifier_name FROM verifications v LEFT JOIN users u ON u.id = v.verifier_id WHERE v.achievement_id = ? ORDER BY v.id DESC",
            (achievement_id,),
        ).fetchall()

    return render_template("achievement_detail.html", user=user, achievement=achievement, verifications=verifications)


@app.route("/achievement/<int:achievement_id>/edit", methods=["GET", "POST"])
@login_required
def edit_achievement(achievement_id):
    user = get_user_by_id(session["user_id"])
    achievement = get_achievement_by_id(achievement_id)

    if not achievement or achievement["user_id"] != user["id"]:
        flash("You can only edit your own achievements.", "error")
        return redirect(url_for("my_achievements"))

    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        category = (request.form.get("category") or "").strip()
        achievement_type = (request.form.get("achievement_type") or "").strip() or (achievement["achievement_type"] or "Achievement")
        organization = (request.form.get("organization") or "").strip()
        achievement_date = request.form.get("achievement_date")
        position = (request.form.get("position") or "").strip()
        description = (request.form.get("description") or "").strip()
        department = (request.form.get("department") or "").strip() or achievement["department"]
        academic_year = (request.form.get("academic_year") or "").strip() or achievement["academic_year"]

        if not all([title, category, organization, achievement_date, description]):
            flash("Please fill in all required fields before resubmitting.", "error")
            return render_template("submit_achievement.html", user=user, achievement=achievement)

        try:
            certificate_file = save_upload(request.files.get("certificate_file"), "cert")
            evidence_file = save_upload(request.files.get("evidence_file"), "evidence")
        except ValueError as exc:
            flash(str(exc), "error")
            return render_template("submit_achievement.html", user=user, achievement=achievement)

        new_certificate = certificate_file or achievement["certificate_filename"]
        new_evidence = evidence_file or achievement["evidence_filename"]

        with get_connection() as conn:
            conn.execute(
                """
                UPDATE achievements
                SET title = ?, category = ?, achievement_type = ?, organization = ?, achievement_date = ?,
                    position = ?, description = ?, department = ?, academic_year = ?,
                    certificate_filename = ?, evidence_filename = ?, status = 'PENDING', updated_at = ?
                WHERE id = ?
                """,
                (
                    title,
                    category,
                    achievement_type,
                    organization,
                    achievement_date,
                    position,
                    description,
                    department,
                    academic_year,
                    new_certificate,
                    new_evidence,
                    datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    achievement_id,
                ),
            )
            conn.commit()

        flash("Achievement updated and resubmitted for review.", "success")
        return redirect(url_for("my_achievements"))

    return render_template("submit_achievement.html", user=user, achievement=achievement, edit_mode=True)


@app.route("/verification")
@login_required
@role_required("VERIFIER")
def verification():
    with get_connection() as conn:
        pending = conn.execute(
            """
            SELECT a.*, u.name AS person_name, u.role AS person_role
            FROM achievements a
            JOIN users u ON a.user_id = u.id
            WHERE a.status IN ('PENDING', 'REJECTED')
            ORDER BY a.created_at DESC
            """
        ).fetchall()

    user = get_user_by_id(session["user_id"])
    return render_template("verification.html", user=user, achievements=pending)


@app.route("/verification/<int:achievement_id>", methods=["GET", "POST"])
@login_required
@role_required("VERIFIER")
def verify_achievement(achievement_id):
    user = get_user_by_id(session["user_id"])
    achievement = get_achievement_by_id(achievement_id)
    if not achievement:
        flash("Achievement not found.", "error")
        return redirect(url_for("verification"))

    if request.method == "POST":
        decision = request.form.get("decision")
        remarks = (request.form.get("remarks") or "").strip()
        if decision not in ("APPROVE", "REJECT"):
            flash("Please choose a valid decision.", "error")
            return redirect(url_for("verify_achievement", achievement_id=achievement_id))

        status_value = "VERIFIED" if decision == "APPROVE" else "REJECTED"
        verified_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        with get_connection() as conn:
            conn.execute(
                "UPDATE achievements SET status = ?, updated_at = ? WHERE id = ?",
                (status_value, verified_at, achievement_id),
            )
            conn.execute(
                "INSERT INTO verifications (achievement_id, verifier_id, status, remarks, verified_at) VALUES (?, ?, ?, ?, ?)",
                (achievement_id, user["id"], "APPROVED" if decision == "APPROVE" else "REJECTED", remarks or ("Approved after reviewing documents." if decision == "APPROVE" else "Rejected due to incomplete or invalid documentation."), verified_at),
            )
            conn.commit()

        if decision == "APPROVE":
            flash("Achievement approved and published to the public gallery.", "success")
        else:
            flash("Achievement rejected. The owner will be able to resubmit after correcting the issue.", "error")
        return redirect(url_for("verification"))

    return render_template("achievement_detail.html", user=user, achievement=achievement, verification_mode=True)


@app.route("/gallery")
def gallery():
    query = (request.args.get("q") or "").strip()
    category = request.args.get("category")
    department = request.args.get("department")
    academic_year = request.args.get("academic_year")
    achievement_type = request.args.get("achievement_type")

    with get_connection() as conn:
        sql = """
            SELECT a.*, u.name, u.role, u.department AS user_department, u.academic_year AS user_academic_year
            FROM achievements a
            JOIN users u ON a.user_id = u.id
            WHERE a.status = 'VERIFIED'
        """
        params = []
        if query:
            sql += " AND (a.title LIKE ? OR a.organization LIKE ? OR u.name LIKE ? OR a.description LIKE ?)"
            like_query = f"%{query}%"
            params.extend([like_query, like_query, like_query, like_query])
        if category:
            sql += " AND a.category = ?"
            params.append(category)
        if department:
            sql += " AND a.department = ?"
            params.append(department)
        if academic_year:
            sql += " AND a.academic_year = ?"
            params.append(academic_year)
        if achievement_type:
            sql += " AND a.achievement_type = ?"
            params.append(achievement_type)
        sql += " ORDER BY a.is_featured DESC, a.achievement_date DESC"
        achievements = conn.execute(sql, params).fetchall()

        filters = {
            "categories": [row[0] for row in conn.execute("SELECT name FROM categories ORDER BY name").fetchall()],
            "departments": [row[0] for row in conn.execute("SELECT name FROM departments ORDER BY name").fetchall()],
            "years": [row[0] for row in conn.execute("SELECT DISTINCT academic_year FROM achievements WHERE academic_year IS NOT NULL ORDER BY academic_year DESC").fetchall()],
            "achievement_types": [row[0] for row in conn.execute("SELECT DISTINCT achievement_type FROM achievements WHERE achievement_type IS NOT NULL AND achievement_type != '' ORDER BY achievement_type").fetchall()],
        }

    user = get_user_by_id(session.get("user_id")) if session.get("user_id") else None
    return render_template("gallery.html", user=user, achievements=achievements, filters=filters, query=query, category=category, department=department, academic_year=academic_year, achievement_type=achievement_type)


@app.route("/analytics")
@login_required
@role_required("VERIFIER")
def analytics():
    user = get_user_by_id(session["user_id"])
    with get_connection() as conn:
        total_achievements = conn.execute("SELECT COUNT(*) FROM achievements").fetchone()[0]
        verified = conn.execute("SELECT COUNT(*) FROM achievements WHERE status = 'VERIFIED'").fetchone()[0]
        pending = conn.execute("SELECT COUNT(*) FROM achievements WHERE status = 'PENDING'").fetchone()[0]
        rejected = conn.execute("SELECT COUNT(*) FROM achievements WHERE status = 'REJECTED'").fetchone()[0]
        student_achievements = conn.execute("SELECT COUNT(*) FROM achievements a JOIN users u ON a.user_id = u.id WHERE u.role = 'STUDENT'").fetchone()[0]
        faculty_achievements = conn.execute("SELECT COUNT(*) FROM achievements a JOIN users u ON a.user_id = u.id WHERE u.role = 'FACULTY'").fetchone()[0]

        category_distribution = [dict(row) for row in conn.execute("SELECT category, COUNT(*) AS value FROM achievements GROUP BY category ORDER BY value DESC").fetchall()]
        department_distribution = [dict(row) for row in conn.execute("SELECT department, COUNT(*) AS value FROM achievements GROUP BY department ORDER BY value DESC").fetchall()]
        year_distribution = [dict(row) for row in conn.execute("SELECT academic_year, COUNT(*) AS value FROM achievements WHERE academic_year IS NOT NULL GROUP BY academic_year ORDER BY academic_year DESC").fetchall()]
        status_distribution = [
            {"label": "Verified", "value": verified},
            {"label": "Pending", "value": pending},
            {"label": "Rejected", "value": rejected},
        ]
        role_distribution = [
            {"label": "Students", "value": student_achievements},
            {"label": "Faculty", "value": faculty_achievements},
        ]

        most_common_category = category_distribution[0]["category"] if category_distribution else "N/A"
        top_departments = [row["department"] for row in department_distribution[:3]] if department_distribution else []
        verification_percentage = round((verified / total_achievements * 100), 2) if total_achievements else 0

    return render_template(
        "analytics.html",
        user=user,
        total_achievements=total_achievements,
        verified=verified,
        pending=pending,
        rejected=rejected,
        student_achievements=student_achievements,
        faculty_achievements=faculty_achievements,
        category_distribution=category_distribution,
        department_distribution=department_distribution,
        year_distribution=year_distribution,
        status_distribution=status_distribution,
        role_distribution=role_distribution,
        most_common_category=most_common_category,
        top_departments=top_departments,
        verification_percentage=verification_percentage,
    )


@app.route("/reports")
@login_required
@role_required("VERIFIER")
def reports():
    user = get_user_by_id(session["user_id"])
    with get_connection() as conn:
        people = conn.execute("SELECT id, name FROM users ORDER BY name").fetchall()
        departments = conn.execute("SELECT name FROM departments ORDER BY name").fetchall()
        categories = conn.execute("SELECT name FROM categories ORDER BY name").fetchall()
        years = conn.execute("SELECT DISTINCT academic_year FROM achievements WHERE academic_year IS NOT NULL ORDER BY academic_year DESC").fetchall()

    filters = {
        "people": people,
        "departments": [row[0] for row in departments],
        "categories": [row[0] for row in categories],
        "years": [row[0] for row in years],
    }

    selected_person = request.args.get("person")
    selected_department = request.args.get("department")
    selected_category = request.args.get("category")
    selected_year = request.args.get("academic_year")
    selected_status = request.args.get("status")
    selected_role = request.args.get("role")

    sql = """
        SELECT a.id, a.title, a.category, a.department, a.achievement_date, a.status,
               u.name AS person_name, u.role AS person_role
        FROM achievements a
        JOIN users u ON a.user_id = u.id
        WHERE 1 = 1
    """
    params = []
    if selected_person:
        sql += " AND a.user_id = ?"
        params.append(selected_person)
    if selected_department:
        sql += " AND a.department = ?"
        params.append(selected_department)
    if selected_category:
        sql += " AND a.category = ?"
        params.append(selected_category)
    if selected_year:
        sql += " AND a.academic_year = ?"
        params.append(selected_year)
    if selected_status:
        sql += " AND a.status = ?"
        params.append(selected_status)
    if selected_role:
        sql += " AND u.role = ?"
        params.append(selected_role)
    sql += " ORDER BY a.created_at DESC"

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()

    return render_template(
        "reports.html",
        user=user,
        rows=rows,
        filters=filters,
        selected_person=selected_person,
        selected_department=selected_department,
        selected_category=selected_category,
        selected_year=selected_year,
        selected_status=selected_status,
        selected_role=selected_role,
    )


@app.route("/reports/export.csv")
@login_required
@role_required("VERIFIER")
def export_reports_csv():
    selected_person = request.args.get("person")
    selected_department = request.args.get("department")
    selected_category = request.args.get("category")
    selected_year = request.args.get("academic_year")
    selected_status = request.args.get("status")
    selected_role = request.args.get("role")

    sql = """
        SELECT a.title, u.name AS person_name, u.role AS person_role, a.department, a.category,
               a.achievement_date, a.status
        FROM achievements a
        JOIN users u ON a.user_id = u.id
        WHERE 1 = 1
    """
    params = []
    if selected_person:
        sql += " AND a.user_id = ?"
        params.append(selected_person)
    if selected_department:
        sql += " AND a.department = ?"
        params.append(selected_department)
    if selected_category:
        sql += " AND a.category = ?"
        params.append(selected_category)
    if selected_year:
        sql += " AND a.academic_year = ?"
        params.append(selected_year)
    if selected_status:
        sql += " AND a.status = ?"
        params.append(selected_status)
    if selected_role:
        sql += " AND u.role = ?"
        params.append(selected_role)
    sql += " ORDER BY a.created_at DESC"

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Achievement Title", "Person", "Role", "Department", "Category", "Date", "Status"])
    for row in rows:
        writer.writerow([row["title"], row["person_name"], row["person_role"], row["department"], row["category"], row["achievement_date"], row["status"]])

    response = send_file(io.BytesIO(output.getvalue().encode("utf-8")), mimetype="text/csv", as_attachment=True, download_name="achievex_reports.csv")
    return response


@app.route("/profile")
@login_required
def profile():
    user = get_user_by_id(session["user_id"])
    if user["role"] == "VERIFIER":
        return redirect(url_for("profiles"))

    stats = get_dashboard_stats_for_user(user["id"])
    with get_connection() as conn:
        categories = conn.execute("SELECT DISTINCT category FROM achievements WHERE user_id = ? ORDER BY category", (user["id"],)).fetchall()
        achievements = conn.execute("SELECT * FROM achievements WHERE user_id = ? ORDER BY created_at DESC", (user["id"],)).fetchall()

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        categories=[row[0] for row in categories],
        achievements=achievements,
        page_title="My Profile",
    )


@app.route("/profiles", methods=["GET", "POST"])
@login_required
@role_required("VERIFIER")
def profiles():
    user = get_user_by_id(session["user_id"])

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        role = (request.form.get("role") or "").strip().upper()
        department = (request.form.get("department") or "").strip()
        academic_year = (request.form.get("academic_year") or "").strip()

        if not all([name, email, password, role]):
            flash("Name, email, password, and role are required.", "error")
            return redirect(url_for("profiles"))

        if role not in {"STUDENT", "FACULTY", "VERIFIER"}:
            flash("Role must be Student, Faculty, or Verifier.", "error")
            return redirect(url_for("profiles"))

        with get_connection() as conn:
            existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
            if existing:
                flash("A member with this email already exists.", "error")
                return redirect(url_for("profiles"))

            conn.execute(
                "INSERT INTO users (name, email, password_hash, role, department, academic_year) VALUES (?, ?, ?, ?, ?, ?)",
                (name, email, generate_password_hash(password), role, department or None, academic_year or None),
            )

        flash(f"{name} was added as a {role.title()} member.", "success")
        return redirect(url_for("profiles"))

    with get_connection() as conn:
        profiles = conn.execute(
            """
            SELECT u.id, u.name, u.role, u.department, u.academic_year,
                   COUNT(a.id) AS total_achievements,
                   SUM(CASE WHEN a.status = 'VERIFIED' THEN 1 ELSE 0 END) AS verified_achievements
            FROM users u
            LEFT JOIN achievements a ON a.user_id = u.id
            GROUP BY u.id
            ORDER BY u.role, u.name
            """
        ).fetchall()

    return render_template("profile.html", user=user, profiles=profiles, all_profiles=True)


@app.route("/passport")
@login_required
def passport():
    user = get_user_by_id(session["user_id"])
    if user["role"] == "VERIFIER":
        flash("Verifier profiles do not have a student passport.", "error")
        return redirect(url_for("dashboard"))

    stats = get_dashboard_stats_for_user(user["id"])
    with get_connection() as conn:
        achievements = conn.execute("SELECT * FROM achievements WHERE user_id = ? ORDER BY achievement_date DESC", (user["id"],)).fetchall()
        categories = conn.execute("SELECT DISTINCT category FROM achievements WHERE user_id = ? ORDER BY category", (user["id"],)).fetchall()

    return render_template("passport.html", user=user, stats=stats, achievements=achievements, categories=[row[0] for row in categories])


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.before_request
def ensure_database():
    init_db()


if __name__ == "__main__":
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
