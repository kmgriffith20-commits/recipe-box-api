import os
from flask import Flask, request, jsonify
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from .config import Config
from .models import db, User

migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["JWT_SECRET_KEY"] = os.environ["JWT_SECRET"]

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    @app.post("/register")
    def register():
        data = request.get_json(silent=True) or {}
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify(error="Missing credentials"), 400

        if User.query.filter_by(username=username).first():
            return jsonify(error="User already exists"), 409

        user = User(
            username=username,
            password_hash=generate_password_hash(password, method="pbkdf2:sha256")
        )
        db.session.add(user)
        db.session.commit()
        return jsonify(message="User registered", id=user.id), 201

    @app.post("/login")
    def login():
        data = request.get_json(silent=True) or {}
        user = User.query.filter_by(
            username=data.get("username")
        ).first()

        if not user or not check_password_hash(
            user.password_hash, data.get("password") or ""
        ):
            return jsonify(error="Invalid credentials"), 401

        token = create_access_token(identity=str(user.id))
        return jsonify(access_token=token), 200


    @app.get("/me")
    @jwt_required()
    def me():
        user_id = get_jwt_identity()
        user = db.session.get(User, int(user_id))

        if not user:
            return jsonify(error="User not found"), 404

        return jsonify({
            "id": user.id,
            "username": user.username
        }), 200

    return app
