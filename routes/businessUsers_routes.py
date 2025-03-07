#--------------------------------------------------------#
#           routes\businessUsers_routes.py               #
#--------------------------------------------------------#
from flask import Blueprint, jsonify, request, current_app, render_template, session, redirect, url_for
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from bson.errors import InvalidId

business_users = Blueprint('business_users', __name__)

def get_collection():
    """Get MongoDB collection using app configuration"""
    client = current_app.config['MONGO_CLIENT']
    db = client[current_app.config['MONGO_DBNAME']]
    return db[current_app.config['COLLECTION_BUSINESS_USERS']]

@business_users.route('/people')
def people_directory():
    """Render the main employee directory page"""
    return render_template('people.html')

@business_users.route('/api/employees')
def get_all_employees():
    """
    Fetch all employees with essential fields
    Returns JSON array of employee documents
    """
    try:
        collection = get_collection()
        projection = {
            '_id': 1,
            'first_name': 1,
            'last_name': 1,
            'preferred_name': 1,
            'work_email': 1,
            'personal_contact': 1,
            'role': 1,
            'venue_id': 1,
            'venue_name': 1,
            'work_area_id': 1,
            'work_area_name': 1,
            'employment_details': 1,
            'payroll_id': 1,
            'leave_entitlements': 1
        }
        
        employees = list(collection.find({}, projection))
        
        # Convert MongoDB-specific types
        for emp in employees:
            emp['_id'] = str(emp['_id'])
            if isinstance(emp.get('date_of_birth'), datetime):
                emp['date_of_birth'] = emp['date_of_birth'].isoformat()  # Convert to ISO format string
        
        return jsonify(employees)
    
    except Exception as e:
        current_app.logger.error(f"Error fetching employees: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@business_users.route('/api/employees/<payroll_id>')
def get_employee_by_payroll_id(payroll_id):
    """Get detailed employee data for modal"""
    try:
        collection = get_collection()
        employee = collection.find_one({'payroll_id': payroll_id})
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
        
        # Convert MongoDB-specific types
        employee['_id'] = str(employee['_id'])

        # Check if date_of_birth is a datetime object and format it
        if isinstance(employee.get('date_of_birth'), datetime):
            employee['date_of_birth'] = employee['date_of_birth'].isoformat()  # Convert to ISO format string

        return jsonify(employee)
    
    except Exception as e:
        current_app.logger.error(f"Error fetching employee {payroll_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@business_users.route('/api/filter')
def filter_employees():
    """
    Filter employees by venue, work area, or role
    Query params: venue, workArea, role
    """
    try:
        collection = get_collection()
        filters = {}
        projection = {
            '_id': 1,
            'first_name': 1,
            'last_name': 1,
            'preferred_name': 1,
            'work_email': 1,
            'personal_contact': 1,
            'role': 1,
            'venue_id': 1,
            'venue_name': 1,
            'work_area_id': 1,
            'work_area_name': 1,
            'employment_details': 1,
            'payroll_id': 1,
            'leave_entitlements': 1
        }

        # Get filter parameters with correct case sensitivity
        venue = request.args.get('venue')
        work_area = request.args.get('workArea')
        role_filter = request.args.get('role')

        if venue:
            filters['venue_id'] = venue
        if work_area:
            filters['work_area_id'] = work_area
        if role_filter:
            filters['role'] = role_filter

        filtered = list(collection.find(filters, projection))
        
        # Convert MongoDB-specific types
        for emp in filtered:
            emp['_id'] = str(emp['_id'])
            if isinstance(emp.get('date_of_birth'), datetime):
                emp['date_of_birth'] = emp['date_of_birth'].isoformat()  # Convert to ISO format string
        
        return jsonify(filtered)
    
    except Exception as e:
        current_app.logger.error(f"Filter error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
        
@business_users.route('/staff_roster')
def staff_roster():
    if "user" not in session:
        return redirect(url_for('auth_bp.login'))
    
    try:
        user_identifier = session["user"]
        payroll_id = user_identifier.get("payroll_id") if isinstance(user_identifier, dict) else user_identifier
        
        # Get user document with venue information
        user = get_collection().find_one(
            {"payroll_id": payroll_id},
            {"venue_name": 1}  # Only fetch needed field
        )
        
        venue_name = user.get("venue_name", "Venue Not Specified")
        
        return render_template(
            "staff_dashboard/staff_roster.html",
            venue_name=venue_name
        )
        
    except Exception as e:
        current_app.logger.error(f"Error loading staff roster: {str(e)}")
        return render_template("error.html", message="Could not load staff roster"), 500       

@business_users.route('/api/roster')
def roster_api():
    try:
        work_area = request.args.get('work_area', '')
        employee = request.args.get('employee', '')
        
        # Get base query from session
        user = get_current_user()  # Implement your user lookup
        base_query = {"venue_id": user['venue_id']}
        
        # Add filters
        if work_area:
            base_query["work_area_name"] = work_area
        if employee:
            base_query["payroll_id"] = employee
        
        # Query and format data
        employees = get_collection().find(base_query, {
            "first_name": 1,
            "last_name": 1,
            "preferred_name": 1,
            "role": 1,
            "shifts": 1
        })
        
        # Format response
        formatted = []
        for emp in employees:
            formatted.append({
                "name": emp.get('preferred_name') or emp['first_name'],
                "role": emp['role'],
                "shifts": process_shifts(emp.get('shifts', []))  # Implement shift processing
            })
        
        return jsonify(formatted)
    
    except Exception as e:
        current_app.logger.error(f"API Error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500       