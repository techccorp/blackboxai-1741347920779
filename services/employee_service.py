from typing import Dict, List, Optional, Any, Union
from bson import ObjectId
from bson.errors import InvalidId
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class EmployeeService:
    """Service for managing employee data with comprehensive error handling"""
    
    def __init__(self, db):
        self.db = db
        self.collection = db[current_app.config['COLLECTION_BUSINESS_USERS']]
    
    def get_employee(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """Get employee data by ID, supporting multiple ID types"""
        if not employee_id:
            logger.warning("Empty employee ID provided")
            return None
            
        # Try first by MongoDB ObjectId
        try:
            obj_id = ObjectId(employee_id)
            employee = self.collection.find_one({'_id': obj_id})
            if employee:
                employee['_id'] = str(employee['_id'])
                return employee
        except InvalidId:
            logger.debug(f"ID '{employee_id}' is not a valid ObjectId, trying other formats")
        except Exception as e:
            logger.error(f"Error retrieving employee by ObjectId: {str(e)}")
            
        # Try by linking_id
        try:
            employee = self.collection.find_one({'linking_id': employee_id})
            if employee:
                employee['_id'] = str(employee['_id'])
                return employee
        except Exception as e:
            logger.error(f"Error retrieving employee by linking_id: {str(e)}")
            
        # Try by payroll_id
        try:
            if isinstance(employee_id, str) and employee_id.startswith('D') and '-' in employee_id:
                employee = self.collection.find_one({'payroll_id': employee_id})
                if employee:
                    employee['_id'] = str(employee['_id'])
                    return employee
        except Exception as e:
            logger.error(f"Error retrieving employee by payroll_id: {str(e)}")
            
        logger.warning(f"Employee not found with ID: {employee_id}")
        return None
    
    def get_employees_by_venue(self, venue_id: str) -> List[Dict[str, Any]]:
        """Get all employees for a venue"""
        if not venue_id:
            logger.warning("Empty venue ID provided")
            return []
            
        try:
            employees = list(self.collection.find({'venue_id': venue_id}))
            for employee in employees:
                employee['_id'] = str(employee['_id'])
            return employees
        except Exception as e:
            logger.error(f"Error retrieving employees for venue {venue_id}: {str(e)}")
            return []
    
    def get_employees_by_work_area(self, venue_id: str, work_area_id: str) -> List[Dict[str, Any]]:
        """Get employees filtered by venue and work area"""
        if not venue_id or not work_area_id:
            logger.warning("Empty venue ID or work area ID provided")
            return []
            
        try:
            employees = list(self.collection.find({
                'venue_id': venue_id,
                'work_area_id': work_area_id
            }))
            for employee in employees:
                employee['_id'] = str(employee['_id'])
            return employees
        except Exception as e:
            logger.error(f"Error retrieving employees for venue {venue_id}, work area {work_area_id}: {str(e)}")
            return []
    
    def get_employee_name(self, employee_id: str) -> str:
        """Get employee full name"""
        employee = self.get_employee(employee_id)
        if not employee:
            logger.warning(f"Unable to get name for unknown employee: {employee_id}")
            return "Unknown Employee"
        
        first_name = employee.get('first_name', '')
        last_name = employee.get('last_name', '')
        preferred_name = employee.get('preferred_name', '')
        
        # Use preferred name if available
        if preferred_name:
            return f"{preferred_name} {last_name}".strip()
        
        return f"{first_name} {last_name}".strip()
        
    def get_employee_hourly_rate(self, employee_id: str) -> float:
        """Get employee hourly rate with fallback calculations"""
        employee = self.get_employee(employee_id)
        if not employee or 'employment_details' not in employee:
            logger.warning(f"No employment details for employee: {employee_id}")
            return 0.0
            
        employment_details = employee.get('employment_details', {})
        pay_rate = employment_details.get('pay_rate', {})
        
        # Calculate hourly rate based on available pay info
        try:
            if 'hourly_rate' in pay_rate:
                return float(pay_rate['hourly_rate'])
            elif 'per_annum_rate' in pay_rate:
                # Approximate hourly rate (assuming 38-hour week, 52 weeks)
                return float(pay_rate['per_annum_rate']) / (38 * 52)
            elif 'fortnight_rate' in pay_rate:
                # Approximate hourly rate (assuming 76-hour fortnight)
                return float(pay_rate['fortnight_rate']) / 76
            elif 'monthly_rate' in pay_rate:
                # Approximate hourly rate (assuming 38-hour week, 52 weeks)
                return float(pay_rate['monthly_rate']) * 12 / (38 * 52)
        except (ValueError, TypeError) as e:
            logger.error(f"Error calculating hourly rate for {employee_id}: {str(e)}")
            
        logger.warning(f"No pay rate found for employee {employee_id}, using minimum wage")
        return 0.0  # Return 0 instead of hardcoded default
    
    def update_employee(self, employee_id: str, update_data: Dict[str, Any]) -> bool:
        """Update employee information"""
        if not employee_id or not update_data:
            logger.warning("Cannot update with empty ID or data")
            return False
            
        try:
            # Try as ObjectId first
            try:
                obj_id = ObjectId(employee_id)
                result = self.collection.update_one(
                    {'_id': obj_id},
                    {'$set': update_data}
                )
            except InvalidId:
                # Try by linking_id if not ObjectId
                result = self.collection.update_one(
                    {'linking_id': employee_id},
                    {'$set': update_data}
                )
                
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating employee {employee_id}: {str(e)}")
            return False