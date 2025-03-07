from flask import Blueprint, request, jsonify
from models import get_db
from bson.objectid import ObjectId

# Create a new blueprint for allergen routes
allergens = Blueprint('allergens', __name__)

# Route to handle allergen search
@allergens.route('/api/allergens', methods=['GET'])
def get_allergens():
    """
    Fetch allergens from the database based on search parameters.
    Parameters include:
    - search_query: Search string to match allergen ingredient names.
    - severity: Filter by severity level.
    - symptom: Filter by symptom description.
    """
    # Get query parameters from the request
    search_query = request.args.get('search_query', '')
    severity_filter = request.args.get('severity', '')
    symptom_filter = request.args.get('symptom', '')

    # Get the allergens collection from the database
    db = get_db()
    allergens_collection = db.allergens  # Assuming allergens are stored in the 'allergens' collection

    # Initialize query filters
    query_filters = []

    # Search by allergen name or description (case-insensitive)
    if search_query:
        query_filters.append({
            "ingredient": {"$regex": ".*" + search_query + ".*", "$options": "i"}
        })

    # Filter by severity
    if severity_filter:
        query_filters.append({
            "severity": severity_filter
        })

    # Filter by symptoms
    if symptom_filter:
        query_filters.append({
            "symptoms": {"$regex": ".*" + symptom_filter + ".*", "$options": "i"}
        })

    # Build the query with the filters
    if query_filters:
        allergens = allergens_collection.find({
            "$and": query_filters
        })
    else:
        allergens = allergens_collection.find()  # Return all allergens if no filters are applied

    # Convert MongoDB cursor to a list of allergen dictionaries
    allergens_list = []
    for allergen in allergens:
        allergen['_id'] = str(allergen['_id'])  # Convert ObjectId to string for JSON response
        # Ensure the `img_url` field is included, using a default placeholder if absent
        allergen['img_url'] = allergen.get('img_url', 'https://via.placeholder.com/100')
        allergens_list.append(allergen)

    # Return the allergen data as JSON
    return jsonify(allergens_list)

