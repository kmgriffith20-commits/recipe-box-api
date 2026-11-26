"""Recipe Box API — BE104 course skeleton.

A working Flask + SQLite CRUD API for recipes. It stores data perfectly —
and it trusts everyone. There is no authentication and no authorization yet.
That is the point: you will add both, lesson by lesson, in Units 2 and 3.
"""
from urllib import response

from app.extensions import limiter
from app.extensions import cache
from app.config import config_by_name
from app.extensions import db, migrate
from .models import Recipe, User
from app.services import add_favorite, remove_favorite, get_user_favorites

import asyncio
import httpx
import os
import hmac
import token
import jwt
from datetime import datetime, timedelta

from .config import config_by_name
from functools import wraps
from dotenv import load_dotenv

from werkzeug.security import generate_password_hash, check_password_hash

from flask import Flask, g, jsonify, request, current_app
from sqlalchemy.exc import IntegrityError

load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET")

def hash_password(plaintext_password: str) -> str:
    """Return a one-way hash of the given plaintext password."""
    return generate_password_hash(plaintext_password, method="pbkdf2:sha256")

def verify_password(stored_hash: str, candidate_password: str) -> bool:
    """Return True if the candidate password matches the stored hash."""
    return check_password_hash(stored_hash, candidate_password)

def token_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return jsonify({"error": "missing Authorization header"}), 401

        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "invalid Authorization header format"}), 401

        token = auth_header[len("Bearer "):]

        try:
            claims = jwt.decode(token, current_app.config["JWT_SECRET"], ...)
        except jwt.InvalidTokenError:
            return jsonify({"error": "invalid or expired token"}), 401

        g.user_id = claims["user_id"]
        g.role = claims.get("role")

        return view_func(*args, **kwargs)

    return wrapped_view

