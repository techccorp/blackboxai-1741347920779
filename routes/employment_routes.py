from flask import Blueprint, render_template, jsonify, request, current_app
from http import HTTPStatus
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import json

employment = Blueprint('employment', __name__)

# Centralized constants for validation
VALID_EMPLOYEE_SECTIONS = ['personal', 'employment', 'journals', 'onboarding', 'documents']
VALID_PERSONAL_TABS = ['personal_details', 'contact', 'login_information']
VALID_WORK_TABS = ['work_details', 'pay_details', 'working_hours', 'leave_entitlements']
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

# Personal Profile Routes
@employment.route('/employee_profile/personal', methods=['GET'])
def personal():
    """Render personal section view mode."""
    return render_template('partials/employee_profile/personal.html')

@employment.route('/employee_profile/personal/edit', methods=['GET'])
def edit_personal_template():
    """Render the main personal edit template."""
    return render_template(
        'components/employee_profile/personal/edit_personal.html', 
        active_tab='personal_details'
    )

@employment.route('/employee_profile/personal/tabs/<tab>', methods=['GET'])
def personal_tab_content(tab):
    """Render specific personal tab content."""
    if tab not in VALID_PERSONAL_TABS:
        return jsonify({'error': 'Invalid tab'}), HTTPStatus.BAD_REQUEST
    
    return render_template(
        f'components/employee_profile/personal/tabs/{tab}.html'
    )

@employment.route('/api/personal/upload-photo', methods=['POST'])
def upload_personal_photo():
    """Handle personal photo upload."""
    try:
        if 'photo' not in request.files:
            return jsonify({'error': 'No file provided'}), HTTPStatus.BAD_REQUEST

        file = request.files['photo']
        if not file or not file.filename:
            return jsonify({'error': 'No file selected'}), HTTPStatus.BAD_REQUEST

        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), HTTPStatus.BAD_REQUEST

        if len(file.read()) > MAX_FILE_SIZE:
            return jsonify({'error': 'File too large'}), HTTPStatus.BAD_REQUEST
        
        file.seek(0)  # Reset file pointer after reading

        filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        return jsonify({
            'status': 'success',
            'message': 'Photo uploaded successfully',
            'url': f"/uploads/{filename}"
        })

    except Exception as e:
        current_app.logger.error(f"Photo upload error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to upload photo'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@employment.route('/api/personal/update', methods=['POST'])
def update_personal_details():
    """Handle personal details update."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['firstName', 'lastName', 'dateOfBirth']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'status': 'error',
                    'message': f'{field} is required'
                }), HTTPStatus.BAD_REQUEST

        # Add your update logic here
        
        return jsonify({
            'status': 'success',
            'message': 'Personal details updated successfully'
        })

    except Exception as e:
        current_app.logger.error(f"Update personal details error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to update personal details'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

# Work Profile Routes
@employment.route('/employee_profile/work', methods=['GET'])
def work():
    """Render work section view mode."""
    return render_template('partials/employee_profile/employment.html')

@employment.route('/employee_profile/work/edit', methods=['GET'])
def edit_work_template():
    """Render the main work edit template."""
    return render_template(
        'components/employee_profile/work/edit_work.html', 
        active_tab='work_details'
    )

@employment.route('/employee_profile/work/tabs/<tab>', methods=['GET'])
def work_tab_content(tab):
    """Render specific work tab content."""
    if tab not in VALID_WORK_TABS:
        return jsonify({'error': 'Invalid tab'}), HTTPStatus.BAD_REQUEST
    
    return render_template(
        f'components/employee_profile/work/tabs/{tab}.html'
    )

@employment.route('/api/work/update', methods=['POST'])
def update_work_details():
    """Handle work details update."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['accessLevel', 'hiredOn']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'status': 'error',
                    'message': f'{field} is required'
                }), HTTPStatus.BAD_REQUEST

        # Add your update logic here
        
        return jsonify({
            'status': 'success',
            'message': 'Work details updated successfully'
        })

    except Exception as e:
        current_app.logger.error(f"Update work details error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to update work details'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

# 2FA Routes
@employment.route('/api/initialize-2fa', methods=['POST'])
def initialize_2fa():
    """Initialize 2FA setup."""
    try:
        # Add 2FA initialization logic here
        return jsonify({
            'status': 'success',
            'qrCode': 'QR_CODE_DATA_URL',
            'secret': 'SECRET_KEY'
        })
    except Exception as e:
        current_app.logger.error(f"2FA initialization error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to initialize 2FA'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

# Other Section Routes
@employment.route('/employee_profile/<section>', methods=['GET'])
def employee_profile_section(section):
    """Render main section templates."""
    if section not in VALID_EMPLOYEE_SECTIONS:
        return "Section not found", HTTPStatus.NOT_FOUND
    
    return render_template(f'partials/employee_profile/{section}.html')

@employment.route('/employee_profile/journals', methods=['GET'])
def journals():
    """Render journals section."""
    return render_template('partials/employee_profile/journals.html')

@employment.route('/employee_profile/onboarding', methods=['GET'])
def onboarding():
    """Render onboarding section."""
    return render_template('partials/employee_profile/onboarding.html')

@employment.route('/employee_profile/documents', methods=['GET'])
def documents():
    """Render documents section."""
    return render_template('partials/employee_profile/documents.html')

# Error Handlers
@employment.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return jsonify({
        'status': 'error',
        'message': 'Resource not found'
    }), HTTPStatus.NOT_FOUND

@employment.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    current_app.logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), HTTPStatus.INTERNAL_SERVER_ERROR

# Before Request Handler
@employment.before_request
def before_request():
    """Handle pre-request tasks."""
    # Add authentication check if needed
    pass

# After Request Handler
@employment.after_request
def after_request(response):
    """Handle post-request tasks."""
    # Add CORS headers if needed
    return response