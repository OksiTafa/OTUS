from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from models import Post, User, session_factory

bp = Blueprint("posts", __name__, url_prefix="/posts")


@bp.get("/")
def list_posts():
    with session_factory() as session:
        stmt = (
            select(Post)
            .options(joinedload(Post.user))
            .order_by(Post.created_at.desc())
        )
        posts = session.scalars(stmt).all()
        return render_template("posts/list.html", posts=posts)


@bp.route("/add/", methods=["GET", "POST"])
def add_post():
    with session_factory() as session:
        users = session.scalars(select(User).order_by(User.username)).all()
        if not users:
            flash("Сначала добавьте пользователя", "error")
            return redirect(url_for("users.add_user"))

        if request.method == "POST":
            user_id = request.form.get("user_id", type=int)
            title = request.form.get("title", "").strip()
            body = request.form.get("body", "").strip()

            if not (user_id and title and body):
                flash("Все поля обязательны", "error")
            elif session.get(User, user_id) is None:
                flash("Пользователь не найден", "error")
            else:
                session.add(Post(user_id=user_id, title=title, body=body))
                session.commit()
                flash("Пост добавлен", "success")
                return redirect(url_for("posts.list_posts"))

        return render_template("posts/add.html", users=users, form=request.form)
