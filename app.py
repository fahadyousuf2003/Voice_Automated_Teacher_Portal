import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from werkzeug.utils import secure_filename
from sqlalchemy import or_

from config import Config
from models import db, Teacher, Course, Attendance, Assignment, Submission, Announcement
from ai_services import (
    fetch_teacher_data, summarize_lecture
)

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

# Create necessary directories
if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])

assignments_folder = os.path.join(app.config["UPLOAD_FOLDER"], "assignments")
if not os.path.exists(assignments_folder):
    os.makedirs(assignments_folder)

@login_manager.user_loader
def load_user(user_id):
    return Teacher.query.get(int(user_id))

# Helper function to get data (JSON or form)
def get_request_data():
    return request.get_json() if request.is_json else request.form

# --------------------------
# Authentication Routes
# --------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        teacher = Teacher.query.filter_by(username=username).first()
        if teacher and teacher.check_password(password):
            login_user(teacher)
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials. Please try again.", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        existing_teacher = Teacher.query.filter(
            or_(Teacher.username == username, Teacher.email == email)
        ).first()
        if existing_teacher:
            flash("A teacher with that username or email already exists.", "danger")
            return redirect(url_for("register"))
        teacher = Teacher(name=name, username=username, email=email)
        teacher.set_password(password)
        db.session.add(teacher)
        db.session.commit()
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

# --------------------------
# Dashboard
# --------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    courses = current_user.courses
    return render_template("dashboard.html", teacher=current_user, courses=courses)

# --------------------------
# Attendance Management
# --------------------------
@app.route("/mark-attendance", methods=["GET", "POST"])
@login_required
def mark_attendance():
    if request.method == "GET":
        # Render the attendance marking page
        courses = current_user.courses  # assuming your teacher has related courses
        return render_template("mark_attendance.html", courses=courses)
    
    # POST: Process the form submission via AJAX or standard form submission
    data = get_request_data()
    course_id = data.get("course_id")
    date_str = data.get("date")
    status = data.get("status")
    
    if not course_id or not date_str or not status:
        return jsonify({"success": False, "error": "All fields are required"}), 400
    
    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    new_record = Attendance(course_id=course_id, date=date_obj, status=status)
    db.session.add(new_record)
    db.session.commit()
    
    return jsonify({"success": True})

# --------------------------
# Summarize Lecture
# --------------------------
@app.route("/summarize-lecture", methods=["POST"])
@login_required
def summarize_lecture_route():
    """
    Summarizes the lecture transcript using the GROQ LLAMA.
    """
    data = request.get_json()
    transcript = data.get("transcript", "")
    if not transcript.strip():
        return jsonify({"summary": "No transcript provided."})
    summary = summarize_lecture(transcript)
    return jsonify({"summary": summary})


# --------------------------
# Chatbot AJAX Endpoint (for POST queries)
# --------------------------
@app.route("/chatbot-query", methods=["POST"])
@login_required
def chatbot_query():
    """
    Endpoint to handle chatbot queries using the Groq LLAMA model.
    """
    try:
        data = request.get_json()
        question = data.get("question", "")

        if not question:
            return jsonify({"success": False, "error": "No question provided."}), 400

        # Use the updated fetch_teacher_data function
        response = fetch_teacher_data(question)
        return jsonify({"success": True, "response": response})

    except Exception as e:
        return jsonify({"success": False, "error": f"Internal server error: {str(e)}"}), 500
    
# --------------------------
# Chatbot Page (GET)
# --------------------------
@app.route("/chatbot", methods=["GET"])
@login_required
def chatbot():
    # Render the chatbot interface page
    return render_template("chatbot.html")

# --------------------------
# Assignment Management
# --------------------------
@app.route("/upload-assignment", methods=["GET", "POST"])
@login_required
def upload_assignment():
    if request.method == "GET":
        # Render the assignment upload form.
        courses = current_user.courses  # assuming your teacher has related courses
        return render_template("upload_assignment.html", courses=courses)
    
    # POST: Process the assignment upload
    if "assignment_file" not in request.files:
        return jsonify({"success": False, "error": "No file selected"}), 400
    file = request.files["assignment_file"]
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)
    course_id = request.form.get("course_id")
    title = request.form.get("title")
    description = request.form.get("description")
    due_date_str = request.form.get("due_date")
    try:
        due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date() if due_date_str else None
    except ValueError:
        return jsonify({"success": False, "error": "Invalid date format"}), 400
    new_assignment = Assignment(
        course_id=course_id,
        title=title,
        description=description,
        upload_date=datetime.now(),
        due_date=due_date,
        file_path=file_path
    )
    db.session.add(new_assignment)
    db.session.commit()
    return jsonify({"success": True})

