import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

from config import Config
from models import db
from models.user import User

# Path to the frontend directory (sibling of backend/)
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))


def create_app():
    """Application factory for the Diet Planner backend."""
    app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
    app.config.from_object(Config)

    # ── Extensions ──────────────────────────────────────────────
    db.init_app(app)

    bcrypt = Bcrypt(app)

    login_manager = LoginManager()
    login_manager.init_app(app)

    # Allow credentials (cookies) from any origin (needed for ngrok)
    CORS(
        app,
        supports_credentials=True,
        origins=["http://localhost:5500", "http://127.0.0.1:5500", "http://localhost:5501", "http://127.0.0.1:5501", "http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000", "http://127.0.0.1:8000", "http://localhost:5000", "http://127.0.0.1:5000"],
    )

    # ── Flask-Login config ──────────────────────────────────────
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        return jsonify({"error": "Authentication required"}), 401

    # ── Register Blueprints ─────────────────────────────────────
    from routes.auth import auth_bp
    from routes.profile import profile_bp
    from routes.meal import meal_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(meal_bp)

    # ── Health check ────────────────────────────────────────────
    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "message": "Diet Planner API is running"}), 200

    # ── Serve frontend ──────────────────────────────────────────
    @app.route("/")
    def serve_index():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.route("/<path:filename>")
    def serve_frontend(filename):
        return send_from_directory(FRONTEND_DIR, filename)

    # ── Create tables ───────────────────────────────────────────
    with app.app_context():
        db.create_all()
        
        # Seed demo user if not exists
        demo_email = "demo@calorithm.com"
        demo_user = User.query.filter_by(email=demo_email).first()
        if not demo_user:
            password_hash = bcrypt.generate_password_hash("demo1234").decode("utf-8")
            demo_user = User(
                name="Demo Indian User",
                email=demo_email,
                password_hash=password_hash,
                age=28,
                gender="male",
                height_cm=175.0,
                weight_kg=72.0,
                activity_level="moderately_active",
                goal="muscle_gain",
                dietary_preference="indian_vegetarian",
                allergies=""
            )
            db.session.add(demo_user)
            db.session.commit()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
