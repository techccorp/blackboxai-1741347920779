from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, current_app, session, redirect, url_for, jsonify, abort
from bson import ObjectId
from services.employee_service import EmployeeService
from services.venue_service import VenueService
from services.financial_service import FinancialService
from models.business_entities.roster import Roster, Shift
from routes.extensions import db
import logging

logger = logging.getLogger(__name__)

# Create Blueprint
rostering_bp = Blueprint('rostering', __name__, url_prefix='/business')

# Initialize services
def get_services():
    """Initialize and return all required services"""
    employee_service = EmployeeService(db.db)
    venue_service = VenueService(db.db)
    financial_service = FinancialService(db.db)
    roster = Roster(db.db)
    return employee_service, venue_service, financial_service, roster

@rostering_bp.route('/rostering')
def rostering_page():
    """Render the rostering page"""
    # Get user's venue ID (assuming it's stored in session)
    venue_id = request.args.get('venue_id') 
    if not venue_id and 'user' in session and 'venue_id' in session['user']:
        venue_id = session['user']['venue_id']
    
    if not venue_id:
        # If no venue_id, redirect to a venue selection page or default venue
        return redirect(url_for('home.index'))
    
    try:
        # Get services
        employee_service, venue_service, financial_service, roster = get_services()
        
        # Get start date (default to current week's Monday)
        today = datetime.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        
        start_date_str = request.args.get('start_date')
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                start_date = start_of_week
        else:
            start_date = start_of_week
        
        # Get week dates
        week_dates = [start_date + timedelta(days=i) for i in range(7)]
        
        # Filter by linking_id if provided
        linking_id = request.args.get('linking_id')
        
        # Filter by work_area_id if provided
        work_area_id = request.args.get('work_area_id')
        
        # Get financial summary
        financial_summary = financial_service.get_financial_summary(venue_id)
        
        # Get venue details
        venue = venue_service.get_venue(venue_id)
        if not venue:
            logger.error(f"Venue not found with ID: {venue_id}")
            abort(404, description="Venue not found")
        
        # Get all employees for the venue, filtered by work area if specified
        if work_area_id:
            employees = employee_service.get_employees_by_work_area(venue_id, work_area_id)
        else:
            employees = employee_service.get_employees_by_venue(venue_id)
        
        # Filter employees by linking_id if specified
        if linking_id:
            employees = [e for e in employees if e.get('linking_id') == linking_id]
        
        # Get roster data for the week
        week_start_datetime = datetime.combine(start_date, datetime.min.time())
        roster_data = roster.get_week_roster(venue_id, week_start_datetime)
        
        # Prepare roster view data
        roster_view = []
        for employee in employees:
            # Use linking_id as the primary identifier
            employee_id = employee.get('linking_id')
            employee_shifts = {date.strftime('%a %d/%m'): None for date in week_dates}
            
            # Fill in shifts data
            if employee_id in roster_data:
                for shift in roster_data[employee_id]['shifts']:
                    shift_date = datetime.fromisoformat(shift['date']).date()
                    date_key = shift_date.strftime('%a %d/%m')
                    
                    if shift['is_rdo']:
                        employee_shifts[date_key] = 'RDO'
                    else:
                        start_time = datetime.fromisoformat(shift['start_time']).strftime('%H:%M') if shift['start_time'] else ''
                        end_time = datetime.fromisoformat(shift['end_time']).strftime('%H:%M') if shift['end_time'] else ''
                        duration = round(shift['duration_hours'], 1)
                        employee_shifts[date_key] = f"{start_time} - {end_time} ({duration}hrs)"
            
            # Use preferred name if available
            preferred_name = employee.get('preferred_name')
            if preferred_name:
                display_name = f"{preferred_name} {employee.get('last_name', '')}".strip()
            else:
                display_name = f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip()
            
            # Add additional fields for UI display
            employee_data = {
                'linking_id': employee_id,
                'name': display_name,
                'shifts': employee_shifts,
                'role_name': employee.get('role_name', ''),
                'work_area_name': employee.get('work_area_name', '')
            }
            
            roster_view.append(employee_data)
        
        # Prepare context
        context = {
            'venue': venue,
            'financial_summary': financial_summary,
            'week_dates': week_dates,
            'roster_view': roster_view,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'selected_linking_id': linking_id,
            'selected_work_area_id': work_area_id
        }
        
        return render_template('business/rostering.html', **context)
    
    except Exception as e:
        logger.error(f"Error rendering rostering page: {str(e)}")
        abort(500, description="An error occurred while loading the roster")

