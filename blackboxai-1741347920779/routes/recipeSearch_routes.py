from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from bson.json_util import dumps
from bson.objectid import ObjectId
from config.base_config import config as Config
from config.mongoDB_config import get_mongo_client

# Initialize the Blueprint
recipe_search = Blueprint('recipe_search', __name__)

def get_db():
    """Get MongoDB database instance"""
    client = get_mongo_client()
    return client[Config.MONGO_DBNAME] if client else None

def lookup_globalRecipe(db, globalRecipe_name):
    """
    Look up a recipe in the global_recipes collection using partial matches.
    """
    query = {'title': {'$regex': globalRecipe_name, '$options': 'i'}}
    return list(db['global_recipes'].find(query))

def lookup_userRecipe(db, userRecipe_name):
    """
    Look up a recipe in the user_recipes collection using partial matches.
    """
    query = {'title': {'$regex': userRecipe_name, '$options': 'i'}}
    return list(db['user_recipes'].find(query))

@recipe_search.route('/api/global_recipes', methods=['GET'])
def get_global_recipes():
    """
    Search for recipes in the global_recipes collection based on query parameters.
    """
    search_query = request.args.get('search_query', '')
    ingredient = request.args.get('ingredient', '')
    cuisine = request.args.get('cuisine', '')
    method = request.args.get('method', '')
    dietary = request.args.get('dietary', '')

    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))

    query = {}

    if search_query:
        query["title"] = {"$regex": search_query, "$options": "i"}
    if ingredient:
        query["ingredients"] = {"$regex": ingredient, "$options": "i"}
    if cuisine:
        query["cuisine"] = {"$regex": cuisine, "$options": "i"}
    if method:
        query["cookery_method"] = {"$regex": method, "$options": "i"}
    if dietary:
        query["dietary"] = {"$regex": dietary, "$options": "i"}

    try:
        db = get_db()
        if not db:
            return jsonify({"error": "Database connection failed"}), 500
            
        recipes = db['global_recipes'].find(query).skip((page - 1) * limit).limit(limit)
        return dumps(list(recipes))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@recipe_search.route('/api/user_recipes', methods=['GET'])
def get_user_recipes():
    """
    Search for recipes in the user_recipes collection based on query parameters.
    """
    search_query = request.args.get('search_query', '')
    ingredient = request.args.get('ingredient', '')
    cuisine = request.args.get('cuisine', '')
    method = request.args.get('method', '')
    dietary = request.args.get('dietary', '')

    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))

    query = {}

    if search_query:
        query["title"] = {"$regex": search_query, "$options": "i"}
    if ingredient:
        query["ingredients"] = {"$regex": ingredient, "$options": "i"}
    if cuisine:
        query["cuisine"] = {"$regex": cuisine, "$options": "i"}
    if method:
        query["cookery_method"] = {"$regex": method, "$options": "i"}
    if dietary:
        query["dietary"] = {"$regex": dietary, "$options": "i"}

    try:
        db = get_db()
        if not db:
            return jsonify({"error": "Database connection failed"}), 500
            
        recipes = db['user_recipes'].find(query).skip((page - 1) * limit).limit(limit)
        return dumps(list(recipes))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
