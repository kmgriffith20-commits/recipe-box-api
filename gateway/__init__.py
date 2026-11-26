import os
import httpx
from flask import Flask, request, jsonify, Response

def create_app():
    app = Flask(__name__)

    app.config["USERS_SERVICE_URL"] = os.getenv(
        "USERS_SERVICE_URL",
        "http://127.0.0.1:5001"
    )

    async def forward_login(data):
        async with httpx.AsyncClient(timeout=10.0) as client:
            return await client.post(
                app.config["USERS_SERVICE_URL"] + "/login",
                json=data
            )

    @app.post("/login")
    async def login():
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({"error": "JSON body required"}), 400

        try:
            result = await forward_login(data)
            return Response(
                result.content,
                status=result.status_code,
                content_type=result.headers.get(
                    "content-type", "application/json"
                )
            )
        except httpx.RequestError:
            return jsonify({
                "error": "Users service unavailable"
            }), 502

    return app

# Concurrent gateway /me endpoint
import asyncio

def register_me_route(app):
    async def fetch_service(client, url, headers, name):
        try:
            response = await client.get(
                url, headers=headers, timeout=3.0
            )
            response.raise_for_status()
            return response.json(), None
        except httpx.TimeoutException:
            return None, f"{name} service timed out"
        except httpx.RequestError:
            return None, f"{name} service unavailable"
        except httpx.HTTPStatusError as exc:
            return None, f"{name} service returned HTTP {exc.response.status_code}"
        except ValueError:
            return None, f"{name} service returned invalid JSON"

    @app.get("/me")
    async def gateway_me():
        authorization = request.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            return jsonify({"error": "Missing Bearer token"}), 401

        headers = {"Authorization": authorization}
        recipes_headers = {
            **headers,
            "X-Internal-Service-Token": os.getenv(
                "INTERNAL_SERVICE_TOKEN", ""
            )
        }

        async with httpx.AsyncClient() as client:
            (user, user_error), (recipes, recipes_error) = await asyncio.gather(
                fetch_service(
                    client, "http://127.0.0.1:5001/me",
                    headers, "Users"
                ),
                fetch_service(
                    client, "http://127.0.0.1:5002/recipes",
                    recipes_headers, "Recipes"
                )
            )

        errors = {}
        if user_error:
            errors["users"] = user_error
        if recipes_error:
            errors["recipes"] = recipes_error

        return jsonify({
            "user": user,
            "recipes": recipes,
            "complete": not bool(errors),
            "errors": errors
        })

_original_create_app = create_app

def create_app():
    app = _original_create_app()
    register_me_route(app)
    return app
