#--------------------------------------------------------#
#    utils/business_utils.py (Updated Production Version)   #
#--------------------------------------------------------#

from datetime import datetime
import uuid
import logging
from config import Config
from pymongo.errors import PyMongoError
from services.auth.id_service import IDService

logger = logging.getLogger(__name__)

# 1. Business Core Functions ==================================================
def lookup_business(db, company_id):
    """Full business entity retrieval with error handling"""
    try:
        result = db[Config.COLLECTION_BUSINESSES].find_one(
            {'company_id': company_id},
            {'_id': 0, 'venues': 1, 'admin_user_id': 1}
        )
        if result:
            logger.debug(f"Found business: {company_id}")
            return result
        logger.warning(f"Business not found: {company_id}")
        return None
    except PyMongoError as e:
        logger.error(f"Business lookup failed: {str(e)}")
        return None

def create_business(db, admin_user_id, business_data):
    """Business creation with validation"""
    try:
        # Initialize ID service for proper ID generation
        id_service = IDService(db)
        company_id = business_data.get('company_id')
        
        # Generate company ID if not provided
        if not company_id:
            company_id = id_service.generate_company_id()
            
        business_doc = {
            'company_id': company_id,
            'admin_user_id': admin_user_id,
            'company_name': business_data['company_name'],
            'director_name': business_data.get('director_name', ''),
            'ACN': business_data.get('ACN', ''),
            'venue_type': business_data.get('venue_type', 'hospitality'),
            'status': 'setup_in_progress',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'head_office': business_data.get('head_office', {}),
            'venues': []
        }
        
        insert_result = db[Config.COLLECTION_BUSINESSES].insert_one(business_doc)
        if insert_result.inserted_id:
            logger.info(f"Created business: {company_id}")
            return business_doc
        return None
    except PyMongoError as e:
        logger.error(f"Business creation error: {str(e)}")
        return None

# 2. Venue Management ========================================================
def lookup_venue(db, venue_id):
    """Complete venue lookup with parent business context"""
    try:
        result = db[Config.COLLECTION_BUSINESSES].find_one(
            {'venues.venue_id': venue_id},
            {'company_id': 1, 'venues.$': 1}
        )
        if result and result.get('venues'):
            logger.debug(f"Found venue: {venue_id}")
            return {
                'company_id': result['company_id'],
                'venue': result['venues'][0]
            }
        logger.warning(f"Venue not found: {venue_id}")
        return None
    except PyMongoError as e:
        logger.error(f"Venue lookup error: {str(e)}")
        return None

def add_venue_to_business(db, company_id, venue_data):
    """Atomic venue addition with error handling"""
    try:
        # Initialize ID service for proper ID generation
        id_service = IDService(db)
        
        # Generate venue ID using the ID service
        venue_id = venue_data.get('venue_id')
        if not venue_id:
            venue_id = id_service.generate_venue_id(company_id)
            
        venue_doc = {
            'venue_id': venue_id,
            'venue_name': venue_data['venue_name'],
            'address': venue_data.get('address'),
            'suburb': venue_data.get('suburb'),
            'state': venue_data.get('state'),
            'post_code': venue_data.get('post_code'),
            'phone': venue_data.get('phone'),
            'email': venue_data.get('email'),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'workareas': []
        }

        # Update business with new venue
        result = db[Config.COLLECTION_BUSINESSES].update_one(
            {'company_id': company_id},
            {
                '$push': {'venues': venue_doc},
                '$set': {'updated_at': datetime.utcnow()}
            }
        )
        
        # Also create separate venue document in BUSINESS_VENUES collection
        venue_full_doc = {
            'venue_id': venue_id,
            'venue_name': venue_data['venue_name'],
            'company_id': company_id,
            'address': venue_data.get('address'),
            'suburb': venue_data.get('suburb'),
            'state': venue_data.get('state'),
            'post_code': venue_data.get('post_code'),
            'phone': venue_data.get('phone'),
            'email': venue_data.get('email'),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'workareas': []
        }
        
        db[Config.COLLECTION_BUSINESS_VENUES].insert_one(venue_full_doc)
        
        if result.modified_count > 0:
            logger.info(f"Added venue {venue_id} to business {company_id}")
            return venue_doc
        logger.warning(f"Business not found: {company_id}")
        return None
    except PyMongoError as e:
        logger.error(f"Venue addition failed: {str(e)}")
        return None

