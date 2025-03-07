"""
Business Users model module for Le Repertoire application.

This module provides data models and database interactions for business users,
including CRUD operations, authentication, and permission handling.
"""
from typing import Dict, List, Optional, Union, Any, Tuple
from datetime import datetime, timezone
from bson import ObjectId
from pymongo import MongoClient, UpdateOne, ASCENDING
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import PyMongoError, DuplicateKeyError, BulkWriteError
from flask import current_app, g
import logging
from decimal import Decimal
import threading

# Import utility functions at module level to avoid repeated imports
from utils.auth.auth_utils import hash_password, check_password, validate_payroll_id
from utils.auth.auth_utils import hash_password, check_password, validate_payroll_id
from utils.audit_logger import AuditLogger
from utils.payroll.taxRates_utils import calculate_period_amounts, get_user_ytd_amounts
from utils.payroll.accrualRates_utils import get_user_leave_summary, calculate_leave_accrual, calculate_service_period

logger = logging.getLogger(__name__)

# Module level constants
LEAVE_TYPES = {
    'annual_leave': 'holiday',
    'sick_leave': 'sick',
    'personal_leave': 'carers',
    'bereavement_leave': 'bereavement'
}

# Thread local storage for connection management
_thread_local = threading.local()

class BusinessUserError(Exception):
    """Base exception for BusinessUserModel errors."""
    def __init__(self, message, error_code=None, details=None):
        self.message = message
        self.error_code = error_code
        self.details = details
        super().__init__(self.message)


