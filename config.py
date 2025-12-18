# config.py
import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

BASE_UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")

PROGRAMS_UPLOAD_FOLDER = os.path.join(BASE_UPLOAD_FOLDER, "programs")
CHILDREN_UPLOAD_FOLDER = os.path.join(BASE_UPLOAD_FOLDER, "children")

os.makedirs(PROGRAMS_UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CHILDREN_UPLOAD_FOLDER, exist_ok=True)

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR,'cm_dev.sqlite')}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-secret-dev")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    BASE_UPLOAD_FOLDER = BASE_UPLOAD_FOLDER
    PROGRAMS_UPLOAD_FOLDER = PROGRAMS_UPLOAD_FOLDER
    CHILDREN_UPLOAD_FOLDER = CHILDREN_UPLOAD_FOLDER
    

# UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads", "programs")
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # other config values if needed


