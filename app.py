from flask import Flask
from sqlalchemy import inspect, text
from config import Config
from extensions import db, login_manager


def create_app():

    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to continue."

    from routes.auth import auth
    from routes.tasks import tasks

    app.register_blueprint(auth)
    app.register_blueprint(tasks)

    with app.app_context():

        from models.user import User
        from models.task import Task

        db.create_all()

        # Add due_time to existing databases without deleting existing tasks.
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


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
