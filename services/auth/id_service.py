# services/auth/id_service.py
import logging
import random
import re
import uuid
from typing import Optional, Tuple, Dict, Any, Union
from pymongo import ReturnDocument, ASCENDING
from pymongo.errors import PyMongoError
from datetime import datetime

logger = logging.getLogger(__name__)

class IDGenerationError(Exception):
    """Custom exception for ID generation failures"""
    pass

class InvalidIDError(Exception):
    """Custom exception for invalid ID formats"""
    pass

class IDService:
    """Production-grade ID service with randomized sequences, validation and auto-correction"""
    
    WORK_AREA_CODES = {
        "admin": "A", "bar": "B", "cleaners": "C", "functions": "F",
        "guest services": "G", "house keeping": "H", "kitchen": "K",
        "maintenance": "M", "operations": "O", "restaurant": "R",
        "store room": "S", "venue": "V"
    }
    
    # Reverse mapping from code to area name for validation
    AREA_NAMES = {code: name for name, code in WORK_AREA_CODES.items()}

    def __init__(self, db):
        """Initialize ID service with database connection"""
        self.db = db
        self.sequences = db['id_sequences']
        self.companies = db['business_entities']
        # No need to create index on _id as it's already indexed
        
    def _get_next_sequence(self, name):
        """Get next sequence value atomically"""
        ret = self.sequences.find_one_and_update(
            {'_id': name},
            {'$inc': {'value': 1}, '$setOnInsert': {'_id': name, 'value': 0}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
            projection={'value': True}
        )
        return ret['value']
        
    def generate_company_id(self) -> str:
        """
        Generate unique 4-digit company ID with random base
        
        Returns:
            String in format 'CNY-XXXX'
        """
        while True:
            company_number = random.randint(1000, 9999)
            company_id = f"CNY-{company_number}"
            
            if not self.companies.find_one({"company_id": company_id}):
                return company_id

    def generate_venue_id(self, company_id: str) -> str:
        """
        Generate venue ID with company prefix and +11 sequence
        
        Args:
            company_id: Company ID string in format 'CNY-XXXX'
            
        Returns:
            String in format 'VEN-XXXX-XX'
            
        Raises:
            InvalidIDError: If company_id format is invalid
        """
        company_number = self._extract_id_component(company_id)
        sequence_name = f"venue_{company_number}"
        
        try:
            result = self.sequences.find_one_and_update(
                {"_id": sequence_name},
                {
                    "$setOnInsert": {"value": random.randint(10, 99)},
                    "$inc": {"value": 11}
                },
                upsert=True,
                return_document=ReturnDocument.AFTER
            )
            
            current = result["value"]
            wrapped = (current - 10) % 90 + 10  # Wrap between 10-99
            if wrapped != current:
                self.sequences.update_one(
                    {"_id": sequence_name},
                    {"$set": {"value": wrapped}}
                )
                
            return f"VEN-{company_number}-{wrapped:02d}"
        except PyMongoError as e:
            logger.error(f"Failed to generate venue ID: {str(e)}")
            raise IDGenerationError(f"Venue ID generation failed: {str(e)}")

    def generate_work_area_id(self, company_id: str, venue_id: str) -> str:
        """
        Generate work area ID with venue prefix and +11 sequence
        
        Args:
            company_id: Company ID string in format 'CNY-XXXX'
            venue_id: Venue ID string in format 'VEN-XXXX-XX'
            
        Returns:
            String in format 'WAI-XXXX-XXXX'
            
        Raises:
            InvalidIDError: If company_id or venue_id format is invalid
        """
        company_number = self._extract_id_component(company_id)
        venue_num = venue_id.split("-")[-1]
        sequence_name = f"work_area_{company_number}_{venue_num}"
        
        try:
            result = self.sequences.find_one_and_update(
                {"_id": sequence_name},
                {
                    "$setOnInsert": {"value": random.randint(10, 99)},
                    "$inc": {"value": 11}
                },
                upsert=True,
                return_document=ReturnDocument.AFTER
            )
            
            current = result["value"]
            wrapped = (current - 10) % 90 + 10  # Wrap between 10-99
            if wrapped != current:
                self.sequences.update_one(
                    {"_id": sequence_name},
                    {"$set": {"value": wrapped}}
                )
                
            return f"WAI-{company_number}-{venue_num}{wrapped:02d}"
        except PyMongoError as e:
            logger.error(f"Failed to generate work area ID: {str(e)}")
            raise IDGenerationError(f"Work area ID generation failed: {str(e)}")

    def generate_linking_id(self, company_id: str, work_area_id: str) -> str:
        """
        Generate linking ID for employees
        
        Args:
            company_id: Company ID string in format 'CNY-XXXX'
            work_area_id: Work area ID string in format 'WAI-XXXX-XXXX'
            
        Returns:
            String in format 'EMP-XXXX-XXXX-XXXXXX'
            
        Raises:
            InvalidIDError: If company_id or work_area_id format is invalid
        """
        company_number = self._extract_id_component(company_id)
        work_area_num = work_area_id.split("-")[-1]
        sequence_name = f"employee_{company_number}_{work_area_num}"
        
        try:
            result = self.sequences.find_one_and_update(
                {"_id": sequence_name},
                {
                    "$setOnInsert": {"value": 100000},
                    "$inc": {"value": 1}
                },
                upsert=True,
                return_document=ReturnDocument.AFTER
            )
            
            employee_number = result["value"]
            return f"EMP-{company_number}-{work_area_num}-{employee_number}"
        except PyMongoError as e:
            logger.error(f"Failed to generate linking ID: {str(e)}")
            raise IDGenerationError(f"Linking ID generation failed: {str(e)}")

    def generate_payroll_id(self, work_area_name: str) -> str:
        """
        Generate payroll ID in format D[AreaCode]-XXXXXX
        
        Args:
            work_area_name: Name of employee's work area
            
        Returns:
            Formatted payroll ID string
            
        Example:
            'DB-520242' for Bar employee
            
        Raises:
            ValueError: If work_area_name is not a recognized work area
        """
        work_area_name_lower = work_area_name.lower()
        if work_area_name_lower not in self.WORK_AREA_CODES:
            recognized_areas = ", ".join(self.WORK_AREA_CODES.keys())
            logger.error(f"Invalid work area '{work_area_name}'. Recognized areas: {recognized_areas}")
            raise ValueError(f"Invalid work area '{work_area_name}'. Must be one of: {recognized_areas}")
            
        area_code = self.WORK_AREA_CODES[work_area_name_lower]
        sequence_name = 'payroll_id'
        
        try:
            result = self.sequences.find_one_and_update(
                {"_id": sequence_name},
                {
                    "$setOnInsert": {"value": 100000},
                    "$inc": {"value": 1}
                },
                upsert=True,
                return_document=ReturnDocument.AFTER
            )
            
            sequence = result["value"]
            return f"D{area_code}-{sequence:06d}"
        except PyMongoError as e:
            logger.error(f"Failed to generate payroll ID: {str(e)}")
            raise IDGenerationError(f"Payroll ID generation failed: {str(e)}")

    def generate_request_id(self):
        """
        Generate unique business request ID with format: REQ-YYYYMMDD-XXXXX
        
        Returns:
            String in format 'REQ-YYYYMMDD-XXXXX'
        
        Raises:
            IDGenerationError: If request ID generation fails
        """
        try:
            date_str = datetime.now().strftime("%Y%m%d")
            sequence = self._get_next_sequence(f"request_{date_str}")
            return f"REQ-{date_str}-{sequence:05d}"
        except PyMongoError as e:
            logger.error(f"Failed to generate request ID: {str(e)}")
            # Fallback UUID for production resilience
            return f"FALLBACK-{uuid.uuid4().hex[:10]}"

    def _extract_id_component(self, id_str: str) -> str:
        """
        Extract the numeric component from an ID string
        
        Args:
            id_str: Full ID string
            
        Returns:
            Numeric component as string
            
        Raises:
            InvalidIDError: If ID format is invalid
        """
        parts = id_str.split("-")
        if len(parts) < 2 or not parts[1].isdigit():
            raise InvalidIDError(f"Invalid ID format: {id_str}")
        return parts[1]

    def extract_area_code_from_payroll_id(self, payroll_id: str) -> Optional[str]:
        """
        Extract area code from a payroll ID
        
        Args:
            payroll_id: Payroll ID to extract from
            
        Returns:
            Area code letter or None if invalid format
        """
        if not re.match(r'^D[A-Z]-\d{6}$', payroll_id):
            return None
        return payroll_id[1]

    def is_valid_area_code(self, area_code: str) -> bool:
        """
        Check if a given area code is valid
        
        Args:
            area_code: Single letter area code to validate
            
        Returns:
            True if area code is valid, False otherwise
        """
        return area_code in self.AREA_NAMES

    def get_work_area_from_payroll_id(self, payroll_id: str) -> Optional[str]:
        """
        Get work area name from a payroll ID
        
        Args:
            payroll_id: Payroll ID to analyze
            
        Returns:
            Work area name or None if area code is invalid/unknown
        """
        area_code = self.extract_area_code_from_payroll_id(payroll_id)
        if not area_code:
            return None
        return self.AREA_NAMES.get(area_code)

    def validate_payroll_id(self, payroll_id: str, work_area_name: str) -> bool:
        """
        Validate payroll ID structure and area code consistency
        
        Args:
            payroll_id: ID to validate
            work_area_name: Expected work area name
            
        Returns:
            True if valid, False otherwise
        """
        if not re.match(r'^D[A-Z]-\d{6}$', payroll_id):
            logger.warning(f"Invalid payroll ID format: {payroll_id}")
            return False
        
        area_code = payroll_id[1]
        if not self.is_valid_area_code(area_code):
            logger.warning(f"Unknown area code in payroll ID: {area_code}")
            return False
            
        expected_code = self.WORK_AREA_CODES.get(work_area_name.lower())
        if not expected_code:
            logger.warning(f"Unknown work area name: {work_area_name}")
            return False
            
        if area_code != expected_code:
            logger.warning(f"Area code mismatch: expected {expected_code} for {work_area_name}, got {area_code}")
            return False
            
        return True

    def validate_linking_id(self, linking_id: str, company_id: str, work_area_id: str) -> bool:
        """
        Validate linking ID structure and embedded identifiers
        
        Args:
            linking_id: ID to validate
            company_id: Expected company ID
            work_area_id: Expected work area ID
            
        Returns:
            True if valid, False otherwise
        """
        if not re.match(r'^EMP-\d{4}-\d{4}-\d{6}$', linking_id):
            return False
            
        try:
            company_num = self._extract_id_component(company_id)
            work_area_num = work_area_id.split("-")[-1]
            linking_parts = linking_id.split("-")
            
            return (len(linking_parts) == 4 and
                    linking_parts[0] == "EMP" and
                    linking_parts[1] == company_num and
                    linking_parts[2] == work_area_num and
                    linking_parts[3].isdigit() and
                    int(linking_parts[3]) >= 100000)
        except InvalidIDError:
            return False

    def correct_payroll_id(self, payroll_id: str, work_area: str) -> Tuple[str, bool]:
        """
        Generate a corrected payroll ID for the given work area
        
        Args:
            payroll_id: Original payroll ID
            work_area: Work area name
            
        Returns:
            Tuple of (corrected_id, was_changed)
        """
        # Extract the numeric portion of the ID
        id_match = re.match(r'^D[A-Z]-(\d+)$', payroll_id)
        if not id_match:
            return payroll_id, False
            
        id_number = id_match.group(1)
        
        # Get the correct area code for this work area
        area_code = self.WORK_AREA_CODES.get(work_area.lower())
        if not area_code:
            return payroll_id, False
            
        # Generate the corrected ID
        corrected_id = f"D{area_code}-{id_number}"
        
        # Return corrected ID and whether it changed
        return corrected_id, corrected_id != payroll_id
        
    def correct_work_email(self, work_email: str, payroll_id: str) -> Tuple[str, bool]:
        """
        Update work email to match payroll ID if needed
        
        Args:
            work_email: Original work email
            payroll_id: Employee's payroll ID
            
        Returns:
            Tuple of (corrected_email, was_changed)
        """
        if not work_email or '@' not in work_email:
            return work_email, False
            
        # Split email into local and domain parts
        local, domain = work_email.split('@', 1)
        
        # If the local part doesn't match the payroll ID, update it
        if local != payroll_id:
            corrected_email = f"{payroll_id}@{domain}"
            return corrected_email, True
        
        return work_email, False

    def auto_correct_employee_data(self, employee_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Automatically correct employee data including payroll ID and work email
        
        Args:
            employee_data: Employee data dictionary
            
        Returns:
            Corrected employee data with corrections information
        """
        corrections = {
            "payroll_id_corrected": False,
            "work_email_corrected": False
        }
        
        # Extract key fields
        payroll_id = employee_data.get("payroll_id")
        work_area = employee_data.get("work_area_name")
        work_email = employee_data.get("work_email")
        
        if not payroll_id or not work_area:
            employee_data["_corrections"] = corrections
            return employee_data
        
        # Auto-correct payroll ID if needed
        corrected_id, id_changed = self.correct_payroll_id(payroll_id, work_area)
        if id_changed:
            logger.warning(f"Auto-correcting payroll ID from {payroll_id} to {corrected_id}")
            employee_data["payroll_id"] = corrected_id
            corrections["payroll_id_corrected"] = True
            payroll_id = corrected_id
        
        # Auto-correct work email if needed
        if work_email:
            corrected_email, email_changed = self.correct_work_email(work_email, payroll_id)
            if email_changed:
                logger.warning(f"Auto-correcting work email from {work_email} to {corrected_email}")
                employee_data["work_email"] = corrected_email
                corrections["work_email_corrected"] = True
        
        employee_data["_corrections"] = corrections
        return employee_data

    def check_payroll_id_assignment(self, employee_data: Union[Dict, list]) -> Dict:
        """
        Check if payroll IDs are correctly assigned based on work areas
        
        Args:
            employee_data: Single employee dict or list of employee dicts
            
        Returns:
            Dictionary with validation results and specific errors
        """
        if isinstance(employee_data, dict):
            employee_data = [employee_data]
            
        results = {
            "total": len(employee_data),
            "correct": 0,
            "incorrect": 0,
            "issues": []
        }
        
        for emp in employee_data:
            payroll_id = emp.get('payroll_id')
            work_area = emp.get('work_area_name')
            
            if not payroll_id or not work_area:
                results['issues'].append({
                    'employee': emp.get('_id', 'Unknown'),
                    'error': 'Missing payroll_id or work_area_name'
                })
                results['incorrect'] += 1
                continue
                
            # Extract area code from payroll ID
            area_code = self.extract_area_code_from_payroll_id(payroll_id)
            if not area_code:
                results['issues'].append({
                    'employee': emp.get('_id', payroll_id),
                    'error': f'Invalid payroll ID format: {payroll_id}'
                })
                results['incorrect'] += 1
                continue
                
            # Check if area code is valid
            if not self.is_valid_area_code(area_code):
                results['issues'].append({
                    'employee': emp.get('_id', payroll_id),
                    'error': f'Unknown area code in payroll ID: {area_code}'
                })
                results['incorrect'] += 1
                continue
                
            # Get expected area code for work area
            expected_code = self.WORK_AREA_CODES.get(work_area.lower())
            if not expected_code:
                results['issues'].append({
                    'employee': emp.get('_id', payroll_id),
                    'error': f'Unknown work area: {work_area}'
                })
                results['incorrect'] += 1
                continue
                
            # Check if area code matches work area
            if area_code != expected_code:
                expected_area = self.AREA_NAMES.get(area_code, 'Unknown')
                results['issues'].append({
                    'employee': emp.get('_id', payroll_id),
                    'error': f'Area code mismatch: ID suggests "{expected_area}" but work_area is "{work_area}"'
                })
                results['incorrect'] += 1
                continue
                
            results['correct'] += 1
            
        return results
