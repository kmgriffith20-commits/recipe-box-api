from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    username = db.Column(
        db.Text,
        nullable=False,
        unique=True
    )

    email = db.Column(
        db.Text,
        nullable=False,
        unique=True
    )

    password_hash = db.Column(
        db.Text,
        nullable=False
    )

    role = db.Column(
        db.Text,
        nullable=False,
        default="user",
        server_default="user"
    )

    recipes = db.relationship("Recipe", back_populates="user", lazy="select")

class Recipe(db.Model):
    category = db.Column(db.Text, nullable=False, default="Uncategorized", server_default="Uncategorized")
    __tablename__ = "recipes"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.Text,
        nullable=False,
        unique=True
    )

    ingredients = db.Column(
        db.Text,
        nullable=False
    )

    instructions = db.Column(
        db.Text,
        nullable=False,
        server_default=""
    )

    is_public = db.Column(
        db.Integer,
        nullable=False,
        server_default="1"
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
    user = db.relationship("User", back_populates="recipes")

class Favorite(db.Model):
    __tablename__ = "favorites"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
    recipe_id = db.Column(
        db.Integer,
        db.ForeignKey("recipes.id"),
        nullable=False
    )

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "recipe_id",
            name="uq_user_recipe_favorite"
        ),
    )

    user = db.relationship("User", backref="favorites")
    recipe = db.relationship("Recipe", backref="favorites")