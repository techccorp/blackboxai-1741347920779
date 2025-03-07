from flask import Blueprint, jsonify, request, current_app
from bson.json_util import dumps
from bson import ObjectId
import re
import logging
from config import Config

# Initialize logging
logger = logging.getLogger(__name__)

# Define the products Blueprint
products = Blueprint('products', __name__)

def get_product_list_collection():
    """
    Lazily initialize the product_list collection.
    """
    if 'MONGO_CLIENT' not in current_app.config:
        logger.error("MONGO_CLIENT is not configured in the application context.")
        raise RuntimeError("Database client not configured. Ensure MONGO_CLIENT is set in app configuration.")

    db = current_app.config['MONGO_CLIENT'][Config.MONGO_DBNAME]
    return db[Config.COLLECTION_PRODUCT_LIST]

@products.route('/api/products/search', methods=['GET'])
def search_products():
    """
    Search for products in the product_list collection based on a query.
    """
    try:
        query = request.args.get('query', '').strip()
        if not query:
            logger.info("Empty query received.")
            return jsonify([])

        collection = get_product_list_collection()
        pattern = re.compile(f'.*{re.escape(query)}.*', re.IGNORECASE)
        pipeline = [
            {
                '$match': {
                    '$or': [
                        {'INGREDIENT': pattern},
                        {'SUPPLIER': pattern}
                    ]
                }
            },
            {
                '$limit': 10
            },
            {
                '$project': {
                    '_id': {'$toString': '$_id'},
                    'SUPPLIER': 1,
                    'INGREDIENT': 1,
                    'PU': 1,
                    'PUC': 1,
                    'RU': 1,
                    'RUC': 1
                }
            }
        ]
        logger.debug(f"Executing pipeline: {pipeline}")
        products = list(collection.aggregate(pipeline))
        logger.info(f"Products fetched: {products}")
        return jsonify(products)

    except Exception as e:
        logger.error(f"Error in product search: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@products.route('/api/products/details/<product_id>', methods=['GET'])
def get_product_details(product_id):
    """
    Get detailed information for a specific product by ID.
    """
    try:
        collection = get_product_list_collection()
        product = collection.find_one({'_id': ObjectId(product_id)})
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # Convert ObjectId to string for JSON serialization
        product['_id'] = str(product['_id'])
        return jsonify(product)

    except Exception as e:
        logger.error(f"Error fetching product details: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@products.route('/api/products/bulk', methods=['POST'])
def bulk_product_lookup():
    """
    Look up multiple products by their IDs.
    """
    try:
        product_ids = request.json.get('product_ids', [])
        if not product_ids:
            return jsonify([])

        collection = get_product_list_collection()
        object_ids = [ObjectId(pid) for pid in product_ids if ObjectId.is_valid(pid)]
        products = list(collection.find({'_id': {'$in': object_ids}}))

        for product in products:
            product['_id'] = str(product['_id'])

        return jsonify(products)

    except Exception as e:
        logger.error(f"Error in bulk product lookup: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@products.route('/api/products/categories', methods=['GET'])
def get_product_categories():
    """
    Get all unique product categories/types.
    """
    try:
        collection = get_product_list_collection()
        categories = collection.distinct('CATEGORY')
        return jsonify(sorted(categories))

    except Exception as e:
        logger.error(f"Error fetching product categories: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Error Handlers
@products.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Resource not found'}), 404

@products.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500