def create_app(config_name="development"):
    app = Flask(__name__)
    app.config["SLOW_SERVICE_BASE_URL"] = "http://localhost:5001"
    
    @app.get("/recipes/async-test")
    async def async_test():
        base_url = current_app.config["SLOW_SERVICE_BASE_URL"]

        async with httpx.AsyncClient() as client:
            tasks = [
                asyncio.create_task(client.get(base_url))
                for _ in range(3)
            ]

            # Allow the HTTP requests to start
            await asyncio.sleep(0)

            # Blocking database query
            recipe_count = db.session.query(Recipe).count()

            # Wait for all three requests
            responses = await asyncio.gather(*tasks)

        return jsonify({
            "status": "async complete",
            "requests": len(responses),
            "status_codes": [r.status_code for r in responses],
            "recipe_count": recipe_count
        })

    @app.get("/multi-nutrition")
    async def multi_nutrition():
        import time
        import asyncio
        import httpx

        base_url = current_app.config["SLOW_SERVICE_BASE_URL"]
        ingredients = ["tomato", "carrot", "potato"]

        start = time.perf_counter()

        async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
            responses = await asyncio.gather(
                *[
                    client.get(f"{base_url}/nutrition/{item}")
                    for item in ingredients
                ]
            )

        for response in responses:
            response.raise_for_status()

        results = [response.json() for response in responses]

        return jsonify({
            "status": "success",
            "mode": "concurrent",
            "results": results,
            "elapsed_seconds": round(
                time.perf_counter() - start, 3
            )
        })
    @app.post("/recipes/<int:recipe_id>/favorite")
    @limiter.limit("10 per minute")
    @token_required
    def favorite_recipe(recipe_id):
        favorite, status = add_favorite(g.user_id, recipe_id)

        if status == 404:
            return jsonify({"error": "Recipe not found"}), 404

        if status == 403:
            return jsonify({"error": "Access denied"}), 403

        return jsonify({
            "message": "Recipe added to favorites",
            "recipe_id": favorite.recipe_id
        }), status


    @app.delete("/recipes/<int:recipe_id>/favorite")
    @token_required
    def unfavorite_recipe(recipe_id):
        remove_favorite(g.user_id, recipe_id)
        return "", 204


    @app.get("/favorites")
    @token_required
    def list_favorites():
        recipes = get_user_favorites(g.user_id)

        return jsonify([
            {
                "id": recipe.id,
                "title": recipe.title,
                "ingredients": recipe.ingredients,
                "instructions": recipe.instructions,
                "is_public": recipe.is_public,
                "category": recipe.category
            }
            for recipe in recipes
        ]), 200

    
    
    @app.get("/recipes")
    def list_recipes():
        expected_token = os.environ.get("INTERNAL_SERVICE_TOKEN")
        provided_token = request.headers.get("X-Internal-Service-Token")

        if (
            not expected_token
            or not provided_token
            or not hmac.compare_digest(provided_token, expected_token)
        ):
            return jsonify({"error": "forbidden: invalid internal token"}), 403

        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer ") or not auth_header[7:].strip():
            return jsonify({"error": "missing or invalid Authorization header"}), 401

        token = auth_header[7:].strip()

        try:
            claims = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except httpx.RequestError as e:
            return jsonify({"error": str(e)}), 502
        except jwt.InvalidTokenError:
            return jsonify({"error": "invalid or expired JWT"}), 401

        if not claims.get("sub"):
            return jsonify({"error": "missing user_id in JWT"}), 401

        return jsonify({
            "message": "Both credentials validated",
            "user_id": claims["sub"]
        }), 200



    @app.post("/recipes")
    def create_recipe():
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return jsonify({"error": "missing Authorization header"}), 401

        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "invalid Authorization header format"}), 401

        token = auth_header[len("Bearer "):]

        try:
            claims = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            requester_id = claims["user_id"]
        except jwt.InvalidTokenError:
            return jsonify({"error": "invalid or expired token"}), 401

        user_id = claims["user_id"]

        data = request.get_json()
        if not data or not data.get("title") or not data.get("ingredients"):
            return jsonify({"error": "title and ingredients are required"}), 400

        current_user = db.session.get(User, g.user_id)

        if current_user is None:
            return jsonify({"error": "unauthorized"}), 401
        
        new_recipe = Recipe(
            title=data["title"],
            ingredients=data["ingredients"],
            instructions=data.get("instructions") or "",
            is_public=1 if data.get("is_public") else 0
        )

        new_recipe.user = current_user
        

        try:
            db.session.add(new_recipe)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify({
                "error": "a recipe with that title already exists"
            }), 409

        return jsonify({
            "id": new_recipe.id,
            "title": new_recipe.title,
            "ingredients": new_recipe.ingredients,
            "instructions": new_recipe.instructions,
            "is_public": bool(new_recipe.is_public),
            "user_id": new_recipe.user_id
        }), 201

    
    @app.get("/recipes/<int:recipe_id>")
    def get_recipe(recipe_id):
        recipe = Recipe.query.filter_by(id=recipe_id).first()

        if recipe is None:
            return jsonify({"error": "recipe not found"}), 404

        return jsonify({
            "id": recipe.id,
            "title": recipe.title,
            "ingredients": recipe.ingredients,
            "instructions": recipe.instructions,
            "is_public": bool(recipe.is_public),
            "user_id": recipe.user_id
        }), 200
    
    @app.patch("/recipes/<int:recipe_id>")
    @token_required
    def update_recipe(recipe_id):
        recipe = Recipe.query.filter_by(id=recipe_id).first()

        if recipe is None:
            return jsonify({"error": "recipe not found"}), 404

        owner_id = recipe.user_id

        current_user = db.session.get(User, g.user_id)

        if current_user is None:
            return jsonify({"error": "unauthorized"}), 401

        if recipe.user != current_user and current_user.role != "admin":
            return jsonify({"error": "forbidden"}), 403

        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "a JSON body is required"}), 400

        allowed_fields = ("title", "ingredients", "instructions")

        if not any(field in data for field in (*allowed_fields, "is_public")):
            return jsonify({"error": "nothing to update"}), 400

        for field in allowed_fields:
            if field in data:
                setattr(recipe, field, data[field])

        if "is_public" in data:
            recipe.is_public = 1 if data["is_public"] else 0

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify({
                "error": "a recipe with that title already exists"
            }), 409

        return jsonify({
            "id": recipe.id,
            "title": recipe.title,
            "ingredients": recipe.ingredients,
            "instructions": recipe.instructions,
            "is_public": bool(recipe.is_public),
            "user_id": recipe.user_id
        }), 200


    @app.delete("/recipes/<int:recipe_id>")
    @token_required
    def delete_recipe(recipe_id):
        
        recipe = Recipe.query.filter_by(id=recipe_id).first()

        if recipe is None:
            return jsonify({"error": "recipe not found"}), 404

        requester_id = g.user_id
        role = g.role

        if requester_id != recipe.user_id and role != "admin":
            return jsonify({"error": "forbidden"}), 403

        db.session.delete(recipe)
        db.session.commit()

        return "", 204

    @app.post("/register")
    @limiter.limit("3 per minute")
    def register():
        data = request.get_json(silent=True)

        if (
            not data
            or not data.get("username")
            or not data.get("email")
            or not data.get("password")
        ):
            return jsonify({
                "error": "username, email, and password are required"
            }), 400

        password_hash = hash_password(data["password"])

        new_user = User(
            username=data["username"],
            email=data["email"],
            password_hash=password_hash
        )

        try:
            db.session.add(new_user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify({
                "error": "username or email already exists"
            }), 409

        return jsonify({
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email
        }), 201
    
        @app.post("/login")
        @limiter.limit("5 per minute")
        def login():
            data = request.get_json(silent=True)

        if not data or not data.get("username") or not data.get("password"):
            return jsonify({"error": "username and password are required"}), 400

        user = User.query.filter_by(username=data["username"]).first()

        if user is None or not check_password_hash(
            user.password_hash, data["password"]
        ):
            return jsonify({"error": "Invalid credentials"}), 401

        payload = {
            "user_id": user.id,
            "username": user.username,
            "role": user.role,
            "exp": datetime.utcnow() + timedelta(hours=1)
        }

        token = jwt.encode(
            payload,
            current_app.config["JWT_SECRET"],
            algorithm="HS256"
        )

        return jsonify({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "token": token
        }), 200

        @app.route("/recipes/async-test", methods=["GET"])
        async def async_test():
            base_url = current_app.config["SLOW_SERVICE_BASE_URL"]
        return jsonify({
            "status": "async stub",
            "base_url": base_url
        })

    return app