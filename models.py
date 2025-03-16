from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# --------------------------
# Teacher Model (User Authentication)
# --------------------------
class Teacher(UserMixin, db.Model):
    __tablename__ = "teachers"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)  # This field now stores plain text passwords
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Relationship: A teacher can have multiple courses
    courses = db.relationship("Course", backref="teacher", lazy=True)

    def set_password(self, password):
        # Store the password as plain text
        self.password_hash = password

    def check_password(self, password):
        # Compare the plain text passwords
        return self.password_hash == password

# --------------------------
# Course Model
# --------------------------
class Course(db.Model):
    __tablename__ = "courses"
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(120), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"), nullable=False)
    assignments = db.relationship("Assignment", backref="course", lazy=True)
    attendance_records = db.relationship("Attendance", backref="course", lazy=True)
    announcements = db.relationship("Announcement", backref="course", lazy=True)


# --------------------------
# Attendance Model
# --------------------------
class Attendance(db.Model):
    __tablename__ = "attendance"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum("Present", "Absent", "Late"), nullable=False)

# --------------------------
# Assignment Model
# --------------------------
class Assignment(db.Model):
    __tablename__ = "assignments"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    upload_date = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    due_date = db.Column(db.Date)
    file_path = db.Column(db.String(255), nullable=False)

    # Relationship: An assignment can have multiple submissions
    submissions = db.relationship("Submission", backref="assignment", lazy=True)

# --------------------------
# Submission Model (Student Assignment Submissions)
# --------------------------
class Submission(db.Model):
    __tablename__ = "submissions"
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignments.id"), nullable=False)
    student_id = db.Column(db.String(64), nullable=False)
    submitted_date = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    file_path = db.Column(db.String(255))
    grade = db.Column(db.String(10))
    feedback = db.Column(db.Text)

# --------------------------
# Announcement Model
# --------------------------
class Announcement(db.Model):
    __tablename__ = "announcements"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_date = db.Column(db.DateTime, server_default=db.func.current_timestamp())
