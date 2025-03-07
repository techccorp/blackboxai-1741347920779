from flask import Blueprint, request, jsonify, session, redirect, url_for
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from config import Config
import os

google_tasks = Blueprint('google_tasks', __name__, url_prefix='/google_tasks')

SCOPES = ['https://www.googleapis.com/auth/tasks']

def get_google_tasks_service(credentials_dict):
    """Initialize and return the Google Tasks API service."""
    credentials = Credentials(**credentials_dict)
    return build('tasks', 'v1', credentials=credentials)


@google_tasks.route('/authorize')
def authorize():
    """Redirect the user to Google's OAuth 2.0 authorization page."""
    flow = Flow.from_client_secrets_file(
        os.getenv('GOOGLE_CLIENT_SECRET_PATH'),
        scopes=SCOPES,
        redirect_uri=url_for('google_tasks.oauth2callback', _external=True)
    )
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes=True
    )
    session['state'] = state
    return redirect(authorization_url)


@google_tasks.route('/oauth2callback')
def oauth2callback():
    """Handle the callback from Google's OAuth 2.0 server."""
    state = session['state']
    flow = Flow.from_client_secrets_file(
        os.getenv('GOOGLE_CLIENT_SECRET_PATH'),
        scopes=SCOPES,
        state=state,
        redirect_uri=url_for('google_tasks.oauth2callback', _external=True)
    )
    flow.fetch_token(authorization_response=request.url)
    session['credentials'] = {
        'token': flow.credentials.token,
        'refresh_token': flow.credentials.refresh_token,
        'token_uri': flow.credentials.token_uri,
        'client_id': flow.credentials.client_id,
        'client_secret': flow.credentials.client_secret,
        'scopes': flow.credentials.scopes
    }
    return redirect(url_for('home.index'))


@google_tasks.route('/add_task', methods=['POST'])
def add_task():
    """Add a new task to the Google Tasks list."""
    if 'credentials' not in session:
        return jsonify({'error': 'User not authenticated'}), 401

    credentials_dict = session['credentials']
    service = get_google_tasks_service(credentials_dict)

    task_data = {
        'title': request.json.get('title'),
        'notes': request.json.get('notes'),
        'due': request.json.get('due')  # Optional
    }

    try:
        result = service.tasks().insert(tasklist='@default', body=task_data).execute()
        return jsonify(result), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@google_tasks.route('/get_tasks', methods=['GET'])
def get_tasks():
    """Retrieve tasks for today."""
    if 'credentials' not in session:
        return jsonify({'error': 'User not authenticated'}), 401

    credentials_dict = session['credentials']
    service = get_google_tasks_service(credentials_dict)

    try:
        tasks = service.tasks().list(tasklist='@default', showCompleted=True).execute()
        return jsonify(tasks.get('items', [])), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@google_tasks.route('/edit_task/<task_id>', methods=['PUT'])
def edit_task(task_id):
    """Edit an existing task in Google Tasks."""
    if 'credentials' not in session:
        return jsonify({'error': 'User not authenticated'}), 401

    credentials_dict = session['credentials']
    service = get_google_tasks_service(credentials_dict)

    task_data = {
        'title': request.json.get('title'),
        'notes': request.json.get('notes'),
        'due': request.json.get('due'),
        'status': request.json.get('status')
    }

    try:
        result = service.tasks().update(tasklist='@default', task=task_id, body=task_data).execute()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@google_tasks.route('/delete_task/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task from Google Tasks."""
    if 'credentials' not in session:
        return jsonify({'error': 'User not authenticated'}), 401

    credentials_dict = session['credentials']
    service = get_google_tasks_service(credentials_dict)

    try:
        service.tasks().delete(tasklist='@default', task=task_id).execute()
        return jsonify({'message': 'Task deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
