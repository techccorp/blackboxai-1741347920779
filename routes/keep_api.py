from flask import Blueprint, request, jsonify, current_app, redirect, url_for
import requests
import os

keep_api = Blueprint('keep_api', __name__)

# Base URL for Google Keep API
GOOGLE_KEEP_BASE_URL = "https://keep.googleapis.com/v1"

@keep_api.route('/notes', methods=['GET'])
def list_notes():
    """Lists all notes."""
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"error": "Authorization token is missing"}), 401
    
    response = requests.get(
        f"{GOOGLE_KEEP_BASE_URL}/notes",
        headers={"Authorization": token}
    )
    return jsonify(response.json()), response.status_code

@keep_api.route('/notes', methods=['POST'])
def create_note():
    """Creates a new note."""
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"error": "Authorization token is missing"}), 401
    
    note_data = request.json
    response = requests.post(
        f"{GOOGLE_KEEP_BASE_URL}/notes",
        headers={"Authorization": token},
        json=note_data
    )
    return jsonify(response.json()), response.status_code

@keep_api.route('/notes/<note_id>', methods=['DELETE'])
def delete_note(note_id):
    """Deletes a specific note by ID."""
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"error": "Authorization token is missing"}), 401
    
    response = requests.delete(
        f"{GOOGLE_KEEP_BASE_URL}/notes/{note_id}",
        headers={"Authorization": token}
    )
    if response.status_code == 204:
        return jsonify({"message": "Note deleted successfully"}), 200
    return jsonify(response.json()), response.status_code

@keep_api.route('/notes/<note_id>', methods=['GET'])
def get_note_details(note_id):
    """Fetches details of a specific note."""
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"error": "Authorization token is missing"}), 401
    
    response = requests.get(
        f"{GOOGLE_KEEP_BASE_URL}/notes/{note_id}",
        headers={"Authorization": token}
    )
    return jsonify(response.json()), response.status_code

# Additional routes for permission management can be added similarly