@app.route("/voice-upload-assignment", methods=["POST"])
@login_required
def voice_upload_assignment():
    data = request.get_json()
    file_name = data.get("file_name")
    course_id = data.get("course_id")
    title = data.get("title")
    description = data.get("description")
    due_date_str = data.get("due_date")

    if not file_name or not course_id or not title:
        return jsonify({"success": False, "error": "Missing required fields."}), 400

    # Define the assignments folder
    assignments_folder = os.path.join(app.config["UPLOAD_FOLDER"], "assignments")
    # Secure the file name to avoid security issues
    secure_file_name = secure_filename(file_name)
    file_path = os.path.join(assignments_folder, secure_file_name)

    if not os.path.exists(file_path):
        return jsonify({"success": False, "error": f"File '{secure_file_name}' not found in assignments folder. Please check if the file exists at '{assignments_folder}'."}), 404

    try:
        due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date() if due_date_str else None
    except ValueError:
        return jsonify({"success": False, "error": "Invalid date format."}), 400

    new_assignment = Assignment(
        course_id=course_id,
        title=title,
        description=description,
        upload_date=datetime.now(),
        due_date=due_date,
        file_path=file_path
    )
    db.session.add(new_assignment)
    db.session.commit()
    return jsonify({"success": True})

# --------------------------
# List Available Assignments
# --------------------------
@app.route("/available-assignments", methods=["GET"])
@login_required
def list_available_assignments():
    assignments_folder = os.path.join(app.config["UPLOAD_FOLDER"], "assignments")
    if not os.path.exists(assignments_folder):
        return jsonify({"success": False, "error": "Assignments folder does not exist"}), 404
    
    files = [f for f in os.listdir(assignments_folder) 
             if os.path.isfile(os.path.join(assignments_folder, f))]
    
    return jsonify({"success": True, "files": files})

# --------------------------
# Grade Assignment
# --------------------------
@app.route("/assign-grade", methods=["GET", "POST"])
@login_required
def assign_grade():
    if request.method == "GET":
        # Render the grade assignment form.
        submissions = Submission.query.all()  # Optionally filter by teacher's courses
        return render_template("assign_grade.html", submissions=submissions)
    
    # POST: Process grade assignment
    data = get_request_data()
    submission_id = data.get("submission_id")
    grade = data.get("grade")
    feedback = data.get("feedback")
    if not submission_id or not grade:
        return jsonify({"success": False, "error": "Submission ID and grade are required"}), 400
    submission = Submission.query.get(submission_id)
    if not submission:
        return jsonify({"success": False, "error": "Submission not found"}), 404
    submission.grade = grade
    submission.feedback = feedback
    db.session.commit()
    return jsonify({"success": True})

# --------------------------
# Announcements
# --------------------------
@app.route("/announcements", methods=["GET", "POST"])
@login_required
def announcements():
    if request.method == "POST":
        data = get_request_data()
        course_id = data.get("course_id")
        message = data.get("message")
        if not course_id or not message:
            return jsonify({"success": False, "error": "Missing course ID or message"}), 400
        new_announcement = Announcement(
            course_id=course_id, 
            message=message,
            created_date=datetime.now()
        )
        db.session.add(new_announcement)
        db.session.commit()
        course = Course.query.get(course_id)
        return jsonify({
            "success": True,
            "course_name": course.course_name,
            "message": message,
            "created_date": new_announcement.created_date.strftime('%Y-%m-%d %H:%M')
        })
    announcements = Announcement.query.order_by(Announcement.created_date.desc()).all()
    return render_template("announcements.html", announcements=announcements, courses=current_user.courses)

# --------------------------
# Schedule Class
# --------------------------
@app.route("/schedule", methods=["GET", "POST"])
@login_required
def schedule():
    if request.method == "GET":
        courses = current_user.courses
        return render_template("schedule.html", courses=courses)
    
    # POST: Process scheduling data.
    data = get_request_data()
    course_id = data.get("course_id")
    date_time_str = data.get("date_time")
    if not course_id or not date_time_str:
        return jsonify({"success": False, "error": "Course and date/time are required"}), 400
    date_time_obj = datetime.strptime(date_time_str, "%Y-%m-%dT%H:%M")
    flash(f"Class scheduled for {date_time_obj.strftime('%Y-%m-%d %H:%M')}", "success")
    return jsonify({"success": True})

# --------------------------
# Virtual Classroom
# --------------------------
@app.route("/virtual_classroom")
@login_required
def virtual_classroom():
    return render_template("virtual_classroom.html")

# --------------------------
# Lecture Capture
# --------------------------
@app.route("/lecture_capture")
@login_required
def lecture_capture():
    return render_template("lecture_capture.html")


# --------------------------
# File Upload Configuration
# --------------------------
if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])

if __name__ == "__main__":
    app.run(debug=True)