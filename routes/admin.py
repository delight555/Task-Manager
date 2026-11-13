
import hmac

from functools import wraps

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    flash,
    current_app
)

from flask_login import login_required, current_user

from extensions import db
from models.user import User


admin = Blueprint("admin", __name__)


def admin_required(view_function):

    @wraps(view_function)
    @login_required
    def wrapped_view(*args, **kwargs):

        if not current_user.is_admin:
            flash("Administrator access is required.", "error")
            return redirect(url_for("tasks.index"))

        return view_function(*args, **kwargs)

    return wrapped_view


# =========================
# UNLOCK ADMINISTRATOR ACCESS
# =========================

@admin.route("/admin/unlock", methods=["GET", "POST"])
@login_required
def unlock():

    if current_user.is_admin:
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":

        entered_password = request.form.get("password", "")
        admin_password = current_app.config.get("ADMIN_PASSWORD", "")

        if not admin_password:
            flash(
                "Administrator password has not been configured.",
                "error"
            )
            return render_template("admin_unlock.html")

        if hmac.compare_digest(entered_password, admin_password):

            current_user.role = "admin"
            db.session.commit()

            flash("Administrator access activated successfully.", "success")

            return redirect(url_for("admin.dashboard"))

        flash("Incorrect administrator password.", "error")

    return render_template("admin_unlock.html")


# =========================
# ADMIN DASHBOARD
# =========================

@admin.route("/admin")
@admin_required
def dashboard():

    users = User.query.order_by(User.id.asc()).all()

    total_users = len(users)
    total_admins = User.query.filter_by(role="admin").count()

    return render_template(
        "admin_dashboard.html",
        users=users,
        total_users=total_users,
        total_admins=total_admins
    )


# =========================
# CHANGE USER ROLE
# =========================

@admin.route("/admin/user/<int:user_id>/role", methods=["POST"])
@admin_required
def change_role(user_id):

    user = User.query.get_or_404(user_id)

    new_role = request.form.get("role", "")

    if user.id == current_user.id:
        flash("You cannot change your own administrator role here.", "error")
        return redirect(url_for("admin.dashboard"))

    if new_role not in ["user", "admin"]:
        flash("Invalid role selected.", "error")
        return redirect(url_for("admin.dashboard"))

    if user.role == "admin" and new_role == "user":

        admin_count = User.query.filter_by(role="admin").count()

        if admin_count <= 1:
            flash("You cannot remove the last administrator.", "error")
            return redirect(url_for("admin.dashboard"))

    user.role = new_role
    db.session.commit()

    flash("User role updated successfully.", "success")

    return redirect(url_for("admin.dashboard"))


# =========================
# DELETE USER
# =========================

@admin.route("/admin/user/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id):

    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash("You cannot delete your own administrator account.", "error")
        return redirect(url_for("admin.dashboard"))

    if user.role == "admin":

        admin_count = User.query.filter_by(role="admin").count()

        if admin_count <= 1:
            flash("You cannot delete the last administrator.", "error")
            return redirect(url_for("admin.dashboard"))

    db.session.delete(user)
    db.session.commit()

    flash("User account deleted successfully.", "success")

    return redirect(url_for("admin.dashboard"))
