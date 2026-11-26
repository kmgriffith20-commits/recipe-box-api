from app.extensions import db
from app.models import Favorite, Recipe


def add_favorite(user_id, recipe_id):
    recipe = db.session.get(Recipe, recipe_id)

    if recipe is None:
        return None, 404

    if not recipe.is_public and recipe.user_id != user_id:
        return None, 403

    favorite = Favorite.query.filter_by(
        user_id=user_id,
        recipe_id=recipe_id
    ).first()

    if favorite:
        return favorite, 200

    favorite = Favorite(
        user_id=user_id,
        recipe_id=recipe_id
    )

    db.session.add(favorite)
    db.session.commit()

    return favorite, 201

def remove_favorite(user_id, recipe_id):
    favorite = Favorite.query.filter_by(
        user_id=user_id,
        recipe_id=recipe_id
    ).first()

    if favorite is None:
        return None, 204

    db.session.delete(favorite)
    db.session.commit()

    return None, 204


def get_user_favorites(user_id):
    favorites = Favorite.query.filter_by(
        user_id=user_id
    ).all()

    return [
        favorite.recipe
        for favorite in favorites
        if favorite.recipe is not None
    ]