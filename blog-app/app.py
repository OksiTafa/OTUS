from flask import Flask, redirect, url_for

from config import settings
from views import posts_bp, users_bp

app = Flask(__name__)
app.config["SECRET_KEY"] = settings.app.secret_key.get_secret_value()

app.register_blueprint(users_bp)
app.register_blueprint(posts_bp)


@app.get("/")
def index():
    return redirect(url_for("posts.list_posts"))