@rostering_bp.route('/api/rostering/shifts', methods=['GET'])
def get_shifts():
    """API endpoint to get shifts"""
    venue_id = request.args.get('venue_id')
    if not venue_id:
        return jsonify({'error': 'Venue ID is required'}), 400
    
    # Parse date range
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    
    if not start_date:
        # Default to current week
        today = datetime.now().date()
        start_date = datetime.combine(today - timedelta(days=today.weekday()), datetime.min.time())
        
    if not end_date:
        # Default to 7 days from start
        end_date = datetime.combine(start_date.date() + timedelta(days=6), datetime.max.time())
    
    # Get linking_id if provided
    linking_id = request.args.get('linking_id')
    
    # Get work_area_id if provided
    work_area_id = request.args.get('work_area_id')
    
    # Get roster data
    _, _, _, roster = get_services()
    
    # Apply filters
    shifts = roster.get_roster_for_venue(venue_id, start_date, end_date, linking_id)
    
    # Filter by work area if specified
    if work_area_id:
        shifts = [shift for shift in shifts if shift.get('work_area_id') == work_area_id]
    
    return jsonify(shifts)

@rostering_bp.route('/api/rostering/shifts', methods=['POST'])
def create_shift():
    """API endpoint to create a new shift"""
    data = request.json
    
    # Validate required fields
    required_fields = ['linking_id', 'venue_id', 'date']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # If it's an RDO, we don't need times
    is_rdo = data.get('is_rdo', False)
    if not is_rdo and ('start_time' not in data or 'end_time' not in data):
        return jsonify({'error': 'Start time and end time are required for non-RDO shifts'}), 400
    
    try:
        # Process date and times
        date = datetime.fromisoformat(data['date'].replace('Z', '+00:00'))
        
        if not is_rdo:
            start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00')).time()
            end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00')).time()
        else:
            start_time = None
            end_time = None
        
        # Create shift object
        shift = Shift(
            linking_id=data['linking_id'],
            venue_id=data['venue_id'],
            date=date,
            start_time=start_time,
            end_time=end_time,
            role=data.get('role'),
            is_rdo=is_rdo,
            notes=data.get('notes'),
            status=data.get('status', 'scheduled')
        )
        
        # Save to database
        _, _, _, roster = get_services()
        shift_id = roster.add_shift(shift)
        
        return jsonify({'success': True, 'shift_id': shift_id}), 201
    
    except ValueError as e:
        return jsonify({'error': f'Invalid data format: {str(e)}'}), 400
    except Exception as e:
        current_app.logger.error(f"Error creating shift: {str(e)}")
        return jsonify({'error': 'Failed to create shift'}), 500

@rostering_bp.route('/api/rostering/shifts/<shift_id>', methods=['PUT'])
def update_shift(shift_id):
    """API endpoint to update an existing shift"""
    data = request.json
    
    try:
        # Ensure dates and times are properly formatted
        if 'date' in data and isinstance(data['date'], str):
            data['date'] = data['date'].replace('Z', '+00:00')
        
        if 'start_time' in data and isinstance(data['start_time'], str):
            data['start_time'] = data['start_time'].replace('Z', '+00:00')
            
        if 'end_time' in data and isinstance(data['end_time'], str):
            data['end_time'] = data['end_time'].replace('Z', '+00:00')
        
        # Update in database
        _, _, _, roster = get_services()
        success = roster.update_shift(shift_id, data)
        
        if success:
            return jsonify({'success': True}), 200
        else:
            return jsonify({'error': 'Shift not found'}), 404
    
    except Exception as e:
        current_app.logger.error(f"Error updating shift: {str(e)}")
        return jsonify({'error': 'Failed to update shift'}), 500

@rostering_bp.route('/api/rostering/shifts/<shift_id>', methods=['DELETE'])
def delete_shift(shift_id):
    """API endpoint to delete a shift"""
    try:
        # Delete from database
        _, _, _, roster = get_services()
        success = roster.delete_shift(shift_id)
        
        if success:
            return jsonify({'success': True}), 200
        else:
            return jsonify({'error': 'Shift not found'}), 404
    
    except Exception as e:
        current_app.logger.error(f"Error deleting shift: {str(e)}")
        return jsonify({'error': 'Failed to delete shift'}), 500
