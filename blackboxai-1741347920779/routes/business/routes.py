# ------------------------------------------------------------
# /routes/business/routes.py
# ------------------------------------------------------------
from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for, current_app, flash
from functools import wraps
from bson import ObjectId
from datetime import datetime
from pymongo.errors import ConnectionFailure, OperationFailure
from models import get_db
from forms import BusinessSetupForm, VenueForm, WorkAreaForm
from utils import (
    create_business,
    add_venue_to_business,
    add_work_area_to_venue,
    assign_user_to_business,
    assign_user_to_work_area,
    get_business_hierarchy,
    update_business_status,
    validate_business_structure,
    lookup_business,
    lookup_venue,
    lookup_work_area
)
from config import Config
import logging

# Initialize logging
logger = logging.getLogger(__name__)

# Initialize blueprint
business = Blueprint('business', __name__, url_prefix='/business')

def handle_db_error(f):
    """Decorator for handling database errors"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ConnectionFailure as e:
            logger.error(f"Database connection error: {str(e)}")
            flash("Unable to connect to database. Please try again later.", "error")
            return redirect(url_for('error_routes.error_503'))
        except OperationFailure as e:
            logger.error(f"Database operation error: {str(e)}")
            return redirect(url_for('error_routes.error_500'))
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {str(e)}")
            return redirect(url_for('error_routes.error_500'))
    return decorated_function

def login_required(f):
    """Enhanced login verification with session security"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            logger.warning('Unauthorized access attempt to business routes')
            flash("Please login to access this page.", "warning")
            return redirect(url_for('auth.login'))
        
        # Verify session integrity
        if 'last_active' not in session or \
           (datetime.utcnow() - datetime.fromisoformat(session['last_active'])).total_seconds() > 3600:
            session.clear()
            flash("Session expired. Please login again.", "warning")
            return redirect(url_for('auth.login'))
        
        # Update last active timestamp
        session['last_active'] = datetime.utcnow().isoformat()
        return f(*args, **kwargs)
    return decorated_function

def verify_business_access(f):
    """Decorator to verify business access permissions"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        business_id = kwargs.get('business_id') or request.view_args.get('business_id')
        if not business_id:
            return jsonify({'error': 'Business ID required'}), 400

        db = get_db()
        business_data = lookup_business(db, business_id)
        
        if not business_data:
            return jsonify({'error': 'Business not found'}), 404
            
        if business_data['admin_user_id'] != session.get('user_id'):
            return jsonify({'error': 'Unauthorized access'}), 403
            
        return f(*args, **kwargs)
    return decorated_function

@business.route('/setup/venue', methods=['GET', 'POST'])
@login_required
@handle_db_error
def setup_venue():
    """
    Renders the venue setup page.
    """
    form = VenueForm()
    if form.validate_on_submit():
        # Logic to handle venue creation
        db = get_db()
        business_id = session.get('business_setup_id')
        venue_data = {
            'name': form.name.data,
            'address': form.address.data,
            'contact': form.contact.data,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        result = add_venue_to_business(db, business_id, venue_data)
        if result:
            flash("Venue added successfully.", "success")
            return redirect(url_for('business.setup_work_areas'))

        flash("Failed to add venue. Please try again.", "error")
    return render_template('business/setup_venue.html', form=form, title="Setup Venue")

@business.route('/api/dashboard_data', methods=['GET'])
@login_required
@handle_db_error
def get_dashboard_data():
    """
    API endpoint to fetch data for the business dashboard.
    """
    db = get_db()
    user_id = session.get('user_id')

    # Fetch business data for the logged-in user
    business_data = db[Config.COLLECTION_BUSINESSES].find_one({"admin_user_id": user_id})
    if not business_data:
        return jsonify({'error': 'No business found for your account.'}), 404

    try:
        # Fetch related data
        venues = list(db[Config.COLLECTION_VENUES].find({"business_id": business_data["_id"]}))
        total_employees = sum(len(venue.get('employees', [])) for venue in venues)

        # Prepare the response
        return jsonify({
            'status': 'success',
            'data': {
                'business': {
                    'id': business_data.get('business_id'),
                    'name': business_data.get('name'),
                    'created_at': business_data.get('created_at'),
                },
                'venues': venues,
                'total_employees': total_employees,
            }
        })
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {str(e)}")
        return jsonify({'error': 'Failed to fetch dashboard data.'}), 500