# 3. Work Area Management ====================================================
def lookup_work_area(db, work_area_id):
    """Full work area lookup with aggregation"""
    try:
        pipeline = [
            {'$unwind': '$venues'},
            {'$unwind': '$venues.workareas'},
            {'$match': {'venues.workareas.work_area_id': work_area_id}},
            {'$project': {
                'company_id': 1,
                'venue_id': '$venues.venue_id',
                'venue_name': '$venues.venue_name',
                'work_area': '$venues.workareas'
            }}
        ]
        result = list(db[Config.COLLECTION_BUSINESSES].aggregate(pipeline))
        return result[0] if result else None
    except PyMongoError as e:
        logger.error(f"Work area lookup error: {str(e)}")
        return None

def add_work_area_to_venue(db, company_id, venue_id, work_area_data):
    """Work area creation with nested updates"""
    try:
        # Initialize ID service for proper ID generation
        id_service = IDService(db)
        
        # Generate work area ID using the ID service
        work_area_id = work_area_data.get('work_area_id')
        if not work_area_id:
            work_area_id = id_service.generate_work_area_id(company_id, venue_id)
            
        work_area_doc = {
            'work_area_id': work_area_id,
            'work_area_name': work_area_data['work_area_name'],
            'description': work_area_data.get('description'),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'employees': []
        }

        # Update business document
        result = db[Config.COLLECTION_BUSINESSES].update_one(
            {'company_id': company_id, 'venues.venue_id': venue_id},
            {
                '$push': {'venues.$.workareas': work_area_doc},
                '$set': {'updated_at': datetime.utcnow()}
            }
        )
        
        # Also update the separate venue document
        db[Config.COLLECTION_BUSINESS_VENUES].update_one(
            {'venue_id': venue_id, 'company_id': company_id},
            {
                '$push': {'workareas': work_area_doc},
                '$set': {'updated_at': datetime.utcnow()}
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"Added work area {work_area_id} to venue {venue_id}")
            return work_area_doc
        logger.warning(f"Venue {venue_id} not found in business {company_id}")
        return None
    except PyMongoError as e:
        logger.error(f"Work area creation failed: {str(e)}")
        return None

# 4. User Assignments ========================================================
def assign_user_to_business(db, company_id, linking_id, role_name='employee'):
    """Complete business user assignment"""
    try:
        role_doc = db[Config.COLLECTION_BUSINESS_ROLES].find_one({'role_name': role_name})
        if not role_doc:
            logger.error(f"Role not found: {role_name}")
            return None

        business_user_doc = {
            'company_id': company_id,
            'linking_id': linking_id,
            'role_name': role_name,
            'permissions': role_doc.get('permissions', []),
            'assigned_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'status': 'active'
        }

        result = db[Config.COLLECTION_BUSINESS_USERS].update_one(
            {'company_id': company_id, 'linking_id': linking_id},
            {'$set': business_user_doc},
            upsert=True
        )
        logger.info(f"Assigned user {linking_id} to business {company_id}")
        return business_user_doc
    except PyMongoError as e:
        logger.error(f"Business assignment failed: {str(e)}")
        return None

def assign_user_to_work_area(db, company_id, venue_id, work_area_id, linking_id, role_data):
    """Atomic work area assignment with array filters"""
    try:
        employee_doc = {
            'linking_id': linking_id,
            'payroll_id': role_data.get('payroll_id'),
            'role_id': role_data.get('role_id'),
            'role_name': role_data.get('role_name', 'staff'),
            'preferred_name': role_data.get('preferred_name'),
            'assigned_at': datetime.utcnow(),
            'status': 'active'
        }

        # Update business document with new employee
        result = db[Config.COLLECTION_BUSINESSES].update_one(
            {
                'company_id': company_id,
                'venues.venue_id': venue_id,
                'venues.workareas.work_area_id': work_area_id
            },
            {
                '$push': {'venues.$[venue].workareas.$[workArea].employees': employee_doc},
                '$set': {'updated_at': datetime.utcnow()}
            },
            array_filters=[
                {'venue.venue_id': venue_id},
                {'workArea.work_area_id': work_area_id}
            ]
        )
        
        # Also update the separate venue document
        db[Config.COLLECTION_BUSINESS_VENUES].update_one(
            {
                'venue_id': venue_id,
                'company_id': company_id,
                'workareas.work_area_id': work_area_id
            },
            {
                '$push': {'workareas.$[workArea].employees': employee_doc},
                '$set': {'updated_at': datetime.utcnow()}
            },
            array_filters=[
                {'workArea.work_area_id': work_area_id}
            ]
        )
        
        # Create or update employee document in BUSINESS_USERS collection
        employee_full_doc = {
            'linking_id': linking_id,
            'payroll_id': role_data.get('payroll_id'),
            'company_id': company_id,
            'venue_id': venue_id,
            'work_area_id': work_area_id,
            'role_id': role_data.get('role_id'),
            'role_name': role_data.get('role_name', 'staff'),
            'preferred_name': role_data.get('preferred_name'),
            'updated_at': datetime.utcnow()
        }
        
        db[Config.COLLECTION_BUSINESS_USERS].update_one(
            {'linking_id': linking_id},
            {'$set': employee_full_doc},
            upsert=True
        )
        
        if result.modified_count > 0:
            logger.info(f"Assigned user {linking_id} to work area {work_area_id}")
            return True
        logger.warning(f"Assignment target not found: {work_area_id}")
        return False
    except PyMongoError as e:
        logger.error(f"Work area assignment failed: {str(e)}")
        return False

# 5. Business Operations =====================================================
def get_business_hierarchy(db, company_id):
    """Complete hierarchy aggregation"""
    try:
        pipeline = [
            {'$match': {'company_id': company_id}},
            {'$lookup': {
                'from': Config.COLLECTION_BUSINESS_USERS,
                'localField': 'company_id',
                'foreignField': 'company_id',
                'as': 'employees'
            }},
            {'$unwind': '$venues'},
            {'$unwind': '$venues.workareas'},
            {'$project': {
                'company_id': 1,
                'company_name': 1,
                'venue': '$venues',
                'work_area': '$venues.workareas',
                'employees': 1
            }}
        ]
        return list(db[Config.COLLECTION_BUSINESSES].aggregate(pipeline))
    except PyMongoError as e:
        logger.error(f"Hierarchy fetch failed: {str(e)}")
        return []

def update_business_status(db, company_id, new_status):
    """Status update with validation"""
    try:
        result = db[Config.COLLECTION_BUSINESSES].update_one(
            {'company_id': company_id},
            {'$set': {'status': new_status, 'updated_at': datetime.utcnow()}}
        )
        if result.modified_count > 0:
            logger.info(f"Updated {company_id} status to {new_status}")
            return True
        logger.warning(f"Business not found: {company_id}")
        return False
    except PyMongoError as e:
        logger.error(f"Status update failed: {str(e)}")
        return False

def validate_business_structure(db, company_id):
    """Comprehensive structure validation"""
    try:
        business = lookup_business(db, company_id)
        issues = []
        
        if not business:
            return False, ["Business not found"]

        required_fields = ['company_name', 'admin_user_id', 'venues']
        for field in required_fields:
            if field not in business:
                issues.append(f"Missing required field: {field}")

        if not isinstance(business.get('venues'), list):
            issues.append("Venues must be a list")
        else:
            for venue in business['venues']:
                if 'venue_id' not in venue:
                    issues.append(f"Venue missing ID: {venue.get('venue_name', 'Unnamed')}")
                if 'workareas' not in venue:
                    issues.append(f"Venue missing work areas: {venue.get('venue_id', 'No ID')}")

        return (len(issues) == 0, issues)
    except PyMongoError as e:
        logger.error(f"Validation failed: {str(e)}")
        return False, [f"Validation error: {str(e)}"]