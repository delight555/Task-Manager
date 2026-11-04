from datetime import datetime, timedelta

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    flash
)

from flask_login import (
    login_required,
    current_user
)

from extensions import db
from models.task import Task


tasks = Blueprint(
    "tasks",
    __name__
)


# =========================
# DASHBOARD
# =========================
@tasks.route("/")
@login_required
def index():

    search = request.args.get(
        "search",
        ""
    ).strip()

    status = request.args.get(
        "status",
        "all"
    )

    priority = request.args.get(
        "priority",
        "all"
    )

    query = Task.query.filter_by(
        user_id=current_user.id
    )

    if search:

        query = query.filter(
            Task.title.ilike(
                f"%{search}%"
            )
        )

    if status == "completed":

        query = query.filter_by(
            completed=True
        )

    elif status == "pending":

        query = query.filter_by(
            completed=False
        )

    if priority in [
        "Low",
        "Medium",
        "High"
    ]:

        query = query.filter_by(
            priority=priority
        )

    task_list = query.order_by(
        Task.created_at.desc()
    ).all()

    total_tasks = Task.query.filter_by(
        user_id=current_user.id
    ).count()

    completed_tasks = Task.query.filter_by(
        user_id=current_user.id,
        completed=True
    ).count()

    pending_tasks = total_tasks - completed_tasks

    # =========================
    # TWO-HOUR REMINDERS
    # =========================
    now = datetime.now()

    reminder_tasks = []

    for task in task_list:

        if task.completed:
            continue

        if not task.due_date:
            continue

        if not task.due_time:
            continue

        try:

            due_datetime = datetime.strptime(
                f"{task.due_date.strftime('%Y-%m-%d')} {task.due_time}",
                "%Y-%m-%d %H:%M"
            )

        except ValueError:

            continue

        time_remaining = due_datetime - now

        # Reminder window:
        # From now until 2 hours from now.
        if timedelta(0) <= time_remaining <= timedelta(hours=2):

            reminder_tasks.append(
                task
            )

    return render_template(
        "index.html",
        tasks=task_list,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        search=search,
        status=status,
        priority=priority,
        reminder_tasks=reminder_tasks
    )


# =========================
# CREATE TASK
# =========================
@tasks.route(
    "/task/create",
    methods=["POST"]
)
@login_required
def create_task():

    title = request.form.get(
        "title",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    priority = request.form.get(
        "priority",
        "Medium"
    )

    due_date_string = request.form.get(
        "due_date",
        ""
    ).strip()

    due_time = request.form.get(
        "due_time",
        ""
    ).strip()

    if not title:

        flash(
            "Task title is required.",
            "error"
        )

        return redirect(
            url_for("tasks.index")
        )

    if priority not in [
        "Low",
        "Medium",
        "High"
    ]:

        priority = "Medium"

    due_date = None

    if due_date_string:

        try:

            due_date = datetime.strptime(
                due_date_string,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            flash(
                "Invalid due date.",
                "error"
            )

            return redirect(
                url_for("tasks.index")
            )

    if due_time:

        try:

            datetime.strptime(
                due_time,
                "%H:%M"
            )

        except ValueError:

            flash(
                "Invalid due time.",
                "error"
            )

            return redirect(
                url_for("tasks.index")
            )

    else:

        due_time = None

    task = Task(
        title=title,
        description=description,
        priority=priority,
        due_date=due_date,
        due_time=due_time,
        user_id=current_user.id
    )

    db.session.add(task)
    db.session.commit()

    flash(
        "Task created successfully.",
        "success"
    )

    return redirect(
        url_for("tasks.index")
    )


# =========================
# COMPLETE / UNCOMPLETE
# =========================
@tasks.route(
    "/task/<int:task_id>/complete"
)
@login_required
def complete_task(task_id):

    task = Task.query.filter_by(
        id=task_id,
        user_id=current_user.id
    ).first_or_404()

    task.completed = not task.completed

    db.session.commit()

    if task.completed:

        flash(
            "Task marked as completed.",
            "success"
        )

    else:

        flash(
            "Task marked as pending.",
            "success"
        )

    return redirect(
        url_for("tasks.index")
    )


# =========================
# EDIT TASK
# =========================
@tasks.route(
    "/task/<int:task_id>/edit",
    methods=["GET", "POST"]
)
@login_required
def edit_task(task_id):

    task = Task.query.filter_by(
        id=task_id,
        user_id=current_user.id
    ).first_or_404()

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        priority = request.form.get(
            "priority",
            "Medium"
        )

        due_date_string = request.form.get(
            "due_date",
            ""
        ).strip()

        due_time = request.form.get(
            "due_time",
            ""
        ).strip()

        if not title:

            flash(
                "Task title is required.",
                "error"
            )

            return redirect(
                url_for(
                    "tasks.edit_task",
                    task_id=task.id
                )
            )

        if priority not in [
            "Low",
            "Medium",
            "High"
        ]:

            priority = "Medium"

        due_date = None

        if due_date_string:

            try:

                due_date = datetime.strptime(
                    due_date_string,
                    "%Y-%m-%d"
                ).date()

            except ValueError:

                flash(
                    "Invalid due date.",
                    "error"
                )

                return redirect(
                    url_for(
                        "tasks.edit_task",
                        task_id=task.id
                    )
                )

        if due_time:

            try:

                datetime.strptime(
                    due_time,
                    "%H:%M"
                )

            except ValueError:

                flash(
                    "Invalid due time.",
                    "error"
                )

                return redirect(
                    url_for(
                        "tasks.edit_task",
                        task_id=task.id
                    )
                )

        else:

            due_time = None

        task.title = title
        task.description = description
        task.priority = priority
        task.due_date = due_date
        task.due_time = due_time

        db.session.commit()

        flash(
            "Task updated successfully.",
            "success"
        )

        return redirect(
            url_for("tasks.index")
        )

    return render_template(
        "edit_task.html",
        task=task
    )


# =========================
# DELETE TASK
# =========================
@tasks.route(
    "/task/<int:task_id>/delete"
)
@login_required
def delete_task(task_id):

    task = Task.query.filter_by(
        id=task_id,
        user_id=current_user.id
    ).first_or_404()

    db.session.delete(task)
    db.session.commit()

    flash(
        "Task deleted successfully.",
        "success"
    )

    return redirect(
        url_for("tasks.index")
    )
