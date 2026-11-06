
from flask import Flask
from sqlalchemy import inspect, text
from config import Config
from extensions import db, login_manager

from datetime import datetime
import threading
import time


# ==================================
# AUTOMATIC TASK COMPLETION
# ==================================

def check_expired_tasks(app):

    with app.app_context():

        # Import Task inside the application context
        from models.task import Task

        now = datetime.now()

        unfinished_tasks = Task.query.filter_by(
            completed=False
        ).all()

        changed = False

        for task in unfinished_tasks:

            if not task.due_date or not task.due_time:
                continue

            try:

                task_due_time = datetime.strptime(
                    task.due_time,
                    "%H:%M"
                ).time()

                due_datetime = datetime.combine(
                    task.due_date,
                    task_due_time
                )

                if now >= due_datetime:

                    task.completed = True
                    changed = True

            except (ValueError, TypeError):
                continue

        if changed:
            db.session.commit()


# ==================================
# CHECK EVERY 60 SECONDS
# ==================================

def deadline_checker(app):

    while True:

        try:

            check_expired_tasks(app)

        except Exception:

            app.logger.exception(
                "Automatic task completion encountered an error."
            )

        time.sleep(60)


# ==================================
# CREATE FLASK APPLICATION
# ==================================

def create_app():

    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = "auth.login"

    login_manager.login_message = (
        "Please log in to continue."
    )

    from routes.auth import auth
    from routes.tasks import tasks

    app.register_blueprint(auth)
    app.register_blueprint(tasks)

    with app.app_context():

        from models.user import User
        from models.task import Task

        db.create_all()

        # Add due_time to existing databases
        # without deleting existing tasks.

        inspector = inspect(db.engine)

        columns = [
            column["name"]
            for column in inspector.get_columns("tasks")
        ]

        if "due_time" not in columns:

            db.session.execute(
                text(
                    "ALTER TABLE tasks ADD COLUMN due_time VARCHAR(5)"
                )
            )

            db.session.commit()

    return app


# ==================================
# START APPLICATION
# ==================================

app = create_app()


if __name__ == "__main__":

    checker_thread = threading.Thread(
        target=deadline_checker,
        args=(app,),
        daemon=True
    )

    checker_thread.start()

    app.run(
        debug=True,
        use_reloader=False
    )
