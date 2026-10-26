from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from models import User, session_factory

bp = Blueprint("users", __name__, url_prefix="/users")


@bp.get("/")
def list_users():
    with session_factory() as session:
        stmt = select(User).options(selectinload(User.posts)).order_by(User.id)
        users = session.scalars(stmt).all()
        return render_template("users/list.html", users=users)


@bp.route("/add/", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()

        if not (name and username and email):
            flash("Все поля обязательны", "error")
        else:
            with session_factory() as session:
                session.add(User(name=name, username=username, email=email))
                try:
                    session.commit()
                except IntegrityError:
                    session.rollback()
                    flash("Пользователь с таким username или email уже существует", "error")
                else:
                    flash("Пользователь добавлен", "success")
                    return redirect(url_for("users.list_users"))

    return render_template("users/add.html", form=request.form)