class BusinessUserModel:
    """
    Business User model for database operations.
    
    Provides methods for:
    - User creation, retrieval, update, deletion
    - Authentication
    - Leave management
    - Employment details
    - Role and permission access
    """
    
    def __init__(self, db=None):
        """
        Initialize the Business User model.
        
        Args:
            db: MongoDB database instance (optional)
        """
        self.db = db or self._get_db()
        self.collection = self.db.business_users
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Ensure all required indexes exist."""
        try:
            # Core indexes
            self.collection.create_index([("payroll_id", ASCENDING)], unique=True)
            self.collection.create_index([("work_email", ASCENDING)])
            self.collection.create_index([("linking_id", ASCENDING)])
            
            # Business context indexes
            self.collection.create_index([("company_id", ASCENDING), ("status", ASCENDING)])
            self.collection.create_index([("venue_id", ASCENDING), ("status", ASCENDING)])
            self.collection.create_index([("work_area_id", ASCENDING), ("status", ASCENDING)])
            
            # Search and filter indexes
            self.collection.create_index([("role_id", ASCENDING)])
            self.collection.create_index([("last_login", ASCENDING)])
            self.collection.create_index([("first_name", ASCENDING), ("last_name", ASCENDING)])
            
            logger.info("BusinessUserModel indexes ensured")
        except Exception as e:
            logger.warning(f"Error ensuring indexes: {str(e)}")
    
    def _to_decimal(self, value: Union[Decimal, float, str, int]) -> Decimal:
        """
        Convert value to Decimal consistently.
        
        Args:
            value: Value to convert
            
        Returns:
            Decimal: Converted value
        """
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))
    
    def _handle_mongo_date(self, date_value: Union[datetime, Dict, str]) -> datetime:
        """
        Consistently handle MongoDB date formats.
        
        Args:
            date_value: Date in various formats
            
        Returns:
            datetime: Converted datetime object
            
        Raises:
            ValueError: If date format is unsupported
        """
        if isinstance(date_value, datetime):
            return date_value
        elif isinstance(date_value, dict) and '$date' in date_value:
            date_str = date_value['$date']
            # Handle both ISO format with Z and without
            if isinstance(date_str, str):
                if date_str.endswith('Z'):
                    date_str = date_str[:-1]
                return datetime.fromisoformat(date_str)
            # Handle numeric timestamp (milliseconds since epoch)
            elif isinstance(date_str, (int, float)):
                return datetime.fromtimestamp(date_str / 1000.0, tz=timezone.utc)
        elif isinstance(date_value, str):
            try:
                return datetime.fromisoformat(date_value)
            except ValueError:
                # Try parsing with different format if ISO format fails
                try:
                    from dateutil import parser
                    return parser.parse(date_value)
                except:
                    raise ValueError(f"Unsupported date string format: {date_value}")
        
        raise ValueError(f"Unsupported date format: {type(date_value)}")
    
    def find_by_id(self, user_id: Union[str, ObjectId]) -> Optional[Dict]:
        """
        Find a user by MongoDB ID.
        
        Args:
            user_id: User's MongoDB ID
            
        Returns:
            Dict: User document or None if not found
        """
        try:
            # Convert string ID to ObjectId if needed
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            
            return self.collection.find_one({"_id": user_id})
        except Exception as e:
            logger.error(f"Error finding user by ID: {str(e)}")
            return None
    
    def find_by_payroll_id(self, payroll_id: str) -> Optional[Dict]:
        """
        Find a user by payroll ID.
        
        Args:
            payroll_id: User's payroll ID
            
        Returns:
            Dict: User document or None if not found
        """
        try:
            return self.collection.find_one({"payroll_id": payroll_id})
        except Exception as e:
            logger.error(f"Error finding user by payroll ID: {str(e)}")
            return None
    
    def find_by_linking_id(self, linking_id: str) -> Optional[Dict]:
        """
        Find a user by linking ID.
        
        Args:
            linking_id: User's linking ID
            
        Returns:
            Dict: User document or None if not found
        """
        try:
            return self.collection.find_one({"linking_id": linking_id})
        except Exception as e:
            logger.error(f"Error finding user by linking ID: {str(e)}")
            return None
    
    def find_by_email(self, email: str) -> Optional[Dict]:
        """
        Find a user by work email.
        
        Args:
            email: User's work email
            
        Returns:
            Dict: User document or None if not found
        """
        try:
            return self.collection.find_one({"work_email": email})
        except Exception as e:
            logger.error(f"Error finding user by email: {str(e)}")
            return None
    
    def find_by_company(self, company_id: str, active_only: bool = True) -> List[Dict]:
        """
        Find all users for a specific company.
        
        Args:
            company_id: Company ID
            active_only: Only include active users if True
            
        Returns:
            List[Dict]: List of user documents
        """
        try:
            query = {"company_id": company_id}
            if active_only:
                query["status"] = {"$ne": "inactive"}
                
            return list(self.collection.find(query).hint([("company_id", ASCENDING), ("status", ASCENDING)]))
        except Exception as e:
            logger.error(f"Error finding users by company: {str(e)}")
            return []
    
    def find_by_venue(self, venue_id: str, active_only: bool = True) -> List[Dict]:
        """
        Find all users for a specific venue.
        
        Args:
            venue_id: Venue ID
            active_only: Only include active users if True
            
        Returns:
            List[Dict]: List of user documents
        """
        try:
            query = {"venue_id": venue_id}
            if active_only:
                query["status"] = {"$ne": "inactive"}
                
            return list(self.collection.find(query).hint([("venue_id", ASCENDING), ("status", ASCENDING)]))
        except Exception as e:
            logger.error(f"Error finding users by venue: {str(e)}")
            return []
    
    def find_by_work_area(self, work_area_id: str, active_only: bool = True) -> List[Dict]:
        """
        Find all users for a specific work area.
        
        Args:
            work_area_id: Work area ID
            active_only: Only include active users if True
            
        Returns:
            List[Dict]: List of user documents
        """
        try:
            query = {"work_area_id": work_area_id}
            if active_only:
                query["status"] = {"$ne": "inactive"}
                
            return list(self.collection.find(query).hint([("work_area_id", ASCENDING), ("status", ASCENDING)]))
        except Exception as e:
            logger.error(f"Error finding users by work area: {str(e)}")
            return []
    
    def find_by_role(self, role_id: str, company_id: Optional[str] = None) -> List[Dict]:
        """
        Find all users with a specific role.
        
        Args:
            role_id: Role ID
            company_id: Optional company ID to filter results
            
        Returns:
            List[Dict]: List of user documents
        """
        try:
            query = {"role_id": role_id}
            if company_id:
                query["company_id"] = company_id
                
            return list(self.collection.find(query).hint([("role_id", ASCENDING)]))
        except Exception as e:
            logger.error(f"Error finding users by role: {str(e)}")
            return []
    
    def authenticate(self, payroll_id: str, password: str) -> Optional[Dict]:
        """
        Authenticate a user with payroll ID and password.
        
        Args:
            payroll_id: User's payroll ID
            password: User's password
            
        Returns:
            Dict: User document if authentication successful, None otherwise
            
        Raises:
            BusinessUserError: For specific authentication failures
        """
        try:
            # Validate payroll ID format
            if not validate_payroll_id(payroll_id):
                logger.warning(f"Invalid payroll ID format: {payroll_id}")
                raise BusinessUserError(
                    "Invalid payroll ID format", 
                    error_code="INVALID_PAYROLL_ID"
                )
            
            # Find user
            user = self.find_by_payroll_id(payroll_id)
            if not user:
                logger.warning(f"User not found with payroll ID: {payroll_id}")
                raise BusinessUserError(
                    "Invalid payroll ID or password", 
                    error_code="AUTH_FAILED"
                )
            
            # Check if user is active
            if user.get('status') == 'inactive':
                logger.warning(f"Inactive user attempted login: {payroll_id}")
                raise BusinessUserError(
                    "Account is inactive or has been disabled", 
                    error_code="ACCOUNT_INACTIVE"
                )
            
            # Verify password
            if not check_password(user.get('password', ''), password):
                logger.warning(f"Invalid password for payroll ID: {payroll_id}")
                raise BusinessUserError(
                    "Invalid payroll ID or password", 
                    error_code="AUTH_FAILED"
                )
            
            # Authentication successful
            return user
        except BusinessUserError:
            # Re-raise business logic errors
            raise
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return None
    
    def create(self, user_data: Dict) -> Optional[str]:
        """
        Create a new business user.
        
        Args:
            user_data: User data dictionary
            
        Returns:
            str: ID of the created user, or None if creation failed
            
        Raises:
            BusinessUserError: For validation or creation errors
        """
        try:
            # Ensure required fields
            required_fields = [
                'payroll_id', 'company_id', 'company_name', 'venue_id', 'venue_name',
                'work_area_id', 'work_area_name', 'role_id', 'role_name',
                'first_name', 'last_name', 'work_email', 'password'
            ]
            
            missing_fields = [field for field in required_fields if field not in user_data]
            if missing_fields:
                raise BusinessUserError(
                    f"Missing required fields: {', '.join(missing_fields)}",
                    error_code="MISSING_FIELDS"
                )
            
            # Validate payroll ID
            if not validate_payroll_id(user_data['payroll_id']):
                raise BusinessUserError(
                    f"Invalid payroll ID format: {user_data['payroll_id']}",
                    error_code="INVALID_PAYROLL_ID"
                )
            
            # Check for existing user with same payroll ID
            existing_user = self.find_by_payroll_id(user_data['payroll_id'])
            if existing_user:
                raise BusinessUserError(
                    f"User with payroll ID already exists: {user_data['payroll_id']}",
                    error_code="DUPLICATE_PAYROLL_ID"
                )
            
            # Check for existing email
            if self.find_by_email(user_data['work_email']):
                raise BusinessUserError(
                    f"User with email already exists: {user_data['work_email']}",
                    error_code="DUPLICATE_EMAIL"
                )
            
            # Hash password
            if 'password' in user_data:
                user_data['password'] = hash_password(user_data['password'])
            
            # Set default fields
            user_data['created_at'] = datetime.utcnow()
            user_data['status'] = user_data.get('status', 'active')
            
            # Set default employment details if not provided
            if 'employment_details' not in user_data:
                user_data['employment_details'] = {
                    'hired_date': datetime.utcnow(),
                    'employment_type': 'full time',
                    'pay_type': 'salary',
                    'pay_rate': {}
                }
            
            # Set default leave entitlements if not provided
            if 'leave_entitlements' not in user_data:
                user_data['leave_entitlements'] = {
                    'holiday_accrued': 0,
                    'holiday_taken': 0,
                    'sick_accrued': 0,
                    'sick_taken': 0,
                    'carers_accrued': 0,
                    'carers_taken': 0,
                    'bereavement_accrued': 0,
                    'bereavement_taken': 0,
                    'maternity_entitlement': 0,
                    'maternity_taken': 0,
                    'unpaid_leave_taken': 0
                }
            
            # Set default accrued employment if not provided
            if 'accrued_employment' not in user_data:
                user_data['accrued_employment'] = {
                    'days_employed': 0,
                    'unpaid_leave': 0,
                    'tax_withheld': 0,
                    'salary_ytd': 0,
                    'tax_withheld_ytd': 0
                }
                
            # Insert user
            result = self.collection.insert_one(user_data)
            if result.inserted_id:
                logger.info(f"Created business user: {user_data['payroll_id']}")
                return str(result.inserted_id)
            
            return None
        except DuplicateKeyError as e:
            logger.error(f"Duplicate key error creating user: {str(e)}")
            raise BusinessUserError(
                "User with duplicate key already exists",
                error_code="DUPLICATE_KEY",
                details=str(e)
            )
        except BusinessUserError:
            # Re-raise business logic errors
            raise
        except Exception as e:
            logger.error(f"Error creating business user: {str(e)}")
            raise BusinessUserError(
                "Failed to create user",
                error_code="CREATE_FAILED",
                details=str(e)
            )
    
    def update(self, user_id: Union[str, ObjectId], update_data: Dict) -> bool:
        """
        Update a business user.
        
        Args:
            user_id: User's MongoDB ID
            update_data: Dictionary of fields to update
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Convert string ID to ObjectId if needed
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            
            # Don't allow updating certain fields
            forbidden_fields = ['_id', 'payroll_id', 'created_at']
            for field in forbidden_fields:
                if field in update_data:
                    del update_data[field]
            
            # Hash password if present
            if 'password' in update_data:
                update_data['password'] = hash_password(update_data['password'])
            
            # Add updated timestamp
            update_data['updated_at'] = datetime.utcnow()
            
            result = self.collection.update_one(
                {"_id": user_id},
                {"$set": update_data}
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Updated user with ID: {user_id}")
            else:
                logger.warning(f"No changes made for user ID: {user_id}")
                
            return success
        except Exception as e:
            logger.error(f"Error updating business user: {str(e)}")
            return False
    
    def update_by_payroll_id(self, payroll_id: str, update_data: Dict) -> bool:
        """
        Update a business user by payroll ID.
        
        Args:
            payroll_id: User's payroll ID
            update_data: Dictionary of fields to update
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Don't allow updating certain fields
            forbidden_fields = ['_id', 'payroll_id', 'created_at']
            for field in forbidden_fields:
                if field in update_data:
                    del update_data[field]
            
            # Hash password if present
            if 'password' in update_data:
                update_data['password'] = hash_password(update_data['password'])
            
            # Add updated timestamp
            update_data['updated_at'] = datetime.utcnow()
            
            result = self.collection.update_one(
                {"payroll_id": payroll_id},
                {"$set": update_data}
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Updated user with payroll ID: {payroll_id}")
            else:
                logger.warning(f"No changes made for payroll ID: {payroll_id}")
                
            return success
        except Exception as e:
            logger.error(f"Error updating business user by payroll ID: {str(e)}")
            return False
    
    def update_employment_details(self, payroll_id: str, employment_details: Dict) -> bool:
        """
        Update a user's employment details.
        
        Args:
            payroll_id: User's payroll ID
            employment_details: Employment details dictionary
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            result = self.collection.update_one(
                {"payroll_id": payroll_id},
                {
                    "$set": {
                        "employment_details": employment_details,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating employment details: {str(e)}")
            return False
    
    def update_leave_entitlements(self, payroll_id: str, leave_entitlements: Dict) -> bool:
        """
        Update a user's leave entitlements.
        
        Args:
            payroll_id: User's payroll ID
            leave_entitlements: Leave entitlements dictionary
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            result = self.collection.update_one(
                {"payroll_id": payroll_id},
                {
                    "$set": {
                        "leave_entitlements": leave_entitlements,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating leave entitlements: {str(e)}")
            return False
    
    def update_accrued_employment(self, payroll_id: str, accrued_employment: Dict) -> bool:
        """
        Update a user's accrued employment details.
        
        Args:
            payroll_id: User's payroll ID
            accrued_employment: Accrued employment dictionary
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            result = self.collection.update_one(
                {"payroll_id": payroll_id},
                {
                    "$set": {
                        "accrued_employment": accrued_employment,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating accrued employment: {str(e)}")
            return False
    
    def deactivate(self, payroll_id: str) -> bool:
        """
        Deactivate a business user.
        
        Args:
            payroll_id: User's payroll ID
            
        Returns:
            bool: True if deactivation successful, False otherwise
        """
        try:
            result = self.collection.update_one(
                {"payroll_id": payroll_id},
                {
                    "$set": {
                        "status": "inactive",
                        "deactivated_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Deactivated user with payroll ID: {payroll_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error deactivating business user: {str(e)}")
            return False
    
    def reactivate(self, payroll_id: str) -> bool:
        """
        Reactivate a business user.
        
        Args:
            payroll_id: User's payroll ID
            
        Returns:
            bool: True if reactivation successful, False otherwise
        """
        try:
            result = self.collection.update_one(
                {"payroll_id": payroll_id},
                {
                    "$set": {
                        "status": "active",
                        "reactivated_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    },
                    "$unset": {
                        "deactivated_at": ""
                    }
                }
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Reactivated user with payroll ID: {payroll_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error reactivating business user: {str(e)}")
            return False
    
    def delete(self, payroll_id: str) -> bool:
        """
        Delete a business user.
        
        Args:
            payroll_id: User's payroll ID
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            result = self.collection.delete_one({"payroll_id": payroll_id})
            success = result.deleted_count > 0
            
            if success:
                logger.info(f"Deleted user with payroll ID: {payroll_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error deleting business user: {str(e)}")
            return False
    
    def change_password(self, payroll_id: str, new_password: str) -> bool:
        """
        Change a user's password.
        
        Args:
            payroll_id: User's payroll ID
            new_password: New password (will be hashed)
            
        Returns:
            bool: True if password change successful, False otherwise
        """
        try:
            hashed_password = hash_password(new_password)
            
            result = self.collection.update_one(
                {"payroll_id": payroll_id},
                {
                    "$set": {
                        "password": hashed_password,
                        "password_updated_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Changed password for user with payroll ID: {payroll_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error changing password: {str(e)}")
            return False
    
    def update_last_login(self, payroll_id: str) -> bool:
        """
        Update a user's last login timestamp.
        
        Args:
            payroll_id: User's payroll ID
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            result = self.collection.update_one(
                {"payroll_id": payroll_id},
                {
                    "$set": {
                        "last_login": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating last login: {str(e)}")
            return False
    
    def add_permission(self, payroll_id: str, permission: str) -> bool:
        """
        Add a permission to a user.
        
        Args:
            payroll_id: User's payroll ID
            permission: Permission to add
            
        Returns:
            bool: True if addition successful, False otherwise
        """
        try:
            result = self.collection.update_one(
                {"payroll_id": payroll_id},
                {
                    "$addToSet": {
                        "permissions": permission
                    },
                    "$set": {
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error adding permission: {str(e)}")
            return False
    
    def remove_permission(self, payroll_id: str, permission: str) -> bool:
        """
        Remove a permission from a user.
        
        Args:
            payroll_id: User's payroll ID
            permission: Permission to remove
            
        Returns:
            bool: True if removal successful, False otherwise
        """
        try:
            result = self.collection.update_one(
                {"payroll_id": payroll_id},
                {
                    "$pull": {
                        "permissions": permission
                    },
                    "$set": {
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error removing permission: {str(e)}")
            return False
    
    def get_permissions(self, payroll_id: str) -> List[str]:
        """
        Get a user's permissions.
        
        Args:
            payroll_id: User's payroll ID
            
        Returns:
            List[str]: List of permissions
        """
        try:
            user = self.find_by_payroll_id(payroll_id)
            if user:
                return user.get('permissions', [])
            return []
        except Exception as e:
            logger.error(f"Error getting permissions: {str(e)}")
            return []
    
    def assign_to_venue(self, payroll_id: str, venue_id: str, venue_name: str) -> bool:
        """
        Assign a user to a venue.
        
        Args:
            payroll_id: User's payroll ID
            venue_id: Venue ID
            venue_name: Venue name
            
        Returns:
            bool: True if assignment successful, False otherwise
        """
        try:
            result = self.collection.update_one(
                {"payroll_id": payroll_id},
                {
                    "$set": {
                        "venue_id": venue_id,
                        "venue_name": venue_name,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Assigned user {payroll_id} to venue {venue_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error assigning user to venue: {str(e)}")
            return False
    
    def assign_to_work_area(self, payroll_id: str, work_area_id: str, work_area_name: str) -> bool:
        """
        Assign a user to a work area.
        
        Args:
            payroll_id: User's payroll ID
            work_area_id: Work area ID
            work_area_name: Work area name
            
        Returns:
            bool: True if assignment successful, False otherwise
        """
        try:
            result = self.collection.update_one(
                {"payroll_id": payroll_id},
                {
                    "$set": {
                        "work_area_id": work_area_id,
                        "work_area_name": work_area_name,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Assigned user {payroll_id} to work area {work_area_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error assigning user to work area: {str(e)}")
            return False
    
    def assign_role(self, payroll_id: str, role_id: str, role_name: str) -> bool:
        """
        Assign a role to a user.
        
        Args:
            payroll_id: User's payroll ID
            role_id: Role ID
            role_name: Role name
            
        Returns:
            bool: True if assignment successful, False otherwise
        """
        try:
            result = self.collection.update_one(
                {"payroll_id": payroll_id},
                {
                    "$set": {
                        "role_id": role_id,
                        "role_name": role_name,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Assigned role {role_id} to user {payroll_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error assigning role: {str(e)}")
            return False
    
    def get_leave_summary(self, payroll_id: str) -> Optional[Dict]:
        """
        Get a user's leave summary.
        
        Args:
            payroll_id: User's payroll ID
            
        Returns:
            Dict: Leave summary or None if user not found
        """
        try:
            user = self.find_by_payroll_id(payroll_id)
            if not user:
                return None
            
            return get_user_leave_summary(user)
        except Exception as e:
            logger.error(f"Error getting leave summary: {str(e)}")
            return None
    
    def get_payroll_details(self, payroll_id: str, pay_frequency: str = 'fortnightly') -> Optional[Dict]:
        """
        Get a user's payroll details.
        
        Args:
            payroll_id: User's payroll ID
            pay_frequency: Pay frequency ('weekly', 'fortnightly', 'monthly')
            
        Returns:
            Dict: Payroll details or None if user not found
        """
        try:
            user = self.find_by_payroll_id(payroll_id)
            if not user:
                return None
            
            # Get annual salary
            employment_details = user.get('employment_details', {})
            pay_rate = employment_details.get('pay_rate', {})
            annual_salary = self._to_decimal(pay_rate.get('per_annum_rate', 0))
            
            # Calculate period amounts
            period_amounts = calculate_period_amounts(annual_salary, pay_frequency)
            
            # Get YTD amounts
            ytd_amounts = get_user_ytd_amounts(user)
            
            return {
                'period_amounts': period_amounts,
                'ytd_amounts': ytd_amounts
            }
        except Exception as e:
            logger.error(f"Error getting payroll details: {str(e)}")
            return None
    
    def search_users(
        self,
        company_id: Optional[str] = None,
        venue_id: Optional[str] = None,
        work_area_id: Optional[str] = None,
        role_id: Optional[str] = None,
        search_text: Optional[str] = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Search for business users with various filters.
        
        Args:
            company_id: Filter by company ID
            venue_id: Filter by venue ID
            work_area_id: Filter by work area ID
            role_id: Filter by role ID
            search_text: Search in name and email fields
            active_only: Only include active users if True
            skip: Number of results to skip (for pagination)
            limit: Maximum number of results to return
            
        Returns:
            Dict: Dict with 'users' list and 'total' count
        """
        try:
            pipeline = []
            
            # Match stage for filtering
            match_stage = {}
            
            if company_id:
                match_stage['company_id'] = company_id
            
            if venue_id:
                match_stage['venue_id'] = venue_id
            
            if work_area_id:
                match_stage['work_area_id'] = work_area_id
            
            if role_id:
                match_stage['role_id'] = role_id
            
            if active_only:
                match_stage['status'] = {'$ne': 'inactive'}
            
            if match_stage:
                pipeline.append({'$match': match_stage})
            
            # Text search stage
            if search_text:
                pipeline.append({
                    '$match': {
                        '$or': [
                            {'first_name': {'$regex': search_text, '$options': 'i'}},
                            {'last_name': {'$regex': search_text, '$options': 'i'}},
                            {'preferred_name': {'$regex': search_text, '$options': 'i'}},
                            {'work_email': {'$regex': search_text, '$options': 'i'}},
                            {'payroll_id': {'$regex': search_text, '$options': 'i'}}
                        ]
                    }
                })
            
            # Sort by name
            pipeline.append({'$sort': {'last_name': 1, 'first_name': 1}})
            
            # Facet for pagination and total count
            pipeline.append({
                '$facet': {
                    'total': [{'$count': 'count'}],
                    'users': [{'$skip': skip}, {'$limit': limit}]
                }
            })
            
            # Execute pipeline with hint if appropriate
            hint = None
            if company_id and active_only:
                hint = [("company_id", ASCENDING), ("status", ASCENDING)]
            elif venue_id and active_only:
                hint = [("venue_id", ASCENDING), ("status", ASCENDING)]
            elif work_area_id and active_only:
                hint = [("work_area_id", ASCENDING), ("status", ASCENDING)]
            elif role_id:
                hint = [("role_id", ASCENDING)]
            
            cursor = self.collection.aggregate(pipeline, hint=hint)
            
            result = list(cursor)
            
            if not result:
                return {'users': [], 'total': 0}
            
            data = result[0]
            return {
                'users': data.get('users', []),
                'total': data.get('total', [{'count': 0}])[0]['count'] if data.get('total') else 0
            }
            
        except Exception as e:
            logger.error(f"Error searching users: {str(e)}")
            return {'users': [], 'total': 0}
    
    def update_ytd_earnings(self, payroll_id: str, amount: Union[Decimal, float, str]) -> bool:
        """
        Update a user's year-to-date earnings.
        
        Args:
            payroll_id: User's payroll ID
            amount: Amount to add to YTD earnings
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Convert amount to Decimal and then to float for MongoDB
            amount_decimal = self._to_decimal(amount)
            amount_float = float(amount_decimal)
            
            # Update using $inc to safely increment the value
            result = self.collection.update_one(
                {"payroll_id": payroll_id},
                {
                    "$inc": {
                        "accrued_employment.salary_ytd": amount_float
                    },
                    "$set": {
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating YTD earnings: {str(e)}")
            return False

    def update_ytd_tax(self, payroll_id: str, amount: Union[Decimal, float, str]) -> bool:
        """
        Update a user's year-to-date tax withheld.
        
        Args:
            payroll_id: User's payroll ID
            amount: Amount to add to YTD tax withheld
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Convert amount to Decimal and then to float for MongoDB
            amount_decimal = self._to_decimal(amount)
            amount_float = float(amount_decimal)
            
            # Update using $inc to safely increment the value
            result = self.collection.update_one(
                {"payroll_id": payroll_id},
                {
                    "$inc": {
                        "accrued_employment.tax_withheld_ytd": amount_float
                    },
                    "$set": {
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating YTD tax: {str(e)}")
            return False

    def record_leave_accrual(self, payroll_id: str, leave_type: str, hours: Union[Decimal, float, str]) -> bool:
        """
        Record leave accrual for a user.
        
        Args:
            payroll_id: User's payroll ID
            leave_type: Type of leave ('holiday', 'sick', 'carers', 'bereavement')
            hours: Hours to add to accrued leave
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Convert hours to Decimal and then to float for MongoDB
            hours_decimal = self._to_decimal(hours)
            hours_float = float(hours_decimal)
            
            # Validate leave type
            valid_types = ['holiday', 'sick', 'carers', 'bereavement']
            if leave_type not in valid_types:
                logger.error(f"Invalid leave type: {leave_type}")
                return False
            
            # Update field name
            field_name = f"leave_entitlements.{leave_type}_accrued"
            
            # Update using $inc to safely increment the value
            result = self.collection.update_one(
                {"payroll_id": payroll_id},
                {
                    "$inc": {
                        field_name: hours_float
                    },
                    "$set": {
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error recording leave accrual: {str(e)}")
            return False

    def record_leave_taken(self, payroll_id: str, leave_type: str, hours: Union[Decimal, float, str]) -> bool:
        """
        Record leave taken by a user.
        
        Args:
            payroll_id: User's payroll ID
            leave_type: Type of leave ('holiday', 'sick', 'carers', 'bereavement')
            hours: Hours to add to leave taken
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Convert hours to Decimal and then to float for MongoDB
            hours_decimal = self._to_decimal(hours)
            hours_float = float(hours_decimal)
            
            # Validate leave type
            valid_types = ['holiday', 'sick', 'carers', 'bereavement']
            if leave_type not in valid_types:
                logger.error(f"Invalid leave type: {leave_type}")
                return False
            
            # Update field name
            field_name = f"leave_entitlements.{leave_type}_taken"
            
            # Update using $inc to safely increment the value
            result = self.collection.update_one(
                {"payroll_id": payroll_id},
                {
                    "$inc": {
                        field_name: hours_float
                    },
                    "$set": {
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error recording leave taken: {str(e)}")
            return False

    def update_days_employed(self, payroll_id: str) -> bool:
        """
        Update a user's days employed count based on hired date.
        
        Args:
            payroll_id: User's payroll ID
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Get user
            user = self.find_by_payroll_id(payroll_id)
            if not user:
                return False
            
            # Get hired date
            hired_date = user.get('employment_details', {}).get('hired_date')
            if not hired_date:
                return False
            
            # Convert MongoDB date format if needed
            try:
                if isinstance(hired_date, dict) and '$date' in hired_date:
                    hired_date = self._handle_mongo_date(hired_date)
                elif isinstance(hired_date, str):
                    hired_date = datetime.fromisoformat(hired_date.rstrip('Z'))
            except ValueError as e:
                logger.error(f"Invalid date format for hired_date: {str(e)}")
                return False
            
            # Calculate days employed
            days_employed = (datetime.utcnow() - hired_date).days
            
            # Update days employed
            result = self.collection.update_one(
                {"payroll_id": payroll_id},
                {
                    "$set": {
                        "accrued_employment.days_employed": days_employed,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating days employed: {str(e)}")
            return False

    def batch_update_accruals(self, company_id: str) -> Dict[str, int]:
        """
        Batch update leave accruals for all active users in a company.
        This would typically be run on a scheduled basis.
        
        Args:
            company_id: Company ID
            
        Returns:
            Dict: Dictionary with counts of successful and failed updates
        """
        try:
            # Get all active users for the company
            users = self.find_by_company(company_id, active_only=True)
            
            success_count = 0
            failed_count = 0
            bulk_operations = []
            
            for user in users:
                try:
                    payroll_id = user.get('payroll_id')
                    
                    # Get employment details
                    employment_details = user.get('employment_details', {})
                    employment_type = employment_details.get('employment_type', 'full time')
                    hired_date = employment_details.get('hired_date')
                    
                    # Skip if no hired date
                    if not hired_date:
                        continue
                    
                    # Convert MongoDB date format if needed
                    try:
                        if isinstance(hired_date, dict) and '$date' in hired_date:
                            hired_date = self._handle_mongo_date(hired_date)
                        elif isinstance(hired_date, str):
                            hired_date = datetime.fromisoformat(hired_date.rstrip('Z'))
                    except ValueError:
                        logger.warning(f"Invalid date format for user {payroll_id}, skipping")
                        failed_count += 1
                        continue
                    
                    # Calculate FTE based on employment type
                    fte = 1.0
                    if employment_type == 'part time':
                        # Get hours per week and calculate FTE based on standard 38-hour week
                        hours_per_week = employment_details.get('hours_per_week', 38)
                        fte = min(1.0, hours_per_week / 38)
                    elif employment_type == 'casual':
                        fte = 0.0  # Casuals don't accrue leave
                    
                    # Skip if no leave accrual (casual employees)
                    if fte <= 0:
                        continue
                    
                    # Calculate service period in years
                    service_years = calculate_service_period(hired_date)
                    
                    # Calculate leave accruals and add bulk operations
                    update_operations = {}
                    for standard_type, db_field in LEAVE_TYPES.items():
                        # Calculate accrual for this period (assume bi-weekly accrual)
                        accrual = calculate_leave_accrual(
                            self._to_decimal(fte), 
                            self._to_decimal(service_years), 
                            standard_type
                        )
                        bi_weekly_accrual = accrual / 26  # 26 fortnights in a year
                        
                        # Add to update operations
                        field_name = f"leave_entitlements.{db_field}_accrued"
                        update_operations[field_name] = float(bi_weekly_accrual)
                    
                    # Update days employed
                    days_employed = (datetime.utcnow() - hired_date).days
                    update_operations["accrued_employment.days_employed"] = days_employed
                    update_operations["updated_at"] = datetime.utcnow()
                    
                    # Add bulk operation
                    bulk_operations.append(
                        UpdateOne(
                            {"payroll_id": payroll_id},
                            {"$inc": update_operations}
                        )
                    )
                    
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Error in batch accrual for user {user.get('payroll_id')}: {str(e)}")
                    failed_count += 1
            
            # Execute bulk operations
            if bulk_operations:
                try:
                    result = self.collection.bulk_write(bulk_operations, ordered=False)
                    logger.info(f"Batch updated {result.modified_count} user accruals for company {company_id}")
                except BulkWriteError as e:
                    logger.error(f"Bulk write error: {str(e)}")
                    failed_count += (len(bulk_operations) - (e.details.get('nModified', 0) or 0))
                    success_count = e.details.get('nModified', 0) or 0
            
            return {
                'success_count': success_count,
                'failed_count': failed_count,
                'total_users': len(users)
            }
        except Exception as e:
            logger.error(f"Error in batch update accruals: {str(e)}")
            return {
                'success_count': 0,
                'failed_count': 0,
                'total_users': 0,
                'error': str(e)
            }

    def generate_payslip(self, payroll_id: str, pay_date: datetime, pay_period_start: datetime, 
                        pay_period_end: datetime, pay_frequency: str = 'fortnightly') -> Dict[str, Any]:
        """
        Generate payslip data for a user.
        
        Args:
            payroll_id: User's payroll ID
            pay_date: Payment date
            pay_period_start: Pay period start date
            pay_period_end: Pay period end date
            pay_frequency: Pay frequency ('weekly', 'fortnightly', 'monthly')
            
        Returns:
            Dict: Payslip data
        """
        try:
            # Get user
            user = self.find_by_payroll_id(payroll_id)
            if not user:
                return {
                    'success': False,
                    'error': 'User not found'
                }
            
            # Get annual salary
            employment_details = user.get('employment_details', {})
            pay_rate = employment_details.get('pay_rate', {})
            annual_salary = self._to_decimal(pay_rate.get('per_annum_rate', 0))
            
            # Calculate period amounts
            period_amounts = calculate_period_amounts(annual_salary, pay_frequency)
            
            # Get YTD amounts
            ytd_amounts = get_user_ytd_amounts(user)
            
            # Get leave summary
            leave_summary = get_user_leave_summary(user)
            
            # Format dates
            pay_date_str = pay_date.strftime('%Y-%m-%d') if isinstance(pay_date, datetime) else pay_date
            period_start_str = pay_period_start.strftime('%Y-%m-%d') if isinstance(pay_period_start, datetime) else pay_period_start
            period_end_str = pay_period_end.strftime('%Y-%m-%d') if isinstance(pay_period_end, datetime) else pay_period_end
            
            # Prepare payslip data
            payslip = {
                'success': True,
                'employee': {
                    'payroll_id': user.get('payroll_id'),
                    'first_name': user.get('first_name'),
                    'last_name': user.get('last_name'),
                    'preferred_name': user.get('preferred_name'),
                    'position': user.get('role_name'),
                    'department': user.get('work_area_name')
                },
                'company': {
                    'name': user.get('company_name'),
                    'venue': user.get('venue_name')
                },
                'payment': {
                    'pay_date': pay_date_str,
                    'pay_period_start': period_start_str,
                    'pay_period_end': period_end_str,
                    'pay_frequency': pay_frequency
                },
                'earnings': {
                    'gross': float(period_amounts['gross']),
                    'tax': float(period_amounts['tax']),
                    'net': float(period_amounts['net']),
                    'super': float(period_amounts['super']),
                    'hourly_rate': float(period_amounts['hourly_rate']),
                    'hours': float(period_amounts['hours'])
                },
                'ytd': {
                    'gross': float(ytd_amounts['earnings']),
                    'tax': float(ytd_amounts['tax']),
                    'super': float(ytd_amounts['super'])
                },
                'leave': leave_summary
            }
            
            return payslip
        except Exception as e:
            logger.error(f"Error generating payslip: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def record_payment(self, payroll_id: str, payment_data: Dict[str, Any]) -> bool:
        """
        Record a payment for a user.
        
        Args:
            payroll_id: User's payroll ID
            payment_data: Payment data
            
        Returns:
            bool: True if recording successful, False otherwise
        """
        try:
            # Ensure required fields
            required_fields = ['pay_date', 'pay_period_start', 'pay_period_end', 
                              'gross', 'tax', 'net', 'super', 'reference']
            
            missing_fields = [field for field in required_fields if field not in payment_data]
            if missing_fields:
                logger.error(f"Missing required payment fields: {', '.join(missing_fields)}")
                return False
            
            # Add timestamp
            payment_data['recorded_at'] = datetime.utcnow()
            
            # Record payment
            result = self.collection.update_one(
                {"payroll_id": payroll_id},
                {
                    "$push": {
                        "payments": payment_data
                    },
                    "$set": {
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Update YTD amounts if successful
            if result.modified_count > 0:
                self.update_ytd_earnings(payroll_id, payment_data['gross'])
                self.update_ytd_tax(payroll_id, payment_data['tax'])
                logger.info(f"Recorded payment with reference {payment_data['reference']} for user {payroll_id}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error recording payment: {str(e)}")
            return False
    
    def get_payment_history(self, payroll_id: str, limit: int = 10) -> List[Dict]:
        """
        Get payment history for a user.
        
        Args:
            payroll_id: User's payroll ID
            limit: Maximum number of payments to return
            
        Returns:
            List[Dict]: List of payments
        """
        try:
            user = self.find_by_payroll_id(payroll_id)
            if not user:
                return []
            
            payments = user.get('payments', [])
            
            # Sort by pay date descending and limit
            if payments:
                payments.sort(key=lambda x: x.get('pay_date', ''), reverse=True)
            
            return payments[:limit]
        except Exception as e:
            logger.error(f"Error getting payment history: {str(e)}")
            return []
    
    def _get_db(self) -> Database:
        """
        Get MongoDB database instance with proper connection management.
        
        Returns:
            Database: MongoDB database instance
        """
        # Check for database in thread-local storage
        if hasattr(_thread_local, 'db'):
            return _thread_local.db
            
        # Check app context
        if hasattr(current_app, 'mongo'):
            _thread_local.db = current_app.mongo.db
            return _thread_local.db
            
        # Check request context
        if hasattr(g, 'db'):
            _thread_local.db = g.db
            return _thread_local.db
        
        # Create new connection with proper parameters
        uri = current_app.config.get('MONGO_URI', 'mongodb://localhost:27017')
        dbname = current_app.config.get('MONGO_DBNAME', 'MyCookBook')
        
        client = MongoClient(
            uri,
            maxPoolSize=50,
            connectTimeoutMS=5000,
            serverSelectionTimeoutMS=5000,
            waitQueueTimeoutMS=5000
        )
        
        # Store client for cleanup
        if hasattr(g, 'mongo_clients'):
            g.mongo_clients.append(client)
        else:
            g.mongo_clients = [client]
            
        _thread_local.db = client[dbname]
        return _thread_local.db


# For direct usage in other modules
def get_business_user_model(db=None) -> BusinessUserModel:
    """
    Get a business user model instance with connection pooling.
    
    Args:
        db: Optional MongoDB database instance
        
    Returns:
        BusinessUserModel: Business user model instance
    """
    # Use singleton pattern for efficiency
    if hasattr(g, 'business_user_model'):
        return g.business_user_model
    
    model = BusinessUserModel(db)
    g.business_user_model = model
    return model


# Register teardown function with Flask app context
def close_connections(exception=None):
    """
    Close any database connections created by this module.
    This function should be registered with Flask's teardown_appcontext.
    
    Usage:
        app.teardown_appcontext(close_connections)
    """
    if hasattr(g, 'mongo_clients'):
        for client in g.mongo_clients:
            client.close()
        g.mongo_clients = []
    
    # Clear thread-local storage
    if hasattr(_thread_local, 'db'):
        delattr(_thread_local, 'db')