
from datetime import datetime, timedelta
from types import SimpleNamespace

from flask import (
    Blueprint, render_template, redirect,
    url_for, request, flash
)
from flask_login import login_required, current_user

from extensions import db
from models.task import Task

tasks = Blueprint("tasks", __name__)


# =========================
# MAIN DASHBOARD
# =========================
@tasks.route("/")
def index():

    if not current_user.is_authenticated:
        today = datetime.now().date()

        demo_tasks = [
            SimpleNamespace(
                id=-1,
                title="Plan your week",
                description="Organize your priorities and upcoming work.",
                priority="High",
                due_date=today + timedelta(days=1),
                due_time="09:00",
                completed=False
            ),
            SimpleNamespace(
                id=-2,
                title="Prepare a project",
                description="Gather everything needed for your next project.",
                priority="Medium",
                due_date=today + timedelta(days=2),
                due_time="13:00",
                completed=False
            )
        ]

        return render_template(
            "index.html",
            tasks=demo_tasks,
            total_tasks=3,
            completed_tasks=1,
            pending_tasks=2,
            search="",
            priority="all",
            reminder_tasks=[],
            now=datetime.now(),
            guest_mode=True
        )

    search = request.args.get("search", "").strip()
    priority = request.args.get("priority", "all")

    query = Task.query.filter_by(
        user_id=current_user.id,
        completed=False
    )

    if search:
        query = query.filter(Task.title.ilike(f"%{search}%"))

    if priority in ["Low", "Medium", "High"]:
        query = query.filter_by(priority=priority)

    task_list = query.order_by(Task.created_at.desc()).all()

    total_tasks = Task.query.filter_by(
        user_id=current_user.id
    ).count()

    completed_tasks = Task.query.filter_by(
        user_id=current_user.id,
        completed=True
    ).count()

    pending_tasks = total_tasks - completed_tasks

    now = datetime.now()
    reminder_tasks = []

    for task in task_list:
        if not task.due_date or not task.due_time:
            continue

        try:
            due_datetime = datetime.strptime(
                f"{task.due_date.strftime('%Y-%m-%d')} {task.due_time}",
                "%Y-%m-%d %H:%M"
            )
        except ValueError:
            continue

        remaining = due_datetime - now

        if timedelta(0) <= remaining <= timedelta(hours=2):
            reminder_tasks.append(task)

    return render_template(
        "index.html",
        tasks=task_list,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        search=search,
        priority=priority,
        reminder_tasks=reminder_tasks,
        now=now,
        guest_mode=False
    )


# =========================
# COMPLETED TASKS PAGE
# =========================
@tasks.route("/completed")
@login_required
def completed():

    search = request.args.get("search", "").strip()

    query = Task.query.filter_by(
        user_id=current_user.id,
        completed=True
    )

    if search:
        query = query.filter(Task.title.ilike(f"%{search}%"))

    completed_list = query.order_by(
        Task.created_at.desc()
    ).all()

    return render_template(
        "completed.html",
        tasks=completed_list
    )


# =========================
# CREATE TASK
# =========================
@tasks.route("/task/create", methods=["POST"])
@login_required
def create_task():

    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    priority = request.form.get("priority", "Medium")
    due_date_string = request.form.get("due_date", "").strip()
    due_time = request.form.get("due_time", "").strip()

    if not title:
        flash("Task title is required.", "error")
        return redirect(url_for("tasks.index"))

    if priority not in ["Low", "Medium", "High"]:
        priority = "Medium"

    due_date = None

    if due_date_string:
        try:
            due_date = datetime.strptime(
                due_date_string, "%Y-%m-%d"
            ).date()
        except ValueError:
            flash("Invalid due date.", "error")
            return redirect(url_for("tasks.index"))

    if due_time:
        try:
            datetime.strptime(due_time, "%H:%M")
        except ValueError:
            flash("Invalid due time.", "error")
            return redirect(url_for("tasks.index"))
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

    flash("Task created successfully.", "success")
    return redirect(url_for("tasks.index"))


# =========================
# COMPLETE / RESTORE TASK
# =========================
@tasks.route("/task/<int:task_id>/complete")
@login_required
def complete_task(task_id):

    task = Task.query.filter_by(
        id=task_id,
        user_id=current_user.id
    ).first_or_404()

    was_completed = task.completed
    task.completed = not task.completed

    db.session.commit()

    if task.completed:
        flash("Task marked as completed.", "success")
        return redirect(url_for("tasks.completed"))

    flash("Task restored to pending tasks.", "success")
    return redirect(url_for("tasks.index"))


# =========================
# EDIT TASK
# =========================
@tasks.route("/task/<int:task_id>/edit", methods=["GET", "POST"])
@login_required
def edit_task(task_id):

    task = Task.query.filter_by(
        id=task_id,
        user_id=current_user.id
    ).first_or_404()

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        priority = request.form.get("priority", "Medium")
        due_date_string = request.form.get("due_date", "").strip()
        due_time = request.form.get("due_time", "").strip()

        if not title:
            flash("Task title is required.", "error")
            return redirect(
                url_for("tasks.edit_task", task_id=task.id)
            )

        if priority not in ["Low", "Medium", "High"]:
            priority = "Medium"

        due_date = None

        if due_date_string:
            try:
                due_date = datetime.strptime(
                    due_date_string, "%Y-%m-%d"
                ).date()
            except ValueError:
                flash("Invalid due date.", "error")
                return redirect(
                    url_for("tasks.edit_task", task_id=task.id)
                )

        if due_time:
            try:
                datetime.strptime(due_time, "%H:%M")
            except ValueError:
                flash("Invalid due time.", "error")
                return redirect(
                    url_for("tasks.edit_task", task_id=task.id)
                )
        else:
            due_time = None

        task.title = title
        task.description = description
        task.priority = priority
        task.due_date = due_date
        task.due_time = due_time

        db.session.commit()

        flash("Task updated successfully.", "success")
        return redirect(url_for("tasks.index"))

    return render_template("edit_task.html", task=task)


# =========================
# DELETE TASK
# =========================
@tasks.route("/task/<int:task_id>/delete")
@login_required
def delete_task(task_id):

    task = Task.query.filter_by(
        id=task_id,
        user_id=current_user.id
    ).first_or_404()

    was_completed = task.completed

    db.session.delete(task)
    db.session.commit()

    flash("Task deleted successfully.", "success")

    if was_completed:
        return redirect(url_for("tasks.completed"))

    return redirect(url_for("tasks.index"))
