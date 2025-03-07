from flask import Blueprint, redirect, url_for, session, request, jsonify
import os
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
from datetime import datetime
from google.auth.transport.requests import Request
import json
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the Blueprint
google_api = Blueprint('google_api', __name__)

# Google API Configuration
SCOPES = [
    'https://www.googleapis.com/auth/tasks',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file',
]

# Centralized API service configuration
API_SERVICES = {
    'tasks': {'name': 'tasks', 'version': 'v1'},
    'calendar': {'name': 'calendar', 'version': 'v3'},
    'keep': {'name': 'keep', 'version': 'v1'}
}

# Load credentials from environment variables
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Ensure required variables are set
if not all([GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI]):
    raise Exception('Google API credentials are not fully set in the environment variables.')

def credentials_to_dict(credentials):
    """Convert credentials to a serializable dictionary."""
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

def get_credentials():
    """Retrieve and refresh user credentials from session."""
    if 'credentials' not in session:
        return None

    try:
        credentials = google.oauth2.credentials.Credentials(**session['credentials'])

        # Refresh if expired
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            session['credentials'] = credentials_to_dict(credentials)

        return credentials
    except Exception as e:
        logger.error(f'Error retrieving credentials: {e}')
        session.pop('credentials', None)
        return None

def initialize_service(service_key):
    """Initialize a Google API service."""
    credentials = get_credentials()
    if not credentials:
        return None, 'Not authenticated', 401

    try:
        service_info = API_SERVICES.get(service_key)
        if not service_info:
            return None, f'Unknown service: {service_key}', 400

        service = googleapiclient.discovery.build(
            service_info['name'], 
            service_info['version'], 
            credentials=credentials
        )
        return service, None, 200
    except Exception as e:
        logger.error(f'Error initializing {service_key} service: {e}')
        return None, f'Error initializing {service_key} service', 500

# Authentication Routes
# Authentication Routes
@google_api.route('/auth/url')
def auth_url():
    """Generate the Google OAuth2 authorization URL."""
    try:
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            'client_secret.json', scopes=SCOPES
        )
        flow.redirect_uri = GOOGLE_REDIRECT_URI

        # Generate the authorization URL and state
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )

        # Store state in session
        session['state'] = state  # Ensure state is properly stored in the session
        logger.info(f'Stored state in session: {session.get("state")}')
        logger.info(f'Generated authorization URL with state: {state}')
        logger.info(f'Redirect URI configured as: {GOOGLE_REDIRECT_URI}')
        
        # Redirect to Google OAuth2 consent page
        return jsonify({'url': authorization_url})
    except Exception as e:
        logger.error(f'Error generating auth URL: {str(e)}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@google_api.route('/oauth2callback')
def oauth2callback():
    """Handle the OAuth2 callback from Google."""
    try:
        # Retrieve state from session
        state = session.get('state')
        logger.info(f"Received state from session: {state}")
        
        if not state:
            logger.error("No state found in session")
            return jsonify({'error': 'No state found'}), 400

        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            'client_secret.json', 
            scopes=SCOPES, 
            state=state
        )
        flow.redirect_uri = GOOGLE_REDIRECT_URI

        # Log the full URL for debugging
        logger.info(f"Authorization response URL: {request.url}")
        authorization_response = request.url
        flow.fetch_token(authorization_response=authorization_response)

        # Log successful token fetch and granted scopes
        credentials = flow.credentials
        logger.info(f"Successfully obtained credentials with scopes: {credentials.scopes}")

        # Store the credentials in the session
        session['credentials'] = credentials_to_dict(credentials)
        logger.info('Successfully stored credentials in session')

        return redirect(url_for('home.home_page'))
        
    except Exception as e:
        logger.error(f"Error in OAuth callback: {str(e)}", exc_info=True)
        # Also log session state for debugging
        logger.error(f"Session state during error: {session.get('state')}")
        return jsonify({
            'error': str(e),
            'error_type': type(e).__name__
        }), 500



@google_api.route('/auth/signout')
def signout():
    """Clear the session and sign out the user."""
    logger.info(f"User signed out at {datetime.utcnow().isoformat()}")
    session.clear()
    return redirect(url_for('index'))

# Google Tasks API Routes
@google_api.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Retrieve all Google Tasks."""
    service, error, status = initialize_service('tasks')
    if error:
        return jsonify({'error': error}), status

    try:
        tasklists = service.tasklists().list().execute()
        tasks = []
        for tasklist in tasklists.get('items', []):
            task_items = service.tasks().list(tasklist=tasklist['id']).execute()
            tasks.extend(task_items.get('items', []))
        return jsonify(tasks)
    except Exception as e:
        logger.error(f'Error fetching tasks: {e}')
        return jsonify({'error': 'Error fetching tasks'}), 500

@google_api.route('/api/tasks', methods=['POST'])
def create_task():
    """Create a new Google Task."""
    service, error, status = initialize_service('tasks')
    if error:
        return jsonify({'error': error}), status

    try:
        data = request.json
        task = {
            'title': data.get('title'),
            'notes': data.get('notes'),
            'due': data.get('due')
        }
        created_task = service.tasks().insert(tasklist='@default', body=task).execute()
        return jsonify(created_task)
    except Exception as e:
        logger.error(f'Error creating task: {e}')
        return jsonify({'error': 'Error creating task'}), 500

@google_api.route('/api/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a specific Google Task."""
    service, error, status = initialize_service('tasks')
    if error:
        return jsonify({'error': error}), status

    try:
        service.tasks().delete(tasklist='@default', task=task_id).execute()
        return jsonify({'message': 'Task deleted successfully'})
    except Exception as e:
        logger.error(f'Error deleting task: {e}')
        return jsonify({'error': 'Error deleting task'}), 500

