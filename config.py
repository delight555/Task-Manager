
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

DATABASE_DIR = os.path.join(BASE_DIR, "database")

# Make sure the database folder exists on Render.
os.makedirs(DATABASE_DIR, exist_ok=True)


class Config:

    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "change-this-secret-key"
    )

    SQLALCHEMY_DATABASE_URI = (
        "sqlite:///" + os.path.join(DATABASE_DIR, "tasks.db")
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    ADMIN_PASSWORD = os.environ.get(
        "TASKFLOW_ADMIN_PASSWORD",
        ""
    )
