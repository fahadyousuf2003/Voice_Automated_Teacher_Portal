import os

class Config:
    # --------------------------
    # Security Configuration
    # --------------------------
    SECRET_KEY = "12adafqq3e3eqff"

    # --------------------------
    # Database Configuration (MySQL)
    # --------------------------
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:@localhost/automated_teacher_portal"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --------------------------
    # File Upload Configuration
    # --------------------------
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), "uploads")
    ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "txt", "zip"}

    # Ensure the upload folder exists
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