# Google Calendar API Routes
@google_api.route('/api/calendar/events', methods=['GET'])
def get_calendar_events():
    """Retrieve upcoming Google Calendar events."""
    service, error, status = initialize_service('calendar')
    if error:
        return jsonify({'error': error}), status

    try:
        now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        return jsonify(events_result.get('items', []))
    except Exception as e:
        logger.error(f'Error fetching events: {e}')
        return jsonify({'error': 'Error fetching events'}), 500

@google_api.route('/api/calendar/events', methods=['POST'])
def create_calendar_event():
    """Create a new Google Calendar event."""
    service, error, status = initialize_service('calendar')
    if error:
        return jsonify({'error': error}), status

    try:
        data = request.json
        event = {
            'summary': data.get('summary'),
            'location': data.get('location'),
            'description': data.get('description'),
            'start': {
                'dateTime': data.get('start'),
                'timeZone': data.get('timeZone', 'UTC')
            },
            'end': {
                'dateTime': data.get('end'),
                'timeZone': data.get('timeZone', 'UTC')
            }
        }
        event = service.events().insert(calendarId='primary', body=event).execute()
        return jsonify(event)
    except Exception as e:
        logger.error(f'Error creating event: {e}')
        return jsonify({'error': 'Error creating event'}), 500

# Google Keep API Routes
@google_api.route('/api/keep/notes', methods=['GET'])
def get_notes():
    """Retrieve Google Keep notes."""
    service, error, status = initialize_service('keep')
    if error:
        return jsonify({'error': error}), status

    try:
        page_size = request.args.get('pageSize', default=10, type=int)
        page_token = request.args.get('pageToken')
        filter_str = request.args.get('filter', 'trashed=false')

        request_params = {
            'pageSize': page_size,
            'filter': filter_str
        }
        if page_token:
            request_params['pageToken'] = page_token

        response = service.notes().list(**request_params).execute()
        return jsonify(response)
    except Exception as e:
        logger.error(f'Error fetching notes: {e}')
        return jsonify({'error': 'Error fetching notes'}), 500

@google_api.route('/api/keep/notes', methods=['POST'])
def create_note():
    """Create a new Google Keep note.""" 
    service, error, status = initialize_service('keep')
    if error:
        return jsonify({'error': error}), status

    try:
        data = request.json
        note = {
            'title': data.get('title', ''),
            'body': {
                'text': data.get('body', {}).get('text', '')
            }
        }
        created_note = service.notes().create(body=note).execute()
        return jsonify(created_note)
    except Exception as e:
        logger.error(f'Error creating note: {e}')
        return jsonify({'error': 'Error creating note'}), 500

@google_api.route('/api/keep/notes/<note_id>', methods=['GET'])
def get_note(note_id):
    """Retrieve a specific Google Keep note."""
    service, error, status = initialize_service('keep')
    if error:
        return jsonify({'error': error}), status

    try:
        note = service.notes().get(name=f'notes/{note_id}').execute()
        return jsonify(note)
    except Exception as e:
        logger.error(f'Error fetching note: {e}')
        return jsonify({'error': 'Error fetching note'}), 500

@google_api.route('/api/keep/notes/<note_id>', methods=['PUT'])
def update_note(note_id):
    """Update a specific Google Keep note.""" 
    service, error, status = initialize_service('keep')
    if error:
        return jsonify({'error': error}), status

    try:
        data = request.json
        note = {
            'name': f'notes/{note_id}',
            'title': data.get('title', ''),
            'body': {
                'text': data.get('body', {}).get('text', '')
            }
        }
        updated_note = service.notes().update(name=f'notes/{note_id}', body=note).execute()
        return jsonify(updated_note)
    except Exception as e:
        logger.error(f'Error updating note: {e}')
        return jsonify({'error': 'Error updating note'}), 500

@google_api.route('/api/keep/notes/<note_id>', methods=['DELETE'])
def delete_note(note_id):
    """Delete a specific Google Keep note."""
    service, error, status = initialize_service('keep')
    if error:
        return jsonify({'error': error}), status

    try:
        service.notes().delete(name=f'notes/{note_id}').execute()
        return jsonify({'message': 'Note deleted successfully'})
    except Exception as e:
        logger.error(f'Error deleting note: {e}')
        return jsonify({'error': 'Error deleting note'}), 500
