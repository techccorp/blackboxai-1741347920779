from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import uuid
import logging
from config import Config

notes = Blueprint("notes", __name__, url_prefix="/api/notes")
logger = logging.getLogger(__name__)

def get_notes_collection():
    """Similar lazy init, just like get_product_list_collection()."""
    if "MONGO_CLIENT" not in current_app.config:
        logger.error("MONGO_CLIENT is not configured in the application context.")
        raise RuntimeError("Database client not configured. Ensure MONGO_CLIENT is set.")

    db = current_app.config["MONGO_CLIENT"][Config.MONGO_DBNAME]
    return db[Config.COLLECTION_USER_NOTES]  # if your config is user_notes

@notes.route("/", methods=["GET"])
def get_notes():
    """
    Fetch all notes from the 'notes' collection.
    """
    try:
        notes_collection = get_notes_collection()
        notes_list = list(notes_collection.find({}, {"_id": 0}))
        logger.info("Fetched all notes successfully.")
        return jsonify({"success": True, "data": notes_list}), 200
    except Exception as e:
        logger.error(f"Error in GET /api/notes: {e}")
        return jsonify({"success": False, "error": "Failed to fetch notes"}), 500

@notes.route("/", methods=["POST"])
def create_note():
    """
    Create a new note in the 'notes' collection.
    Expects at least 'title'; 'items'/'labels' optional.
    """
    try:
        data = request.json
        if not data or not data.get("title"):
            logger.warning("Invalid data provided (missing 'title').")
            return jsonify({"success": False, "message": "Invalid data provided"}), 400

        data.setdefault("items", [])
        data.setdefault("labels", [])
        data["id"] = str(uuid.uuid4())
        data["created_at"] = datetime.utcnow().isoformat()  # Serialize datetime

        notes_collection = get_notes_collection()
        notes_collection.insert_one(data)

        logger.info(f"Note created successfully with ID {data['id']}")
        return jsonify({"success": True, "message": "Note created", "note": data}), 201
    except Exception as e:
        logger.error(f"Error in POST /api/notes: {e}")
        return jsonify({"success": False, "error": "Failed to create note"}), 500

@notes.route("/<string:note_id>", methods=["DELETE"])
def delete_note(note_id):
    """
    Delete a note by its unique 'id'.
    """
    try:
        notes_collection = get_notes_collection()
        result = notes_collection.delete_one({"id": note_id})
        if result.deleted_count == 0:
            logger.warning(f"Note with ID {note_id} not found.")
            return jsonify({"success": False, "message": "Note not found"}), 404

        logger.info(f"Note with ID {note_id} deleted successfully.")
        return jsonify({"success": True, "message": "Note deleted"}), 200
    except Exception as e:
        logger.error(f"Error in DELETE /api/notes/{note_id}: {e}")
        return jsonify({"success": False, "error": "Failed to delete note"}), 500
