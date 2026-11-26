# Service Ownership

The Users Service owns user accounts, authentication, and user information in its own database. The Recipes Service owns recipes and recipe-related data in a separate database. The old relationship-based recipe.user and current_user ownership check is retired. Recipe ownership is now verified by comparing the recipe's owner_id with the user_id from the JWT token.
