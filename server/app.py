"""Tucuso-term Flask app. Search endpoint arrives in T6, web UI in T7,
reviewer auth + moderation UI in T9.
"""
import os

from flask import Flask

from server import db as dbmod
from server.api import bp as api_bp
from server.export import bp_export
from server.search import bp_search
from server.moderation_ui import bp_mod
from server.web import bp_web


def create_app(config=None):
    app = Flask(
        __name__,
        template_folder="../web",
        static_folder="../web/static",
    )
    app.config["DATABASE"] = os.environ.get("TUCUSO_DB", "data/tucuso.db")
    app.config["SECRET_KEY"] = os.environ.get("TUCUSO_SECRET", "dev-only-change-me")
    if config:
        app.config.update(config)
    dbmod.init_app(app)
    app.register_blueprint(api_bp)
    app.register_blueprint(bp_search)
    app.register_blueprint(bp_export)
    app.register_blueprint(bp_web)
    app.register_blueprint(bp_mod)

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    @app.get("/sw.js")
    def service_worker():
        # served from the root so the SW scope covers the whole site
        return app.send_static_file("sw.js")

    return app


app = create_app()
